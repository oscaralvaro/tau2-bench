import json
from pathlib import Path
from tau2.environment.environment import Environment
from tau2.environment.rag import ChromaPolicyIndex, THINK_INSTRUCTION

from .user_data_model import HealthcareUserDB
from .user_tools import HealthcareUserTools
from .data_model import HealthcareDB
from .tools import HealthcareToolkit
from .utils import get_data_path

_POLICY_INDEX_CACHE = {}

# -------------------------
# CARGAR ENTORNO
# -------------------------
def get_cached_policy_index(policy_path, chunking_strategy):
    policy_path = Path(policy_path)
    cache_key = (
        str(policy_path),
        policy_path.stat().st_mtime_ns,
        chunking_strategy,
    )

    if cache_key not in _POLICY_INDEX_CACHE:
        print(">>> Construyendo índice RAG...")
        with open(policy_path, "r", encoding="utf-8") as f:
            policy_text = f.read()

        _POLICY_INDEX_CACHE[cache_key] = ChromaPolicyIndex(
            policy_text,
            strategy=chunking_strategy,
        )

    return _POLICY_INDEX_CACHE[cache_key]


def get_environment(
    db=None,
    solo_mode=False,
    chunking_strategy="headers",
    retrieval_k=3,
    use_think=False,
    use_rag=True,
):

    # cargar base de datos
    if db is None:
        db_path = get_data_path("db.json")
        db = HealthcareDB.load(db_path)

    user_db = HealthcareUserDB()
    user_tools = HealthcareUserTools(user_db)

    # cargar policy
    policy_path = get_data_path("policy.md")
    policy_rag_path = get_data_path("policy_rag.md")
    if use_rag:
        policy_index = get_cached_policy_index(
            policy_path,
            chunking_strategy,
        )

        toolkit = HealthcareToolkit(
            db,
            policy_index=policy_index,
            retrieval_k=retrieval_k,
        )

        with open(policy_rag_path, "r", encoding="utf-8") as f:
            policy = f.read()

        if use_think:
            policy = policy + THINK_INSTRUCTION

    else:
        toolkit = HealthcareToolkit(db)

        with open(policy_path, "r", encoding="utf-8") as f:
            policy = f.read()

    env = Environment(
        domain_name="healthcare_enrique",
        tools=toolkit,
        user_tools=user_tools,
        policy=policy,
        solo_mode=solo_mode,
)

    return env


# -------------------------
# CARGAR TASKS
# -------------------------

def get_tasks(task_split_name="base"):
    tasks_path = get_data_path("tasks.json")

    from tau2.data_model.tasks import Task

    with open(tasks_path, "r", encoding="utf-8") as f:
        raw_tasks = json.load(f)

    tasks = [Task(**t) for t in raw_tasks]

    splits = get_tasks_split()
    if task_split_name in splits:
        task_ids = splits[task_split_name]
        tasks = [t for t in tasks if t.id in task_ids]

    return tasks


# -------------------------
# SPLITS
# -------------------------

def get_tasks_split():
    split_path = get_data_path("split_tasks.json")

    with open(split_path, "r", encoding="utf-8") as f:
        splits = json.load(f)

    return splits