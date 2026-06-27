# Copyright Sierra
import json
from pathlib import Path
from typing import Optional

from tau2.data_model.message import AssistantMessage, ToolMessage, UserMessage
from tau2.data_model.tasks import InitializationData, Task
from tau2.domains.estaciondeservicio_Rivera.data_model import GrifoDB
from tau2.domains.estaciondeservicio_Rivera.user_data_model import (
    RiveraUserDB,
    SMSInboxMessage,
)
from tau2.domains.estaciondeservicio_Rivera.tools import (
    EstacionDeServicioRiveraTools,
)
from tau2.domains.estaciondeservicio_Rivera.user_tools import (
    EstacionDeServicioRiveraUserTools,
)
from tau2.domains.estaciondeservicio_Rivera.utils import (
    ESTACIONDESERVICIO_RIVERA_DB_PATH,
    ESTACIONDESERVICIO_RIVERA_POLICY_PATH,
    ESTACIONDESERVICIO_RIVERA_POLICY_RAG_PATH,
    ESTACIONDESERVICIO_RIVERA_TASK_SET_PATH,
    ESTACIONDESERVICIO_RIVERA_USER_DB_PATH,
)
from tau2.environment.environment import Environment
from tau2.environment.rag import THINK_INSTRUCTION, ChromaPolicyIndex, _make_gemini_embed_fn
from tau2.utils import get_dict_hash, load_file

_NON_DETERMINISTIC_READ_TOOLS = {"retrieve_policy", "think"}

_POLICY_EMBED_CACHE: dict[str, list[float]] = {}


def _cached_policy_embed_fn(texts: list[str]) -> list[list[float]]:
    """Memoizes embeddings by exact text so identical chunks/queries always
    get the same vector within a process. Without this, the evaluator's
    replay of the agent's tool calls (which rebuilds the policy index from
    scratch) can re-embed the same text and get a slightly different vector
    from the API, occasionally flipping which near-tied chunk ranks first in
    retrieve_policy and breaking the replay consistency check."""
    missing = [text for text in texts if text not in _POLICY_EMBED_CACHE]
    if missing:
        embed_fn = _make_gemini_embed_fn()
        for text, vector in zip(missing, embed_fn(missing)):
            _POLICY_EMBED_CACHE[text] = vector
    return [_POLICY_EMBED_CACHE[text] for text in texts]


class EstacionDeServicioRiveraEnvironment(Environment):
    tools: EstacionDeServicioRiveraTools
    user_tools: EstacionDeServicioRiveraUserTools

    @staticmethod
    def _remove_sms_reason_from_hash(db_dump: dict) -> dict:
        """Keep SMS reason user-facing, but do not make DB reward depend on it."""
        for verification in db_dump.get("sms_verifications", {}).values():
            verification["reason"] = None
        for message in db_dump.get("sms_inbox", {}).values():
            message["reason"] = None
        return db_dump

    def get_db_hash(self) -> Optional[str]:
        if self.tools is None:
            return None
        db_dump = self.tools.db.model_dump()
        return get_dict_hash(self._remove_sms_reason_from_hash(db_dump))

    def get_user_db_hash(self) -> Optional[str]:
        if self.user_tools is None:
            return None
        db_dump = self.user_tools.db.model_dump()
        return get_dict_hash(self._remove_sms_reason_from_hash(db_dump))

    def sync_tools(self):
        if self.user_tools is None:
            return

        inbox = {}
        session = self.user_tools.db.session
        for verification in self.tools.db.sms_verifications.values():
            if session.customer_id is not None and verification.id_cliente != session.customer_id:
                continue
            if verification.role != session.role:
                continue
            if verification.user_id is not None and session.user_id != verification.user_id:
                continue
            if session.telefono is not None and verification.destination_phone != session.telefono:
                continue
            previous = self.user_tools.db.sms_inbox.get(verification.verification_id)
            consumed = previous.consumed if previous is not None else False
            inbox[verification.verification_id] = SMSInboxMessage(
                verification_id=verification.verification_id,
                customer_id=verification.id_cliente,
                role=verification.role,
                user_id=verification.user_id,
                phone=verification.destination_phone,
                code=verification.code,
                reason=verification.reason,
                sent_at=verification.sent_at,
                consumed=consumed,
            )
        self.user_tools.db.sms_inbox = inbox

    def set_state(
        self,
        initialization_data: Optional[InitializationData],
        initialization_actions,
        message_history: list,
    ):
        """Same as Environment.set_state, but does not enforce that replayed
        calls to non-deterministic, read-only tools (retrieve_policy, think)
        return the exact same content recorded live.

        The evaluator rebuilds this environment from scratch to replay the
        agent's tool calls (registry.get_env_constructor never receives the
        --env-args used for the live run, so the replay always uses this
        function's default chunking_strategy). retrieve_policy's output
        depends on chunking_strategy/retrieval_k, so a replay built with a
        different strategy than the live run would otherwise raise a false
        mismatch. Neither tool mutates the DB, so skipping the equality
        check here cannot affect the DB-based reward.
        """

        def get_actions_from_messages(messages: list):
            messages = list(reversed(messages))
            actions = []
            while messages:
                message = messages.pop()
                if isinstance(message, ToolMessage):
                    raise ValueError(
                        "Tool message not expected. Tool messages should always follow a tool call."
                    )
                if (
                    isinstance(message, (AssistantMessage, UserMessage))
                    and message.is_tool_call()
                ):
                    for tc in message.tool_calls:
                        if len(messages) == 0:
                            raise ValueError("Tool message expected. Got None.")
                        tm = messages.pop()
                        if not isinstance(tm, ToolMessage):
                            raise ValueError(f"Tool message expected. Got {type(tm)}")
                        if tc.id != tm.id:
                            raise ValueError(
                                f"Tool call id mismatch. Got {tc.id} and {tm.id}"
                            )
                        actions.append((tc, tm))
            return actions

        if self.solo_mode:
            assert all(
                not isinstance(message, UserMessage) for message in message_history
            ), "User messages are not allowed in solo mode"

        if initialization_data is not None:
            if initialization_data.agent_data is not None:
                self.tools.update_db(initialization_data.agent_data)
            if initialization_data.user_data is not None:
                self.user_tools.update_db(initialization_data.user_data)

        if initialization_actions is not None:
            for action in initialization_actions:
                self.run_env_function_call(action)

        for tool_call, expected_response in get_actions_from_messages(message_history):
            if tool_call.name in _NON_DETERMINISTIC_READ_TOOLS:
                continue
            response = self.get_response(tool_call)
            try:
                content = json.loads(response.content)
            except Exception:
                content = response.content
            try:
                expected_content = json.loads(expected_response.content)
            except Exception:
                expected_content = expected_response.content
            if content != expected_content:
                raise ValueError(
                    f"Tool call:\n{tool_call}\n\nReturned:\n{response}\n\nExpected:\n{expected_response}"
                )
        self.sync_tools()


def get_environment(
    db: Optional[GrifoDB] = None,
    user_db: Optional[RiveraUserDB] = None,
    solo_mode: bool = False,
    chunking_strategy: str = "headers",
    retrieval_k: int = 3,
    use_think: bool = False,
    use_rag: bool = True,
) -> Environment:
    if solo_mode:
        raise ValueError("estaciondeservicio_Rivera domain does not support solo mode")
    if db is None:
        db = GrifoDB.load(ESTACIONDESERVICIO_RIVERA_DB_PATH)
    if user_db is None:
        if ESTACIONDESERVICIO_RIVERA_USER_DB_PATH.exists():
            user_db = RiveraUserDB.load(ESTACIONDESERVICIO_RIVERA_USER_DB_PATH)
        else:
            user_db = RiveraUserDB()

    if use_rag:
        with open(ESTACIONDESERVICIO_RIVERA_POLICY_PATH, "r", encoding="utf-8") as fp:
            policy_text = fp.read()
        policy_index = ChromaPolicyIndex(
            policy_text, strategy=chunking_strategy, _embed_fn=_cached_policy_embed_fn
        )
        tools = EstacionDeServicioRiveraTools(
            db, policy_index=policy_index, retrieval_k=retrieval_k
        )
        with open(ESTACIONDESERVICIO_RIVERA_POLICY_RAG_PATH, "r", encoding="utf-8") as fp:
            policy = fp.read()
        if use_think:
            policy = policy + THINK_INSTRUCTION
    else:
        tools = EstacionDeServicioRiveraTools(db)
        with open(ESTACIONDESERVICIO_RIVERA_POLICY_PATH, "r", encoding="utf-8") as fp:
            policy = fp.read()

    user_tools = EstacionDeServicioRiveraUserTools(user_db)
    return EstacionDeServicioRiveraEnvironment(
        domain_name="estaciondeservicio_Rivera",
        policy=policy,
        tools=tools,
        user_tools=user_tools,
    )


def get_tasks(task_split_name: Optional[str] = "base") -> list[Task]:
    tasks = load_file(ESTACIONDESERVICIO_RIVERA_TASK_SET_PATH)
    tasks = [Task.model_validate(task) for task in tasks]
    if task_split_name is None:
        return tasks
    task_splits = get_tasks_split()
    if task_split_name not in task_splits:
        raise ValueError(
            f"Invalid task split name: {task_split_name}. Valid splits are: {task_splits.keys()}"
        )
    tasks = [task for task in tasks if task.id in task_splits[task_split_name]]
    return tasks


def get_tasks_split() -> dict[str, list[str]]:
    split_file = (
        Path(ESTACIONDESERVICIO_RIVERA_TASK_SET_PATH).parent
        / f"split_{Path(ESTACIONDESERVICIO_RIVERA_TASK_SET_PATH).stem}.json"
    )
    return load_file(split_file)
