import json
from typing import Dict, List

from tau2.environment.environment import Environment
from tau2.domains.sanita_irigoin.data_model import ArrozDB
from tau2.domains.sanita_irigoin.tools import ArrozToolKit
from tau2.domains.sanita_irigoin.utils import (
    DB_PATH, POLICY_PATH, TASKS_PATH, SPLIT_TASKS_PATH
)


def get_environment() -> Environment:
    """Carga la base de datos y la política, retorna un objeto Environment."""
    db = ArrozDB.load(DB_PATH)
    policy = POLICY_PATH.read_text(encoding="utf-8")
    toolkit = ArrozToolKit(db=db)
    return Environment(db=db, toolkit=toolkit, policy=policy)


def get_tasks(task_split_name: str = "base"):
   tasks_raw = json.load(open(TASKS_PATH))
   splits = get_tasks_split()
   ids = splits.get(task_split_name, [])
   return [t for t in tasks_raw if t["id"] in ids]


def get_tasks_split() -> Dict[str, List[str]]:
    """Retorna el diccionario de splits de tareas."""
    with open(SPLIT_TASKS_PATH, encoding="utf-8") as f:
        return json.load(f)