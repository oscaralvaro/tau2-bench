from typing import Optional

from tau2.data_model.tasks import Task
from tau2.domains.salud_mendoza_lista.data_model import SaludDB
from tau2.domains.salud_mendoza_lista.tools import SaludToolkit
from tau2.domains.salud_mendoza_lista.utils import DATA_DIR
from tau2.environment.environment import Environment
from tau2.utils import load_file


def get_environment(solo_mode: bool = False) -> Environment:
    """
    Punto de entrada: carga la DB y la politica, y retorna el Environment.
    """
    if solo_mode:
        raise ValueError("salud_mendoza_lista does not support solo mode")

    db = SaludDB.load(str(DATA_DIR / "db.json"))
    with open(DATA_DIR / "policy.md", "r", encoding="utf-8") as f:
        policy = f.read()

    return Environment(
        domain_name="salud_mendoza_lista",
        policy=policy,
        tools=SaludToolkit(db),
    )


def get_tasks(task_split_name: Optional[str] = "base") -> list[Task]:
    """
    Carga y retorna la lista de tasks filtradas por el split solicitado.
    """
    tasks = [Task.model_validate(task) for task in load_file(DATA_DIR / "tasks.json")]
    if task_split_name is None:
        return tasks

    splits = get_tasks_split()
    if task_split_name not in splits:
        raise ValueError(
            f"Invalid task split name: {task_split_name}. Valid splits are: {list(splits.keys())}"
        )

    task_ids = set(splits[task_split_name])
    filtered_tasks = [task for task in tasks if task.id in task_ids]
    missing_task_ids = sorted(task_ids - {task.id for task in filtered_tasks})
    if missing_task_ids:
        raise ValueError(
            f"Task split '{task_split_name}' references missing tasks: {missing_task_ids}"
        )
    return filtered_tasks


def get_tasks_split() -> dict[str, list[str]]:
    """
    Retorna el diccionario de splits de tareas.
    """
    return load_file(DATA_DIR / "split_tasks.json")
