# src/tau2/domains/academico_jefersoncorrea/environment.py
from pathlib import Path
from typing import Optional

from tau2.data_model.tasks import Task
from tau2.domains.academico_jefersoncorrea.data_model import AcademicDB
from tau2.domains.academico_jefersoncorrea.tools import AcademicTools
from tau2.domains.academico_jefersoncorrea.utils import (
    ACADEMICO_DB_PATH,
    ACADEMICO_POLICY_PATH,
    ACADEMICO_TASK_SET_PATH,
)
from tau2.environment.environment import Environment
from tau2.utils import load_file


def get_environment(
    db: Optional[AcademicDB] = None,
    solo_mode: bool = False,
) -> Environment:
    """
    Inicializa y devuelve el entorno de evaluación para el dominio académico.
    Carga la base de datos, inicializa las herramientas y lee la política.
    """
    if solo_mode:
        raise ValueError("El dominio académico no soporta el modo solitario (solo mode)")
    
    if db is None:
        db = AcademicDB.load(ACADEMICO_DB_PATH)
        
    tools = AcademicTools(db)
    
    # encoding="utf-8" es crucial para que lea bien las tildes de nuestro policy.md en español
    with open(ACADEMICO_POLICY_PATH, "r", encoding="utf-8") as fp:
        policy = fp.read()
        
    return Environment(
        domain_name="academico_jefersoncorrea",
        policy=policy,
        tools=tools,
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
            f"Nombre de split inválido: {task_split_name}. Los válidos son: {list(task_splits.keys())}"
        )
        
    return [task for task in tasks if task.id in task_splits[task_split_name]]


def get_tasks_split() -> dict[str, list[str]]:
    """
    Carga las divisiones (splits) de las tareas, usualmente para separar entre datos de prueba y validación.
    """
    split_file = (
        Path(ACADEMICO_TASK_SET_PATH).parent
        / f"split_{Path(ACADEMICO_TASK_SET_PATH).stem}.json"
    )
    return load_file(split_file)