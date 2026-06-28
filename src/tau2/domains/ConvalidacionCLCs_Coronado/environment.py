"""Environment configuration for the CLC validation system."""

from typing import Optional

from tau2.data_model.tasks import Task
from tau2.domains.ConvalidacionCLCs_Coronado.data_model import (
    ConvalidacionCLCDB,
    get_db,
)
from tau2.domains.ConvalidacionCLCs_Coronado.tools import ConvalidacionCLCTools
from tau2.domains.ConvalidacionCLCs_Coronado.user_tools import ConvalidacionCLCUserTools
from tau2.domains.ConvalidacionCLCs_Coronado.utils import (
    CONVALIDACION_DOMAIN_NAME,
    CONVALIDACION_POLICY_PATH,
    CONVALIDACION_SPLIT_TASKS_PATH,
    CONVALIDACION_TASK_SET_PATH,
)
from tau2.environment.environment import Environment
from tau2.environment.rag import THINK_INSTRUCTION, ChromaPolicyIndex
from tau2.utils import load_file


def get_environment(
    db: Optional[ConvalidacionCLCDB] = None,
    solo_mode: bool = False,
    chunking_strategy: str = "headers",
    retrieval_k: int = 3,
    use_think: bool = False,
    use_rag: bool = True,
) -> Environment:
    """Return the environment for the CLC validation domain.

    RAG (E4): cuando use_rag=True, la política se indexa en ChromaDB con la
    estrategia de chunking indicada y el agente la consulta vía retrieve_policy;
    el system prompt es la versión reducida policy_rag.md. Con use_rag=False se
    usa la política completa en el prompt (baseline sin RAG). Estos parámetros los
    pasa el framework desde --env-args, sin tocar código entre condiciones.
    """
    if solo_mode:
        raise ValueError("ConvalidacionCLCs_Coronado does not support solo mode")

    if db is None:
        db = get_db()

    policy_rag_path = CONVALIDACION_POLICY_PATH.parent / "policy_rag.md"

    if use_rag:
        with open(CONVALIDACION_POLICY_PATH, "r", encoding="utf-8") as fp:
            policy_text = fp.read()
        policy_index = ChromaPolicyIndex(policy_text, strategy=chunking_strategy)
        tools = ConvalidacionCLCTools(
            db, policy_index=policy_index, retrieval_k=retrieval_k
        )
        with open(policy_rag_path, "r", encoding="utf-8") as fp:
            policy = fp.read()
        if use_think:
            policy = policy + THINK_INSTRUCTION
    else:
        tools = ConvalidacionCLCTools(db)
        with open(CONVALIDACION_POLICY_PATH, "r", encoding="utf-8") as fp:
            policy = fp.read()

    user_tools = ConvalidacionCLCUserTools(tools._sms_codes)

    return Environment(
        domain_name=CONVALIDACION_DOMAIN_NAME,
        policy=policy,
        tools=tools,
        user_tools=user_tools,
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
