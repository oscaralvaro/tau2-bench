from pathlib import Path
from typing import Optional
from webbrowser import get

from tau2.data_model.tasks import Task
from tau2.domains.healthcare_macalupu.auth_data_model import AuthCodeService
from tau2.domains.healthcare_macalupu.data_model import HealthcareDB
from tau2.domains.healthcare_macalupu.tools import HealthcareTools
from tau2.domains.healthcare_macalupu.user_data_model import HealthcareUserDB
from tau2.domains.healthcare_macalupu.user_tools import HealthcareUserTools
from tau2.domains.healthcare_macalupu.utils import (
    HEALTHCARE_DB_PATH,
    HEALTHCARE_POLICY_PATH,
    HEALTHCARE_TASK_SET_PATH,
)
from tau2.environment.environment import Environment
from tau2.utils import load_file


class HealthcareEnvironment(Environment):
    tools: HealthcareTools
    user_tools: HealthcareUserTools

    def __init__(
        self,
        domain_name: str,
        policy: str,
        tools: HealthcareTools,
        user_tools: HealthcareUserTools,
    ):
        super().__init__(domain_name, policy, tools, user_tools)


# ---------------------------------------------------------------------------
# Environment factory
# ---------------------------------------------------------------------------
def get_environment(
    db: Optional[HealthcareDB] = None,
    user_db: Optional[HealthcareUserDB] = None,
    solo_mode: bool = False,
) -> Environment:

    if solo_mode:
        raise ValueError("healthcare_macalupu domain does not support solo mode")

    auth_service = AuthCodeService()

    if db is None:
        db = HealthcareDB.load(HEALTHCARE_DB_PATH)  # pyright: ignore[reportAssignmentType, reportArgumentType]
    if user_db is None:
        user_db = HealthcareUserDB(auth_service._codes)

    tools = HealthcareTools(db, auth_service)  # pyright: ignore[reportArgumentType]
    user_tools = HealthcareUserTools(user_db)

    with open(HEALTHCARE_POLICY_PATH, "r", encoding="utf-8") as fp:
        policy = fp.read()

    return HealthcareEnvironment(
        domain_name="healthcare_macalupu",
        policy=policy,
        tools=tools,
        user_tools=user_tools,
    )


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
