from typing import Optional

from tau2.data_model.tasks import Task
from tau2.domains.salud_mendoza_rag.data_model import SaludMendozaRAGDB
from tau2.domains.salud_mendoza_rag.tools import SaludRAGToolkit
from tau2.domains.salud_mendoza_rag.utils import DATA_DIR
from tau2.environment.environment import Environment
from tau2.utils import load_file


def get_environment(solo_mode: bool = False) -> Environment:
    if solo_mode:
        raise ValueError("salud_mendoza_rag does not support solo mode")

    db = SaludMendozaRAGDB.load(str(DATA_DIR / "db.json"))
    with open(DATA_DIR / "policy.md", "r", encoding="utf-8") as f:
        policy = f.read()

    return Environment(
        domain_name="salud_mendoza_rag",
        policy=policy,
        tools=SaludRAGToolkit(db),
    )


def get_tasks(task_split_name: Optional[str] = "base") -> list[Task]:
    tasks = [Task.model_validate(task) for task in load_file(DATA_DIR / "tasks.json")]
    if task_split_name is None:
        return tasks

    task_splits = get_tasks_split()
    if task_split_name not in task_splits:
        raise ValueError(
            f"Invalid task split name: {task_split_name}. Valid splits are: {list(task_splits.keys())}"
        )

    task_ids = set(task_splits[task_split_name])
    filtered_tasks = [task for task in tasks if task.id in task_ids]
    missing_task_ids = sorted(task_ids - {task.id for task in filtered_tasks})
    if missing_task_ids:
        raise ValueError(
            f"Task split '{task_split_name}' references missing tasks: {missing_task_ids}"
        )
    return filtered_tasks


def get_tasks_split() -> dict[str, list[str]]:
    split_candidates = [
        DATA_DIR / "split_tasks.json",
        DATA_DIR / "split_task.json",
    ]
    for split_path in split_candidates:
        if split_path.exists():
            return load_file(split_path)

    expected = ", ".join(path.name for path in split_candidates)
    raise FileNotFoundError(
        f"No task split file found in {DATA_DIR}. Expected one of: {expected}"
    )
