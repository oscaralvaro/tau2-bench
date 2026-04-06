from tau2.domains.salud_mendoza_lista.environment import get_environment, get_tasks
from tau2.domains.salud_mendoza_lista.data_model import Paciente, SaludDB
from tau2.domains.salud_mendoza_lista.tools import SaludToolkit


def test_get_patient_details():
    db = SaludDB()
    db.pacientes["12.345.678-9"] = Paciente(
        rut="12.345.678-9",
        nombre="Juan",
        prevision="Fonasa A",
        comuna="Piura",
    )
    toolkit = SaludToolkit(db)
    res = toolkit.get_patient_details("12.345.678-9")
    assert "Juan" in res


def test_lista_environment_loading():
    env = get_environment()
    assert env is not None
    assert env.tools is not None
    assert env.tools.db is not None


def test_lista_tools_existence():
    env = get_environment()
    tool_names = set(env.tools.get_tools().keys())
    assert "get_patient_details" in tool_names
    assert "search_waiting_list_by_rut" in tool_names
    assert "create_appointment_reservation" in tool_names
    assert "update_priority" in tool_names
    assert "transfer_to_human_agents" in tool_names


def test_lista_task_loading():
    tasks = get_tasks("base")
    assert len(tasks) == 10
    assert tasks[0].user_scenario.instructions.domain == "salud_mendoza_lista"
