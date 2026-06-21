import json
from pathlib import Path
from typing import Optional

from tau2.data_model.tasks import Task
from tau2.environment.environment import Environment
from tau2.environment.rag import THINK_INSTRUCTION, ChromaPolicyIndex

from .data_model import DivemotorDB
from .tools import DivemotorTools
from .user_tools import DivemotorUserTools


DOMAIN_DATA_PATH = Path("data/tau2/domains/divemotor_santiago")
DB_PATH = DOMAIN_DATA_PATH / "db.json"
TASKS_PATH = DOMAIN_DATA_PATH / "tasks.json"
SPLITS_PATH = DOMAIN_DATA_PATH / "split_tasks.json"
POLICY_PATH = DOMAIN_DATA_PATH / "policy.md"
POLICY_RAG_PATH = DOMAIN_DATA_PATH / "policy_rag.md"


def get_environment(
    db: Optional[DivemotorDB] = None,
    solo_mode: bool = False,
    chunking_strategy: str = "headers",
    retrieval_k: int = 3,
    use_think: bool = False,
    use_rag: bool = True,
):
    if db is None:
        with open(DB_PATH, "r", encoding="utf-8") as f:
            db = DivemotorDB(**json.load(f))

    user_tools = DivemotorUserTools(db=db)

    if use_rag:
        with open(POLICY_PATH, "r", encoding="utf-8") as f:
            policy_text = f.read()
        policy_index = ChromaPolicyIndex(
            policy_text,
            strategy=chunking_strategy,
        )
        tools = DivemotorTools(
            db=db,
            policy_index=policy_index,
            retrieval_k=retrieval_k,
        )
        with open(POLICY_RAG_PATH, "r", encoding="utf-8") as f:
            policy = f.read()
        if use_think:
            policy += THINK_INSTRUCTION
    else:
        tools = DivemotorTools(db=db)
        with open(POLICY_PATH, "r", encoding="utf-8") as f:
            policy = f.read()

    return Environment(
        domain_name="divemotor_santiago",
        policy=policy,
        tools=tools,
        user_tools=user_tools,
        solo_mode=solo_mode,
    )


def get_tasks(task_split_name="base"):
    with open(TASKS_PATH, "r", encoding="utf-8") as f:
        tasks_data = json.load(f)

    with open(SPLITS_PATH, "r", encoding="utf-8") as f:
        splits = json.load(f)

    if task_split_name not in splits:
        selected = tasks_data
    else:
        selected_ids = set(splits[task_split_name])
        selected = [t for t in tasks_data if t["id"] in selected_ids]

    return [Task(**t) for t in selected]


def get_tasks_split():
    with open(SPLITS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)
