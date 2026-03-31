"""Environment configuration for the CLC validation system."""

from typing import Optional

from tau2.data_model.tasks import Task
from tau2.domains.ConvalidacionCLCs_Coronado.data_model import (
    ConvalidacionCLCDB,
    get_db,
)
from tau2.domains.ConvalidacionCLCs_Coronado.tools import ConvalidacionCLCTools
from tau2.domains.ConvalidacionCLCs_Coronado.utils import (
    CONVALIDACION_DOMAIN_NAME,
    CONVALIDACION_POLICY_PATH,
    CONVALIDACION_SPLIT_TASKS_PATH,
    CONVALIDACION_TASK_SET_PATH,
)
from tau2.environment.environment import Environment
from tau2.utils import load_file


def get_environment(
    db: Optional[ConvalidacionCLCDB] = None,
    solo_mode: bool = False,
) -> Environment:
    """Return the environment for the CLC validation domain."""
    if solo_mode:
        raise ValueError("ConvalidacionCLCs_Coronado does not support solo mode")

    if db is None:
        db = get_db()

    tools = ConvalidacionCLCTools(db)
    with open(CONVALIDACION_POLICY_PATH, "r", encoding="utf-8") as fp:
        policy = fp.read()

    return Environment(
        domain_name=CONVALIDACION_DOMAIN_NAME,
        policy=policy,
        tools=tools,
    )


def get_tasks(task_split_name: Optional[str] = "base") -> list[Task]:
    """Return the tasks for the domain, optionally filtered by split."""
    tasks_data = load_file(CONVALIDACION_TASK_SET_PATH)
    tasks = [Task.model_validate(task) for task in tasks_data]

    if task_split_name is None:
        return tasks

    task_splits = get_tasks_split()
    if task_split_name not in task_splits:
        raise ValueError(
            f"Invalid task split name: {task_split_name}. "
            f"Valid splits are: {list(task_splits.keys())}"
        )

    allowed_ids = set(task_splits[task_split_name])
    return [task for task in tasks if task.id in allowed_ids]


def get_tasks_split() -> dict[str, list[str]]:
    """Return the configured task splits for the domain."""
    return load_file(CONVALIDACION_SPLIT_TASKS_PATH)
