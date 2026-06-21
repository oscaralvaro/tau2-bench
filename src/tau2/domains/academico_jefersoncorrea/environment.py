from pathlib import Path
from typing import Optional

from tau2.data_model.tasks import Task
from tau2.domains.academico_jefersoncorrea.data_model import AcademicDB
from tau2.domains.academico_jefersoncorrea.tools import AcademicTools
from tau2.domains.academico_jefersoncorrea.user_tools import AcademicUserTools
from tau2.domains.academico_jefersoncorrea.utils import (
    ACADEMICO_DB_PATH,
    ACADEMICO_POLICY_PATH,
    ACADEMICO_POLICY_RAG_PATH,
    ACADEMICO_TASK_SET_PATH,
)
from tau2.environment.environment import Environment
from tau2.environment.rag import THINK_INSTRUCTION, ChromaPolicyIndex
from tau2.utils import load_file


def get_environment(
    db: Optional[AcademicDB] = None,
    solo_mode: bool = False,
    chunking_strategy: str = "headers",
    retrieval_k: int = 3,
    use_think: bool = False,
    use_rag: bool = True,
) -> Environment:
    """
    Inicializa y devuelve el entorno de evaluacion para el dominio academico.
    Cuando use_rag=True, indexa policy.md y usa policy_rag.md como prompt reducido.
    """
    if solo_mode:
        raise ValueError("El dominio academico no soporta el modo solitario (solo mode)")

    if db is None:
        db = AcademicDB.load(ACADEMICO_DB_PATH)

    if use_rag:
        with open(ACADEMICO_POLICY_PATH, "r", encoding="utf-8") as fp:
            policy_text = fp.read()
        policy_index = ChromaPolicyIndex(policy_text, strategy=chunking_strategy)
        tools = AcademicTools(db, policy_index=policy_index, retrieval_k=retrieval_k)
        with open(ACADEMICO_POLICY_RAG_PATH, "r", encoding="utf-8") as fp:
            policy = fp.read()
        if use_think:
            policy = policy + THINK_INSTRUCTION
    else:
        tools = AcademicTools(db)
        with open(ACADEMICO_POLICY_PATH, "r", encoding="utf-8") as fp:
            policy = fp.read()

    user_tools = AcademicUserTools(db)

    return Environment(
        domain_name="academico_jefersoncorrea",
        policy=policy,
        tools=tools,
        user_tools=user_tools,
    )


def get_tasks(task_split_name: Optional[str] = "base") -> list[Task]:
    """
    Carga los escenarios de prueba (tasks) desde el archivo JSON.
    """
    tasks = load_file(ACADEMICO_TASK_SET_PATH)
    tasks = [Task.model_validate(task) for task in tasks]

    if task_split_name is None:
        return tasks

    task_splits = get_tasks_split()
    if task_split_name not in task_splits:
        raise ValueError(
            f"Nombre de split invalido: {task_split_name}. Los validos son: {list(task_splits.keys())}"
        )

    return [task for task in tasks if task.id in task_splits[task_split_name]]


def get_tasks_split() -> dict[str, list[str]]:
    """
    Carga las divisiones (splits) de las tareas, usualmente para separar entre datos de prueba y validacion.
    """
    split_file = (
        Path(ACADEMICO_TASK_SET_PATH).parent
        / f"split_{Path(ACADEMICO_TASK_SET_PATH).stem}.json"
    )
    return load_file(split_file)
