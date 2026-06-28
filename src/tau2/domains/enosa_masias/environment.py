import os
from typing import Optional
from tau2.data_model.tasks import Task
from tau2.domains.enosa_masias.data_model import EnosaDB
from tau2.domains.enosa_masias.tools import EnosaToolKit
from tau2.domains.enosa_masias.user_tools import EnosaUserToolKit
from tau2.domains.enosa_masias.utils import (
    ENOSA_DB_PATH, ENOSA_POLICY_PATH, ENOSA_TASK_SPLIT_PATH, ENOSA_TASK_SET_PATH,
)
from tau2.environment.environment import Environment
from tau2.environment.rag import ChromaPolicyIndex, THINK_INSTRUCTION
from tau2.utils import load_file

# Definimos la ruta del nuevo policy_rag.md
ENOSA_POLICY_RAG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "data", "tau2", "domains", "enosa_masias", "policy_rag.md")

def get_environment(
    db: Optional[EnosaDB] = None, 
    solo_mode: bool = False,
    chunking_strategy="headers",
    retrieval_k=3,
    use_think=False,
    use_rag=True,
) -> Environment:
    if solo_mode: raise ValueError("ENOSA no soporta solo_mode")
    if db is None: db = EnosaDB.load(ENOSA_DB_PATH)
    
    # Cargamos la política completa original para indexarla
    with open(ENOSA_POLICY_PATH, "r", encoding="utf-8") as fp:
        policy_full_text = fp.read()

    # Construimos el índice y las herramientas dependiendo de si usamos RAG o no
    if use_rag:
        policy_index = ChromaPolicyIndex(policy_full_text, strategy=chunking_strategy)
        tools = EnosaToolKit(db, policy_index=policy_index, retrieval_k=retrieval_k)
        
        # Leemos el system prompt resumido (el de E4)
        with open(ENOSA_POLICY_RAG_PATH, "r", encoding="utf-8") as fp:
            policy_text = fp.read()
    else:
        # Condición A (Baseline sin RAG)
        tools = EnosaToolKit(db)
        policy_text = policy_full_text
        
    user_tools = EnosaUserToolKit(db)
    
    if use_think:
        policy_text = policy_text + "\n\n" + THINK_INSTRUCTION
        
    return Environment(
        domain_name="enosa_masias", 
        policy=policy_text, 
        tools=tools, 
        user_tools=user_tools
    )

def get_tasks(task_split_name: Optional[str] = "base") -> list[Task]:
    tasks = load_file(ENOSA_TASK_SET_PATH)
    tasks = [Task.model_validate(task) for task in tasks]
    
    if task_split_name is None: return tasks
    
    task_splits = get_tasks_split()
    if task_split_name not in task_splits:
        raise ValueError(f"Split '{task_split_name}' no encontrado. Usa: {list(task_splits.keys())}")
        
    return [t for t in tasks if t.id in task_splits[task_split_name]]

def get_tasks_split() -> dict[str, list[str]]:
    return load_file(ENOSA_TASK_SPLIT_PATH)