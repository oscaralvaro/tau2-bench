from pathlib import Path
from typing import Optional

from tau2.data_model.tasks import Task
from tau2.domains.healthcare_macalupu.auth_data_model import AuthCodeService
from tau2.domains.healthcare_macalupu.data_model import HealthcareDB
from tau2.domains.healthcare_macalupu.tools import HealthcareTools
from tau2.domains.healthcare_macalupu.user_data_model import HealthcareUserDB
from tau2.domains.healthcare_macalupu.user_tools import HealthcareUserTools
from tau2.domains.healthcare_macalupu.utils import (
    HEALTHCARE_DB_PATH,
    HEALTHCARE_POLICY_PATH,
    HEALTHCARE_POLICY_RAG_PATH,
    HEALTHCARE_TASK_SET_PATH,
)
from tau2.environment.environment import Environment
from tau2.environment.rag import THINK_INSTRUCTION, ChromaPolicyIndex, ChunkingStrategy
from tau2.utils import load_file


# ---------------------------------------------------------------------------
# Environment factory
# ---------------------------------------------------------------------------
def get_environment(
    db: Optional[HealthcareDB] = None,
    user_db: Optional[HealthcareUserDB] = None,
    solo_mode: bool = False,
    chunking_strategy: ChunkingStrategy = "headers",
    retrieval_k: int = 3,
    use_think: bool = False,
) -> Environment:

    if solo_mode:
        raise ValueError("healthcare_macalupu domain does not support solo mode")

    if db is None:
        db = HealthcareDB.load(HEALTHCARE_DB_PATH)  # pyright: ignore[reportAssignmentType, reportArgumentType]
    if user_db is None:
        user_db = HealthcareUserDB()

    auth_service = AuthCodeService()
    auth_service.add_observer(user_db)

    with open(HEALTHCARE_POLICY_PATH, "r", encoding="utf-8") as fp:
        policy_text = fp.read()
    policy_index = ChromaPolicyIndex(policy_text, strategy=chunking_strategy)

    tools = HealthcareTools(
        db=db,  # pyright: ignore[reportArgumentType]
        auth_service=auth_service,
        policy_index=policy_index,
        retrieval_k=retrieval_k,
    )
    user_tools = HealthcareUserTools(user_db)

    with open(HEALTHCARE_POLICY_RAG_PATH, "r", encoding="utf-8") as fp:
        policy = fp.read()
    if use_think:
        policy = policy + f"\n\n{THINK_INSTRUCTION}"

    return Environment(
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
