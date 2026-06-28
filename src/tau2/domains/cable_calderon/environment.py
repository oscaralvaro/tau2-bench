from typing import Optional
import json

from tau2.environment.environment import Environment
from tau2.environment.rag import ChromaPolicyIndex, THINK_INSTRUCTION
from tau2.data_model.tasks import Task
from tau2.domains.cable_calderon.data_model import CableCalderonDB
from tau2.domains.cable_calderon.tools import CableCalderonToolKit
from tau2.domains.cable_calderon.user_tools import CableUserToolKit
from tau2.domains.cable_calderon.utils import (
    CABLE_CALDERON_DB_PATH,
    CABLE_CALDERON_TASKS_PATH,
    CABLE_CALDERON_SPLIT_TASKS_PATH,
    CABLE_CALDERON_POLICY_PATH,
    CABLE_CALDERON_POLICY_RAG_PATH,
)
_POLICY_INDEX_CACHE = {}


def get_cached_policy_index(chunking_strategy: str):
    cache_key = (
        str(CABLE_CALDERON_POLICY_PATH),
        CABLE_CALDERON_POLICY_PATH.stat().st_mtime_ns,
        chunking_strategy,
    )

    if cache_key not in _POLICY_INDEX_CACHE:
        policy_text = CABLE_CALDERON_POLICY_PATH.read_text(encoding="utf-8")
        _POLICY_INDEX_CACHE[cache_key] = ChromaPolicyIndex(
            policy_text,
            strategy=chunking_strategy,
        )

    return _POLICY_INDEX_CACHE[cache_key]

def get_environment(
    db: Optional[CableCalderonDB] = None,
    solo_mode: bool = False,
    chunking_strategy: str = "headers",
    retrieval_k: int = 3,
    use_think: bool = False,
    use_rag: bool = True,
) -> Environment:
    if solo_mode:
        raise ValueError("Cable Calderon domain does not support solo mode")

    if db is None:
        db = CableCalderonDB.load()

    if use_rag:
        policy_index = get_cached_policy_index(chunking_strategy)
        policy = CABLE_CALDERON_POLICY_RAG_PATH.read_text(encoding="utf-8")
        toolkit = CableCalderonToolKit(
            db=db,
            policy_index=policy_index,
            retrieval_k=retrieval_k,
        )
    else:
        policy = CABLE_CALDERON_POLICY_PATH.read_text(encoding="utf-8")
        toolkit = CableCalderonToolKit(db=db)

    if use_think:
        policy = policy + THINK_INSTRUCTION

    user_toolkit = CableUserToolKit(db=db)

    return Environment(
        domain_name="cable_calderon",
        policy=policy,
        tools=toolkit,
        user_tools=user_toolkit,
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