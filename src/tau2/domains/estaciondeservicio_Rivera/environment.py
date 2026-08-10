# Copyright Sierra
from pathlib import Path
from typing import Optional

from tau2.data_model.tasks import Task
from tau2.domains.estaciondeservicio_Rivera.data_model import GrifoDB
from tau2.domains.estaciondeservicio_Rivera.user_data_model import (
    RiveraUserDB,
    SMSInboxMessage,
)
from tau2.domains.estaciondeservicio_Rivera.tools import (
    EstacionDeServicioRiveraTools,
)
from tau2.domains.estaciondeservicio_Rivera.user_tools import (
    EstacionDeServicioRiveraUserTools,
)
from tau2.domains.estaciondeservicio_Rivera.utils import (
    ESTACIONDESERVICIO_RIVERA_DB_PATH,
    ESTACIONDESERVICIO_RIVERA_POLICY_PATH,
    ESTACIONDESERVICIO_RIVERA_TASK_SET_PATH,
    ESTACIONDESERVICIO_RIVERA_USER_DB_PATH,
)
from tau2.environment.environment import Environment
from tau2.utils import get_dict_hash, load_file


class EstacionDeServicioRiveraEnvironment(Environment):
    tools: EstacionDeServicioRiveraTools
    user_tools: EstacionDeServicioRiveraUserTools

    @staticmethod
    def _remove_sms_reason_from_hash(db_dump: dict) -> dict:
        """Keep SMS reason user-facing, but do not make DB reward depend on it."""
        for verification in db_dump.get("sms_verifications", {}).values():
            verification["reason"] = None
        for message in db_dump.get("sms_inbox", {}).values():
            message["reason"] = None
        return db_dump

    def get_db_hash(self) -> Optional[str]:
        if self.tools is None:
            return None
        db_dump = self.tools.db.model_dump()
        return get_dict_hash(self._remove_sms_reason_from_hash(db_dump))

    def get_user_db_hash(self) -> Optional[str]:
        if self.user_tools is None:
            return None
        db_dump = self.user_tools.db.model_dump()
        return get_dict_hash(self._remove_sms_reason_from_hash(db_dump))

    def sync_tools(self):
        if self.user_tools is None:
            return

        inbox = {}
        session = self.user_tools.db.session
        for verification in self.tools.db.sms_verifications.values():
            if session.customer_id is not None and verification.id_cliente != session.customer_id:
                continue
            if verification.role != session.role:
                continue
            if verification.user_id is not None and session.user_id != verification.user_id:
                continue
            if session.telefono is not None and verification.destination_phone != session.telefono:
                continue
            previous = self.user_tools.db.sms_inbox.get(verification.verification_id)
            consumed = previous.consumed if previous is not None else False
            inbox[verification.verification_id] = SMSInboxMessage(
                verification_id=verification.verification_id,
                customer_id=verification.id_cliente,
                role=verification.role,
                user_id=verification.user_id,
                phone=verification.destination_phone,
                code=verification.code,
                reason=verification.reason,
                sent_at=verification.sent_at,
                consumed=consumed,
            )
        self.user_tools.db.sms_inbox = inbox


def get_environment(
    db: Optional[GrifoDB] = None,
    user_db: Optional[RiveraUserDB] = None,
    solo_mode: bool = False,
) -> Environment:
    if solo_mode:
        raise ValueError("estaciondeservicio_Rivera domain does not support solo mode")
    if db is None:
        db = GrifoDB.load(ESTACIONDESERVICIO_RIVERA_DB_PATH)
    if user_db is None:
        if ESTACIONDESERVICIO_RIVERA_USER_DB_PATH.exists():
            user_db = RiveraUserDB.load(ESTACIONDESERVICIO_RIVERA_USER_DB_PATH)
        else:
            user_db = RiveraUserDB()
    tools = EstacionDeServicioRiveraTools(db)
    user_tools = EstacionDeServicioRiveraUserTools(user_db)
    with open(ESTACIONDESERVICIO_RIVERA_POLICY_PATH, "r") as fp:
        policy = fp.read()
    return EstacionDeServicioRiveraEnvironment(
        domain_name="estaciondeservicio_Rivera",
        policy=policy,
        tools=tools,
        user_tools=user_tools,
    )


def get_tasks(task_split_name: Optional[str] = "base") -> list[Task]:
    tasks = load_file(ESTACIONDESERVICIO_RIVERA_TASK_SET_PATH)
    tasks = [Task.model_validate(task) for task in tasks]
    if task_split_name is None:
        return tasks
    task_splits = get_tasks_split()
    if task_split_name not in task_splits:
        raise ValueError(
            f"Invalid task split name: {task_split_name}. Valid splits are: {task_splits.keys()}"
        )
    tasks = [task for task in tasks if task.id in task_splits[task_split_name]]
    return tasks


def get_tasks_split() -> dict[str, list[str]]:
    split_file = (
        Path(ESTACIONDESERVICIO_RIVERA_TASK_SET_PATH).parent
        / f"split_{Path(ESTACIONDESERVICIO_RIVERA_TASK_SET_PATH).stem}.json"
    )
    return load_file(split_file)
