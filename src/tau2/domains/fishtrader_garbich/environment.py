from pathlib import Path
from typing import Optional

from tau2.data_model.message import (
    AssistantMessage,
    Message,
    ToolMessage,
    UserMessage,
)
from tau2.data_model.tasks import EnvFunctionCall, InitializationData, Task
from tau2.domains.fishtrader_garbich.data_model import FishTraderDB
from tau2.domains.fishtrader_garbich.tools import FishTraderTools
from tau2.domains.fishtrader_garbich.user_data_model import FishTraderUserDB
from tau2.domains.fishtrader_garbich.user_tools import FishTraderUserTools
from tau2.domains.fishtrader_garbich.utils import (
    FISHTRADER_GARBICH_DB_PATH,
    FISHTRADER_GARBICH_POLICY_PATH,
    FISHTRADER_GARBICH_POLICY_RAG_PATH,
    FISHTRADER_GARBICH_TASK_SET_PATH,
)
from tau2.environment.environment import Environment
from tau2.environment.rag import THINK_INSTRUCTION, ChromaPolicyIndex
from tau2.utils import load_file


class FishTraderEnvironment(Environment):
    tools: FishTraderTools
    user_tools: FishTraderUserTools

    def __init__(
        self,
        domain_name: str,
        policy: str,
        tools: FishTraderTools,
        user_tools: FishTraderUserTools,
    ):
        super().__init__(domain_name, policy, tools, user_tools)

    def sync_tools(self):
        """
        Bridge the agent-generated verification code to the user's SMS inbox.
        Called automatically after every tool invocation.
        """
        pending = self.tools._pending_verification
        if pending is not None:
            self.user_tools.db.surroundings.received_sms_code = pending["code"]
        else:
            # Clear the inbox once the code has been consumed (verified or failed)
            if self.tools._verified is not None or self.tools._pending_verification is None:
                self.user_tools.db.surroundings.received_sms_code = None

    # Read-only tools whose output depends on CLI-controlled settings and that never
    # mutate the environment. ``retrieve_policy`` returns different text depending on
    # the chunking strategy passed via --env-args, but the evaluator rebuilds the
    # environment with default env-args and replays every tool call demanding a byte
    # identical match (see Environment.set_state). That breaks any run using a
    # non-default chunking strategy (e.g. fixed_200), discarding all simulations.
    # Since these tools do not change state, dropping them from the replay leaves the
    # reconstructed state—and therefore the reward—untouched, while making evaluation
    # agnostic to the chunking strategy.
    _REPLAY_SKIP_TOOLS = {"retrieve_policy"}

    @classmethod
    def _strip_readonly_tool_calls(
        cls, message_history: list[Message]
    ) -> list[Message]:
        if not message_history:
            return message_history
        skip_ids: set[str] = set()
        filtered: list[Message] = []
        for message in message_history:
            if isinstance(message, ToolMessage):
                if message.id in skip_ids:
                    skip_ids.discard(message.id)
                    continue
                filtered.append(message)
                continue
            if (
                isinstance(message, (AssistantMessage, UserMessage))
                and message.is_tool_call()
                and all(tc.name in cls._REPLAY_SKIP_TOOLS for tc in message.tool_calls)
            ):
                skip_ids.update(tc.id for tc in message.tool_calls)
                continue
            filtered.append(message)
        return filtered

    def set_state(
        self,
        initialization_data: Optional[InitializationData],
        initialization_actions: Optional[list[EnvFunctionCall]],
        message_history: list[Message],
    ):
        return super().set_state(
            initialization_data=initialization_data,
            initialization_actions=initialization_actions,
            message_history=self._strip_readonly_tool_calls(message_history),
        )


def get_environment(
    db: Optional[FishTraderDB] = None,
    user_db: Optional[FishTraderUserDB] = None,
    solo_mode: bool = False,
    chunking_strategy: str = "headers",
    retrieval_k: int = 3,
    use_think: bool = False,
    use_rag: bool = True,
) -> FishTraderEnvironment:
    """
    Load the fish trader environment, including database, policy, and tools.

    When ``use_rag`` is True the agent receives the reduced ``policy_rag.md``
    system prompt and retrieves policy sections on demand via ``retrieve_policy``;
    the full ``policy.md`` is indexed in ChromaDB using ``chunking_strategy``.
    When ``use_rag`` is False the legacy E3 behaviour is used: the full
    ``policy.md`` is loaded as the system prompt and no index is built.
    """
    if solo_mode:
        raise ValueError("Fish trader domain does not support solo mode")
    if db is None:
        db = FishTraderDB.load(FISHTRADER_GARBICH_DB_PATH)
    if user_db is None:
        user_db = FishTraderUserDB()
    user_tools = FishTraderUserTools(user_db)

    if use_rag:
        with open(FISHTRADER_GARBICH_POLICY_PATH, "r", encoding="utf-8") as fp:
            policy_text = fp.read()
        policy_index = ChromaPolicyIndex(policy_text, strategy=chunking_strategy)
        tools = FishTraderTools(db, policy_index=policy_index, retrieval_k=retrieval_k)
        with open(FISHTRADER_GARBICH_POLICY_RAG_PATH, "r", encoding="utf-8") as fp:
            policy = fp.read()
        if use_think:
            policy = policy + THINK_INSTRUCTION
    else:
        tools = FishTraderTools(db)
        with open(FISHTRADER_GARBICH_POLICY_PATH, "r", encoding="utf-8") as fp:
            policy = fp.read()

    return FishTraderEnvironment(
        domain_name="fishtrader_garbich",
        policy=policy,
        tools=tools,
        user_tools=user_tools,
    )


def get_tasks(task_split_name: Optional[str] = "base") -> list[Task]:
    """
    Load and optionally filter the tasks for the fish trader domain.
    """
    tasks = load_file(FISHTRADER_GARBICH_TASK_SET_PATH)
    tasks = [Task.model_validate(task) for task in tasks]
    if task_split_name is None:
        return tasks
    task_splits = get_tasks_split()
    if task_split_name not in task_splits:
        raise ValueError(
            f"Invalid task split name: {task_split_name}. Valid splits are: {task_splits.keys()}"
        )
    return [task for task in tasks if task.id in task_splits[task_split_name]]


def get_tasks_split() -> dict[str, list[str]]:
    """
    Load the task split mapping for the fish trader domain.
    """
    split_file = (
        Path(FISHTRADER_GARBICH_TASK_SET_PATH).parent
        / f"split_{Path(FISHTRADER_GARBICH_TASK_SET_PATH).stem}.json"
    )
    return load_file(split_file)
