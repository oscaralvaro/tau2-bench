import json
from tau2.environment.environment import Environment
from tau2.data_model.tasks import Task
from .data_model import DivemotorDB
from .tools import DivemotorTools


def get_environment(solo_mode=False):
    import json
    from tau2.environment.environment import Environment

    with open("data/tau2/domains/divemotor_santiago/db.json") as f:
        data = json.load(f)

    # eliminar campo extra para que pydantic no falle
    data.pop("users", None)

    db = DivemotorDB(**data)

    with open("data/tau2/domains/divemotor_santiago/policy.md") as f:
        policy = f.read()

    env = Environment(
        domain_name="divemotor_santiago",
        policy=policy
    )

    env.db = db
    env.tools = DivemotorTools(db=db)

    return env


def get_tasks(task_split_name="base"):
    with open("data/tau2/domains/divemotor_santiago/tasks.json") as f:
        tasks_data = json.load(f)

    with open("data/tau2/domains/divemotor_santiago/split_tasks.json") as f:
        splits = json.load(f)

    if task_split_name not in splits:
        selected = tasks_data
    else:
        selected_ids = set(splits[task_split_name])
        selected = [t for t in tasks_data if t["id"] in selected_ids]

    return [Task(**t) for t in selected]


def get_tasks_split():
    with open("data/tau2/domains/divemotor_santiago/split_tasks.json") as f:
        return json.load(f)