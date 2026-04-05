from pathlib import Path
from typing import Optional

from tau2.data_model.tasks import Task
from tau2.domains.sanita_irigoin.data_model import ArrozDB
from tau2.domains.sanita_irigoin.tools import ArrozToolKit
from tau2.domains.sanita_irigoin.utils import (
    DB_PATH,
    POLICY_PATH,
    TASKS_PATH,
    SPLIT_TASKS_PATH,
)
from tau2.environment.environment import Environment
from tau2.utils import load_file


def get_environment(
    db: Optional[ArrozDB] = None,
    solo_mode: bool = False,
) -> Environment:
    if solo_mode:
        raise ValueError("sanita_irigoin domain does not support solo mode")
    if db is None:
        db = ArrozDB.load(DB_PATH)
    tools = ArrozToolKit(db)
    with open(POLICY_PATH, "r", encoding="utf-8") as fp:
        policy = fp.read()
    return Environment(
        domain_name="sanita_irigoin",
        policy=policy,
        tools=tools,
    )


def get_tasks(task_split_name: Optional[str] = "base") -> list[Task]:
    tasks = load_file(TASKS_PATH)
    tasks = [Task.model_validate(task) for task in tasks]
    if task_split_name is None:
        return tasks
    task_splits = get_tasks_split()
    if task_split_name not in task_splits:
        raise ValueError(
            f"Invalid task split name: {task_split_name}. "
            f"Valid splits are: {task_splits.keys()}"
        )
    return [task for task in tasks if task.id in task_splits[task_split_name]]


def get_tasks_split() -> dict[str, list[str]]:
    split_file = (
        Path(TASKS_PATH).parent
        / f"split_{Path(TASKS_PATH).stem}.json"
    )
    return load_file(split_file)