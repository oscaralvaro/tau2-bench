from pathlib import Path
import json

from tau2.environment.environment import Environment
from tau2.domains.divemotor_sales_support_nunez.data_model import DivemotorDB
from tau2.domains.divemotor_sales_support_nunez.tools import DivemotorTools
from tau2.data_model.tasks import Task

# Rutas
BASE_PATH = Path(__file__).resolve().parent
DATA_PATH = BASE_PATH.parent.parent.parent.parent / "data" / "tau2" / "domains" / "divemotor_sales_support_nunez"


# Función para cargar JSON
def load_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


# 🔥 ENTORNO PRINCIPAL
def get_environment(solo_mode: bool = False):
    # DB
    db_data = load_json(DATA_PATH / "db.json")
    db = DivemotorDB(**db_data)

    # TOOLS (usan db)
    tools = DivemotorTools(db=db)

    # POLICY (string)
    with open(DATA_PATH / "policy.md", "r", encoding="utf-8") as f:
        policy_text = f.read()

    # ENV (ORDEN CORRECTO)
    env = Environment(
        "divemotor_sales_support_nunez",
        policy_text,
        tools
    )

    return env


# 🔥 TASKS
def get_tasks(task_split_name: str = "base"):
    tasks = load_json(DATA_PATH / "tasks.json")
    splits = load_json(DATA_PATH / "split_tasks.json")

    if task_split_name not in splits:
        raise ValueError(f"Split {task_split_name} no existe")

    task_ids = set(splits[task_split_name])

    # 🔥 CONVERSIÓN A OBJETOS Task
    filtered_tasks = [
        Task(**t) for t in tasks if t["id"] in task_ids
    ]

    return filtered_tasks


# 🔥 SPLITS
def get_tasks_split():
    return load_json(DATA_PATH / "split_tasks.json")

