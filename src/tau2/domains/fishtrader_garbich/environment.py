from pathlib import Path
from typing import Optional

from tau2.data_model.tasks import Task
from tau2.domains.fishtrader_garbich.data_model import FishTraderDB
from tau2.domains.fishtrader_garbich.tools import FishTraderTools
from tau2.domains.fishtrader_garbich.utils import (
    FISHTRADER_GARBICH_DB_PATH,
    FISHTRADER_GARBICH_POLICY_PATH,
    FISHTRADER_GARBICH_TASK_SET_PATH,
)
from tau2.environment.environment import Environment
from tau2.utils import load_file


def get_environment(
    db: Optional[FishTraderDB] = None,
    solo_mode: bool = False,
) -> Environment:
    """
    Load the fish trader environment, including database, policy, and tools.
    """
    if solo_mode:
        raise ValueError("Fish trader domain does not support solo mode")
    if db is None:
        db = FishTraderDB.load(FISHTRADER_GARBICH_DB_PATH)
    tools = FishTraderTools(db)
    with open(FISHTRADER_GARBICH_POLICY_PATH, "r") as fp:
        policy = fp.read()
    return Environment(
        domain_name="fishtrader_garbich",
        policy=policy,
        tools=tools,
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
