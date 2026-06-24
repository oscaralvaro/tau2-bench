from functools import lru_cache
from pathlib import Path
from typing import Optional

from tau2.data_model.tasks import Task
from tau2.domains.ecommerce_calle.data_model import EcommerceDB
from tau2.domains.ecommerce_calle.tools import EcommerceToolKit
from tau2.domains.ecommerce_calle.user_tools import EcommerceUserToolKit
from tau2.domains.ecommerce_calle.utils import (
    ECOMMERCE_DB_PATH,
    ECOMMERCE_POLICY_PATH,
    ECOMMERCE_POLICY_RAG_PATH,
    ECOMMERCE_TASK_SET_PATH,
)
from tau2.environment.environment import Environment
from tau2.environment.rag import ChromaPolicyIndex, THINK_INSTRUCTION
from tau2.utils import load_file


@lru_cache(maxsize=8)
def _get_policy_index(chunking_strategy: str) -> ChromaPolicyIndex:
    with open(ECOMMERCE_POLICY_PATH, "r", encoding="utf-8") as fp:
        policy_text = fp.read()
    return ChromaPolicyIndex(policy_text, strategy=chunking_strategy)


def get_environment(
    db: Optional[EcommerceDB] = None,
    solo_mode: bool = False,
    chunking_strategy: str = "headers",
    retrieval_k: int = 3,
    use_think: bool = False,
) -> Environment:
    if solo_mode:
        raise ValueError("Ecommerce domain does not support solo mode")
    if db is None:
        db = EcommerceDB.load(ECOMMERCE_DB_PATH)
    policy_index = _get_policy_index(chunking_strategy)
    tools = EcommerceToolKit(db, policy_index=policy_index, retrieval_k=retrieval_k)
    user_tools = EcommerceUserToolKit(db)
    with open(ECOMMERCE_POLICY_RAG_PATH, "r", encoding="utf-8") as fp:
        policy = fp.read()
    if use_think:
        policy = policy + "\n\n" + THINK_INSTRUCTION
    return Environment(
        domain_name="ecommerce_calle",
        policy=policy,
        tools=tools,
        user_tools=user_tools,
    )


def get_tasks(task_split_name: Optional[str] = "base") -> list[Task]:
    tasks = load_file(ECOMMERCE_TASK_SET_PATH)
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
    split_file = (
        Path(ECOMMERCE_TASK_SET_PATH).parent
        / f"split_{Path(ECOMMERCE_TASK_SET_PATH).stem}.json"
    )
    return load_file(split_file)
