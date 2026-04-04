from typing import Optional

from tau2.data_model.tasks import Task
from tau2.domains.hotel_calle.data_model import HotelCalleDB
from tau2.domains.hotel_calle.tools import HotelCalleTools
from tau2.domains.hotel_calle.utils import (
    HOTEL_CALLE_DB_PATH,
    HOTEL_CALLE_POLICY_PATH,
    HOTEL_CALLE_TASK_SPLIT_PATH,
    HOTEL_CALLE_TASK_SET_PATH,
)
from tau2.environment.environment import Environment
from tau2.utils import load_file


def get_environment(
    db: Optional[HotelCalleDB] = None,
    solo_mode: bool = False,
) -> Environment:
    if solo_mode:
        raise ValueError("Hotel Calle domain does not support solo mode")
    if db is None:
        db = HotelCalleDB.load(HOTEL_CALLE_DB_PATH)
    tools = HotelCalleTools(db)
    with open(HOTEL_CALLE_POLICY_PATH, "r", encoding="utf-8") as fp:
        policy = fp.read()
    return Environment(
        domain_name="hotel_calle",
        policy=policy,
        tools=tools,
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
