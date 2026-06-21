from functools import lru_cache
from typing import Optional

from tau2.data_model.tasks import Task
from tau2.domains.hotel_calle.data_model import HotelCalleDB
from tau2.domains.hotel_calle.tools import HotelCalleTools
from tau2.domains.hotel_calle.user_data_model import HotelCalleUserDB, SmsMessage
from tau2.domains.hotel_calle.user_tools import HotelCalleUserTools
from tau2.domains.hotel_calle.utils import (
    HOTEL_CALLE_DB_PATH,
    HOTEL_CALLE_POLICY_PATH,
    HOTEL_CALLE_POLICY_RAG_PATH,
    HOTEL_CALLE_TASK_SPLIT_PATH,
    HOTEL_CALLE_TASK_SET_PATH,
)
from tau2.environment.environment import Environment
from tau2.environment.rag import THINK_INSTRUCTION, ChromaPolicyIndex
from tau2.utils import load_file


class HotelCalleEnvironment(Environment):
    tools: HotelCalleTools
    user_tools: HotelCalleUserTools

    def sync_tools(self):
        if self.user_tools is None or self.tools is None:
            return
        seen = {
            (message.reservation_id, message.role, message.code)
            for message in self.user_tools.db.sms_messages
        }
        for verification in self.tools.db.verification_codes.values():
            key = (
                verification.reservation_id,
                verification.role,
                verification.code,
            )
            if key in seen:
                continue
            self.user_tools.db.sms_messages.append(
                SmsMessage(
                    reservation_id=verification.reservation_id,
                    phone=verification.phone,
                    role=verification.role,
                    code=verification.code,
                )
            )


@lru_cache(maxsize=4)
def _get_policy_index(chunking_strategy: str) -> ChromaPolicyIndex:
    with open(HOTEL_CALLE_POLICY_PATH, "r", encoding="utf-8") as fp:
        policy_text = fp.read()
    return ChromaPolicyIndex(
        policy_text,
        strategy=chunking_strategy,
    )


def get_environment(
    db: Optional[HotelCalleDB] = None,
    solo_mode: bool = False,
    chunking_strategy: str = "headers",
    retrieval_k: int = 3,
    use_think: bool = False,
    use_rag: bool = True,
) -> Environment:
    if solo_mode:
        raise ValueError("Hotel Calle domain does not support solo mode")
    if db is None:
        db = HotelCalleDB.load(HOTEL_CALLE_DB_PATH)

    if use_rag:
        policy_index = _get_policy_index(chunking_strategy)
        tools = HotelCalleTools(
            db,
            policy_index=policy_index,
            retrieval_k=retrieval_k,
        )
        with open(HOTEL_CALLE_POLICY_RAG_PATH, "r", encoding="utf-8") as fp:
            policy = fp.read()
        if use_think:
            policy = policy + THINK_INSTRUCTION
    else:
        tools = HotelCalleTools(db)
        with open(HOTEL_CALLE_POLICY_PATH, "r", encoding="utf-8") as fp:
            policy = fp.read()

    user_tools = HotelCalleUserTools(HotelCalleUserDB())
    return HotelCalleEnvironment(
        domain_name="hotel_calle",
        policy=policy,
        tools=tools,
        user_tools=user_tools,
    )


def get_tasks(task_split_name: Optional[str] = "base") -> list[Task]:
    tasks = load_file(HOTEL_CALLE_TASK_SET_PATH)
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
    return load_file(HOTEL_CALLE_TASK_SPLIT_PATH)
