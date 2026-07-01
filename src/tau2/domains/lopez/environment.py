from pathlib import Path
from typing import Optional

from tau2.data_model.tasks import Task
from tau2.domains.lopez.data_model import GamerBitStoreDB
from tau2.domains.lopez.tools import GamerBitStoreTools
from tau2.domains.lopez.user_data_model import LopezUserDB, SMSInboxMessage
from tau2.domains.lopez.user_tools import LopezUserTools
from tau2.domains.lopez.utils import (
    GAMERBIT_STORE_DB_PATH,
    GAMERBIT_STORE_POLICY_PATH,
    GAMERBIT_STORE_POLICY_RAG_PATH,
    GAMERBIT_STORE_TASK_SET_PATH,
    GAMERBIT_STORE_USER_DB_PATH,
)
from tau2.environment.environment import Environment
from tau2.environment.rag import THINK_INSTRUCTION, ChromaPolicyIndex
from tau2.utils import load_file


class LopezEnvironment(Environment):
    tools: GamerBitStoreTools
    user_tools: LopezUserTools

    def __init__(
        self,
        domain_name: str,
        policy: str,
        tools: GamerBitStoreTools,
        user_tools: LopezUserTools,
    ) -> None:
        super().__init__(domain_name, policy, tools, user_tools)

    def use_tool(self, tool_name: str, **kwargs):
        resultado = super().use_tool(tool_name, **kwargs)
        self.sync_tools()
        return resultado

    def use_user_tool(self, tool_name: str, **kwargs):
        resultado = super().use_user_tool(tool_name, **kwargs)
        self.sync_tools()
        return resultado

    def sync_tools(self):
        if self.user_tools is None:
            return
        inbox_by_id = {sms.id: sms for sms in self.user_tools.db.sms_inbox}
        for verificacion in self.tools.db.verificaciones_sms.values():
            if verificacion.id in inbox_by_id:
                existente = inbox_by_id[verificacion.id]
                existente.codigo = verificacion.codigo
                existente.rol_requerido = verificacion.rol_requerido.value
                existente.telefono = verificacion.enviada_a
                continue
            self.user_tools.db.sms_inbox.append(
                SMSInboxMessage(
                    id=verificacion.id,
                    cliente_id=verificacion.cliente_id,
                    telefono=verificacion.enviada_a,
                    rol_requerido=verificacion.rol_requerido.value,
                    codigo=verificacion.codigo,
                    leido=False,
                )
            )


def get_environment(
    db: Optional[GamerBitStoreDB] = None,
    user_db: Optional[LopezUserDB] = None,
    solo_mode: bool = False,
    chunking_strategy: str = "headers",
    retrieval_k: int = 3,
    use_think: bool = False,
    use_rag: bool = True,
) -> Environment:
    if solo_mode:
        raise ValueError("lopez no soporta solo_mode")
    if db is None:
        db = GamerBitStoreDB.load(GAMERBIT_STORE_DB_PATH)
    if user_db is None:
        if GAMERBIT_STORE_USER_DB_PATH.exists():
            user_db = LopezUserDB.load(GAMERBIT_STORE_USER_DB_PATH)
        else:
            user_db = LopezUserDB()
    if use_rag:
        with open(GAMERBIT_STORE_POLICY_PATH, "r", encoding="utf-8") as fp:
            policy_text = fp.read()
        policy_index = ChromaPolicyIndex(policy_text, strategy=chunking_strategy)
        tools = GamerBitStoreTools(
            db,
            policy_index=policy_index,
            retrieval_k=retrieval_k,
        )
        with open(GAMERBIT_STORE_POLICY_RAG_PATH, "r", encoding="utf-8") as fp:
            policy = fp.read()
        if use_think:
            policy = policy + THINK_INSTRUCTION
    else:
        tools = GamerBitStoreTools(db)
        with open(GAMERBIT_STORE_POLICY_PATH, "r", encoding="utf-8") as fp:
            policy = fp.read()
    user_tools = LopezUserTools(user_db)
    return LopezEnvironment(
        domain_name="lopez",
        policy=policy,
        tools=tools,
        user_tools=user_tools,
    )


def get_tasks(task_split_name: Optional[str] = "base") -> list[Task]:
    tasks = load_file(GAMERBIT_STORE_TASK_SET_PATH)
    tasks = [Task.model_validate(task) for task in tasks]
    if task_split_name is None:
        return tasks
    task_splits = get_tasks_split()
    if task_split_name not in task_splits:
        raise ValueError(
            f"Invalid task split name: {task_split_name}. Valid splits are: {task_splits.keys()}"
        )
    return [task for task in tasks if task.id in task_splits[task_split_name]]


def get_tasks_split() -> dict[str, list[str]]:
    split_file = (
        Path(GAMERBIT_STORE_TASK_SET_PATH).parent
        / f"split_{Path(GAMERBIT_STORE_TASK_SET_PATH).stem}.json"
    )
    return load_file(split_file)
