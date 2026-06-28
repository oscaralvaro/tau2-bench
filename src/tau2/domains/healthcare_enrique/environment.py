import json
from tau2.environment.environment import Environment

from .data_model import HealthcareDB
from .tools import HealthcareToolkit
from .utils import get_data_path


# -------------------------
# CARGAR ENTORNO
# -------------------------

def get_environment(solo_mode=False):

    # cargar base de datos
    db_path = get_data_path("db.json")
    db = HealthcareDB.load(db_path)

    # cargar policy
    policy_path = get_data_path("policy.md")
    with open(policy_path, "r", encoding="utf-8") as f:
        policy = f.read()

    # toolkit
    toolkit = HealthcareToolkit(db)

    # crear entorno
    env = Environment(
    domain_name="healthcare_enrique",
    tools=toolkit,
    policy=policy
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