from pathlib import Path
from typing import Optional
from webbrowser import get

from tau2.data_model.tasks import Task
from tau2.domains.healthcare_macalupu.data_model import InterconsultaDB, get_db
from tau2.domains.healthcare_macalupu.tools import InterconsultaTools
from tau2.domains.healthcare_macalupu.utils import (
    HEALTHCARE_POLICY_PATH,
    HEALTHCARE_POLICY_SOLO_PATH,
    HEALTHCARE_TASK_SET_PATH,
)
from tau2.environment.environment import Environment
from tau2.utils import load_file

# ---------------------------------------------------------------------------
# Environment factory
# ---------------------------------------------------------------------------


def get_environment(
    db: Optional[InterconsultaDB] = None, solo_mode: bool = False
) -> Environment:
    """
    Build and return the Interconsulta domain Environment.

    Args:
        db: Optional pre-loaded database. If None, the default db.json is used.
        solo_mode: If True, loads the solo-mode policy variant and sets the
                   environment to solo mode (agent acts without a user simulator).

    Returns:
        A fully configured Environment instance for the interconsulta domain.
    """
    if db is None:
        db = get_db()

    tools = InterconsultaTools(db)

    policy_path = HEALTHCARE_POLICY_SOLO_PATH if solo_mode else HEALTHCARE_POLICY_PATH
    with open(policy_path, "r", encoding="utf-8") as fp:
        policy = fp.read()

    env = Environment(
        domain_name="interconsulta",
        policy=policy,
        tools=tools,
    )

    if solo_mode:
        env.set_solo_mode(True)

    return env


# ---------------------------------------------------------------------------
# Task loaders
# ---------------------------------------------------------------------------


def get_tasks(task_split_name: Optional[str] = None) -> list[Task]:
    """
    Load evaluation tasks for the interconsulta domain.

    Args:
        task_split_name: Optional name of a task split defined in
                         split_tasks.json (e.g. 'medico', 'paciente',
                         'adversarial', 'happy_path').
                         If None, all tasks are returned.

    Returns:
        A list of Task objects.

    Raises:
        ValueError: If the requested split name does not exist.
    """
    tasks = load_file(HEALTHCARE_TASK_SET_PATH)
    tasks = [Task.model_validate(task) for task in tasks]

    if task_split_name is None:
        return tasks

    task_splits = get_tasks_split()
    if task_split_name not in task_splits:
        raise ValueError(
            f"Split '{task_split_name}' no encontrado. "
            f"Splits disponibles: {list(task_splits.keys())}"
        )

    split_ids = set(task_splits[task_split_name])
    return [task for task in tasks if task.id in split_ids]


def get_tasks_split() -> dict[str, list[str]]:
    """
    Load the task split definitions from split_tasks.json.

    Returns:
        A dict mapping split names to lists of task IDs.
    """
    split_file = (
        Path(HEALTHCARE_TASK_SET_PATH).parent
        / f"split_{Path(HEALTHCARE_TASK_SET_PATH).stem}.json"
    )
    return load_file(split_file)
