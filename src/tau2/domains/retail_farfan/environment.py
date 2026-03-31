import json
from tau2.environment.environment import Environment

from .data_model import RetailDB
from .tools import RetailTools


def get_environment():
    # Cargar base de datos
    with open("data/tau2/domains/retail_farfan/db.json") as f:
        data = json.load(f)

    # Crear objeto DB
    db = RetailDB(**data)

    # Crear herramientas
    tools = RetailTools(db)

    # 🔥 CORRECCIÓN IMPORTANTE AQUÍ
    return Environment(database=db, toolkit=tools)


def get_tasks(task_split_name="base"):
    import json

    # Cargar tasks
    with open("data/tau2/domains/retail_farfan/tasks.json") as f:
        tasks = json.load(f)

    # Cargar splits
    with open("data/tau2/domains/retail_farfan/split_tasks.json") as f:
        splits = json.load(f)

    ids = splits[task_split_name]

    # Filtrar tasks
    return [t for t in tasks if t["id"] in ids]


def get_tasks_split():
    import json

    with open("data/tau2/domains/retail_farfan/split_tasks.json") as f:
        return json.load(f)
