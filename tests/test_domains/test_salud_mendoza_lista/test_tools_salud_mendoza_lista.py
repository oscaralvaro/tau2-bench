from tau2.domains.salud_mendoza_lista.environment import get_environment, get_tasks
from tau2.domains.salud_mendoza_lista.data_model import (
    MedicoAPS,
    Paciente,
    ProtocoloDerivacion,
    SaludDB,
)
from tau2.domains.salud_mendoza_lista.tools import SaludToolkit
from tau2.domains.salud_mendoza_lista.user_tools import SaludUserToolkit


# ─────────────────────────────────────────
# Tests originales (corregidos)
# ─────────────────────────────────────────

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
    # Nuevas herramientas
    assert "send_sms_verification_code" in tool_names
    assert "verify_sms_code" in tool_names
    assert "search_derivation_protocol" in tool_names
    assert "create_interconsulta_from_aps" in tool_names


def test_lista_task_loading():
    tasks = get_tasks("base")
    assert len(tasks) == 20
    assert tasks[0].user_scenario.instructions.domain == "salud_mendoza_lista"


# ─────────────────────────────────────────
# Tests SMS: send_sms_verification_code
# ─────────────────────────────────────────

def test_send_sms_paciente_existente():
    env = get_environment()
    toolkit = SaludToolkit(env.tools.db)
    resultado = toolkit.send_sms_verification_code(rut="15.222.333-k")
    assert "SMS ENVIADO" in resultado
    assert "15.222.333-k" in toolkit.db.sms_verification_codes


def test_send_sms_paciente_no_existe():
    env = get_environment()
    toolkit = SaludToolkit(env.tools.db)
    resultado = toolkit.send_sms_verification_code(rut="99.999.999-9")
    assert "ERROR" in resultado


# ─────────────────────────────────────────
# Tests SMS: verify_sms_code
# ─────────────────────────────────────────

def test_verify_sms_codigo_correcto():
    env = get_environment()
    toolkit = SaludToolkit(env.tools.db)
    toolkit.send_sms_verification_code(rut="10.444.555-6")
    codigo_real = toolkit.db.sms_verification_codes["10.444.555-6"]
    resultado = toolkit.verify_sms_code(rut="10.444.555-6", codigo=codigo_real)
    assert "EXITOSA" in resultado
    assert "10.444.555-6" not in toolkit.db.sms_verification_codes


def test_verify_sms_codigo_incorrecto():
    env = get_environment()
    toolkit = SaludToolkit(env.tools.db)
    toolkit.send_sms_verification_code(rut="18.666.777-8")
    resultado = toolkit.verify_sms_code(rut="18.666.777-8", codigo="000000")
    assert "FALLIDA" in resultado
    assert "18.666.777-8" in toolkit.db.sms_verification_codes


def test_verify_sms_sin_codigo_previo():
    env = get_environment()
    toolkit = SaludToolkit(env.tools.db)
    resultado = toolkit.verify_sms_code(rut="12.888.999-0", codigo="123456")
    assert "ERROR" in resultado


# ─────────────────────────────────────────
# Tests user_tools: get_sms_verification_code
# ─────────────────────────────────────────

def test_user_get_sms_code_despues_de_envio():
    env = get_environment()
    toolkit = SaludToolkit(env.tools.db)
    user_toolkit = SaludUserToolkit(env.tools.db)
    toolkit.send_sms_verification_code(rut="20.111.222-3")
    codigo_agente = toolkit.db.sms_verification_codes["20.111.222-3"]
    resultado = user_toolkit.get_sms_verification_code(rut="20.111.222-3")
    assert resultado["exito"] is True
    assert resultado["codigo"] == codigo_agente


def test_user_get_sms_code_sin_envio_previo():
    env = get_environment()
    user_toolkit = SaludUserToolkit(env.tools.db)
    resultado = user_toolkit.get_sms_verification_code(rut="15.222.333-k")
    assert resultado["exito"] is False
    assert resultado["codigo"] is None


# ─────────────────────────────────────────
# Tests RAG: search_derivation_protocol
# ─────────────────────────────────────────

def test_search_protocol_colelitiasis():
    env = get_environment()
    toolkit = SaludToolkit(env.tools.db)
    resultado = toolkit.search_derivation_protocol(
        especialidad="Cirugia Digestiva",
        condicion="Colelitiasis"
    )
    assert "PROTOCOLO ENCONTRADO" in resultado
    assert "Ecografia" in resultado
    assert "Hemograma" in resultado


def test_search_protocol_glaucoma():
    env = get_environment()
    toolkit = SaludToolkit(env.tools.db)
    resultado = toolkit.search_derivation_protocol(
        especialidad="Oftalmologia",
        condicion="Glaucoma"
    )
    assert "PROTOCOLO ENCONTRADO" in resultado
    assert "Tonometria" in resultado


def test_search_protocol_condicion_inexistente():
    env = get_environment()
    toolkit = SaludToolkit(env.tools.db)
    resultado = toolkit.search_derivation_protocol(
        especialidad="Dermatologia",
        condicion="Psoriasis"
    )
    assert "NO ENCONTRADO" in resultado


# ─────────────────────────────────────────
# Tests RAG: get_medico_details
# ─────────────────────────────────────────

def test_get_medico_existente():
    env = get_environment()
    toolkit = SaludToolkit(env.tools.db)
    resultado = toolkit.get_medico_details(codigo_medico="MED-001")
    assert "MEDICO ENCONTRADO" in resultado
    assert "Roberto Fuentes" in resultado


def test_get_medico_no_existe():
    env = get_environment()
    toolkit = SaludToolkit(env.tools.db)
    resultado = toolkit.get_medico_details(codigo_medico="MED-999")
    assert "ERROR" in resultado


# ─────────────────────────────────────────
# Tests RAG: create_interconsulta_from_aps
# ─────────────────────────────────────────

def test_create_interconsulta_exitoso():
    env = get_environment()
    toolkit = SaludToolkit(env.tools.db)
    n_inicial = len(toolkit.db.interconsultas)
    resultado = toolkit.create_interconsulta_from_aps(
        codigo_medico="MED-002",
        rut_paciente_referido="10.444.555-6",
        condicion="Glaucoma",
        especialidad_destino="Oftalmologia",
        examenes_adjuntos=["Tonometria bilateral", "Fondo de ojo", "Agudeza visual"],
        notas_clinicas="PIO 24 mmHg en ojo derecho."
    )
    assert "INTERCONSULTA CREADA" in resultado
    assert len(toolkit.db.interconsultas) == n_inicial + 1


def test_create_interconsulta_medico_invalido():
    env = get_environment()
    toolkit = SaludToolkit(env.tools.db)
    resultado = toolkit.create_interconsulta_from_aps(
        codigo_medico="MED-999",
        rut_paciente_referido="15.222.333-k",
        condicion="Cataratas",
        especialidad_destino="Oftalmologia",
        examenes_adjuntos=["Agudeza visual"]
    )
    assert "ERROR" in resultado