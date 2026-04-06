from pathlib import Path
from typing import Optional
from tau2.data_model.tasks import Task
from tau2.domains.filtro_gastelo.data_model import FiltrosDB
from tau2.domains.filtro_gastelo.tools import FiltrosTools
from tau2.domains.filtro_gastelo.utils import (
    FILTRO_DB_PATH,
    FILTRO_POLICY_PATH,
    FILTRO_TASK_SET_PATH,
)
from tau2.environment.environment import Environment
from tau2.utils import load_file


def get_environment(
    db: Optional[FiltrosDB] = None,
    solo_mode: bool = False,
) -> Environment:
    if solo_mode:
        raise ValueError("El dominio filtro_gastelo no soporta modo solo")
    if db is None:
        db = FiltrosDB.load(FILTRO_DB_PATH)
    tools = FiltrosTools(db)
    with open(FILTRO_POLICY_PATH, "r") as fp:
        policy = fp.read()
    return Environment(
        domain_name="filtro_gastelo",
        policy=policy,
        tools=tools,
    )


def get_tasks(task_split_name: Optional[str] = "base") -> list[Task]:
    tasks = load_file(FILTRO_TASK_SET_PATH)
    tasks = [Task.model_validate(task) for task in tasks]
    if task_split_name is None:
        return tasks
    task_splits = get_tasks_split()
    if task_split_name not in task_splits:
        raise ValueError(
            f"Split inválido: {task_split_name}. Splits válidos: {task_splits.keys()}"
        )
    return [task for task in tasks if task.id in task_splits[task_split_name]]


def get_tasks_split() -> dict[str, list[str]]:
    split_file = (
        Path(FILTRO_TASK_SET_PATH).parent
        / f"split_{Path(FILTRO_TASK_SET_PATH).stem}.json"
    )
    return load_file(split_file)