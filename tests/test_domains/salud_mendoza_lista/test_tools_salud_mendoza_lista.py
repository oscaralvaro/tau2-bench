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


def test_create_appointment_reservation_updates_state():
    env = get_environment()
    res = env.tools.use_tool(
        "create_appointment_reservation",
        id_interconsulta="IC-002",
        slot_id="SLOT-2",
    )
    assert "RESERVA EXITOSA" in res
    assert env.tools.db.interconsultas["IC-002"].estado == "Agendado"
    assert "SLOT-2" not in env.tools.db.agenda_disponible


def test_update_priority_updates_db():
    env = get_environment()
    res = env.tools.use_tool(
        "update_priority",
        id_interconsulta="IC-005",
        nueva_prioridad="Urgente",
    )
    assert "Urgente" in res
    assert env.tools.db.interconsultas["IC-005"].prioridad == "Urgente"


def test_transfer_to_human_agents_message():
    env = get_environment()
    res = env.tools.use_tool(
        "transfer_to_human_agents",
        summary="Paciente muy molesto y solicita supervisor.",
    )
    assert res == "YOU ARE BEING TRANSFERRED TO A HUMAN AGENT. PLEASE HOLD ON."


def test_create_appointment_reservation_rejects_wrong_specialty():
    env = get_environment()
    res = env.tools.use_tool(
        "create_appointment_reservation",
        id_interconsulta="IC-002",
        slot_id="SLOT-1",
    )
    assert "no corresponde a la especialidad" in res
    assert env.tools.db.interconsultas["IC-002"].estado == "En Espera"
    assert "SLOT-1" in env.tools.db.agenda_disponible
