from pathlib import Path
from typing import Optional

from tau2.data_model.tasks import Task
from tau2.domains.ecommerce_zulemalopez.data_model import EcommerceDB
from tau2.domains.ecommerce_zulemalopez.tools import EcommerceTools
from tau2.domains.ecommerce_zulemalopez.utils import (
    ECOMMERCE_DB_PATH,
    ECOMMERCE_POLICY_PATH,
    ECOMMERCE_TASK_SET_PATH,
)
from tau2.environment.environment import Environment
from tau2.utils import load_file


def get_environment(
    db: Optional[EcommerceDB] = None,
    solo_mode: bool = False,
) -> Environment:
    if solo_mode:
        raise ValueError("ecommerce_zulemalopez does not support solo mode")
    if db is None:
        db = EcommerceDB.load(ECOMMERCE_DB_PATH)
    tools = EcommerceTools(db)
    with open(ECOMMERCE_POLICY_PATH, "r", encoding="utf-8") as fp:
        policy = fp.read()
    return Environment(
        domain_name="ecommerce_zulemalopez",
        policy=policy,
        tools=tools,
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
