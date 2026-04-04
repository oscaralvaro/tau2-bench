# Copyright Sierra
from pathlib import Path
from typing import Optional

from tau2.data_model.tasks import Task
from tau2.domains.estaciondeservicio_Rivera.data_model import GrifoDB
from tau2.domains.estaciondeservicio_Rivera.tools import (
    EstacionDeServicioRiveraTools,
)
from tau2.domains.estaciondeservicio_Rivera.utils import (
    ESTACIONDESERVICIO_RIVERA_DB_PATH,
    ESTACIONDESERVICIO_RIVERA_POLICY_PATH,
    ESTACIONDESERVICIO_RIVERA_TASK_SET_PATH,
)
from tau2.environment.environment import Environment
from tau2.utils import load_file


def get_environment(
    db: Optional[GrifoDB] = None,
    solo_mode: bool = False,
) -> Environment:
    if solo_mode:
        raise ValueError("estaciondeservicio_Rivera domain does not support solo mode")
    if db is None:
        db = GrifoDB.load(ESTACIONDESERVICIO_RIVERA_DB_PATH)
    tools = EstacionDeServicioRiveraTools(db)
    with open(ESTACIONDESERVICIO_RIVERA_POLICY_PATH, "r") as fp:
        policy = fp.read()
    return Environment(
        domain_name="estaciondeservicio_Rivera",
        policy=policy,
        tools=tools,
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
