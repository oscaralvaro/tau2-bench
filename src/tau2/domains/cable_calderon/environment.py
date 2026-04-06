from typing import Optional
from tau2.environment.environment import Environment
from tau2.data_model.tasks import Task
from tau2.domains.cable_calderon.data_model import CableCalderonDB
from tau2.domains.cable_calderon.tools import CableCalderonToolKit
from tau2.domains.cable_calderon.utils import (
    CABLE_CALDERON_DB_PATH,
    CABLE_CALDERON_TASKS_PATH,
    CABLE_CALDERON_SPLIT_TASKS_PATH,
    CABLE_CALDERON_POLICY_PATH,
)
import json


def get_environment(
    db: Optional[CableCalderonDB] = None,
    solo_mode: bool = False,
) -> Environment:
    """Carga la base de datos y la política, retorna un objeto Environment."""
    if solo_mode:
        raise ValueError("Cable Calderon domain does not support solo mode")
    if db is None:
        db = CableCalderonDB.load()
    policy = CABLE_CALDERON_POLICY_PATH.read_text(encoding="utf-8")
    toolkit = CableCalderonToolKit(db=db)
    return Environment(
        domain_name="cable_calderon",
        policy=policy,
        tools=toolkit,
    )                               

def get_tasks(task_split_name: Optional[str] = "base") -> list[Task]:
    """Carga y retorna la lista de Tasks desde tasks.json filtradas por split."""
    tasks_data = json.loads(CABLE_CALDERON_TASKS_PATH.read_text(encoding="utf-8"))
    splits = get_tasks_split()
    task_ids = splits.get(task_split_name, [])
    tasks = [Task.model_validate(t) for t in tasks_data if t["id"] in task_ids]
    return tasks


def get_tasks_split() -> dict:
    """Retorna el diccionario de splits de tareas."""
    return json.loads(CABLE_CALDERON_SPLIT_TASKS_PATH.read_text(encoding="utf-8"))