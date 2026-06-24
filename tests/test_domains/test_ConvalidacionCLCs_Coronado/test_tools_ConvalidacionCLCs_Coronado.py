import json

import pytest
from loguru import logger

from tau2.data_model.message import ToolCall, ToolMessage
from tau2.domains.ConvalidacionCLCs_Coronado.data_model import (
    ConvalidacionCLCDB,
    Estudiante,
    Solicitud,
)
from tau2.domains.ConvalidacionCLCs_Coronado.environment import get_environment
from tau2.domains.ConvalidacionCLCs_Coronado.tools import ConvalidacionCLCTools
from tau2.environment.environment import Environment
from tau2.environment.rag import ChromaPolicyIndex


@pytest.fixture
def convalidacion_db() -> ConvalidacionCLCDB:
    return ConvalidacionCLCDB(
        estudiantes=[
            {
                "carnet": "2020123456",
                "nombre_completo": "SUAREZ PEÑA PABLO",
                "programa": "IME",
                "clcs_validados": [2],
                "clcs_validados_ids": ["clc2"],
                "cantidad_clcs_validados": 1,
            },
            {
                "carnet": "2020987654",
                "nombre_completo": "RAMIREZ LOPEZ ANA",
                "programa": "IC",
                "clcs_validados": [],
                "clcs_validados_ids": [],
                "cantidad_clcs_validados": 0,
            },
        ],
        congresos_preaprobados={
            "IC": ["CONEIC"],
            "IIS": ["CONEII", "INTERCON"],
            "IME": ["CONEIMERA", "INTERCON"],
        },
        bienales_arquitectura=["BIENAL DE ARQUITECTURA 2025"],
        horas_certificados=[
            {
                "carnet": "2020123456",
                "actividad": "YOUTH FOR DEVELOPMENT 2024",
                "horas_pdf": 20,
            },
            {
                "carnet": "2020987654",
                "actividad": "CONEIC 2025",
                "horas_pdf": 24,
            },
        ],
        certificados_pdf=[
            {
                "carnet": "2020123456",
                "actividad": "YOUTH FOR DEVELOPMENT 2024",
                "tipo_actividad": "Actividades Externas",
                "horas_pdf": 20,
                "incluye_carnet": True,
                "incluye_nombre_actividad": True,
                "incluye_tipo_actividad": True,
                "incluye_horas_totales": True,
                "incluye_nota": True,
                "nota": 15,
            },
            {
                "carnet": "2020987654",
                "actividad": "CONEIC 2025",
                "tipo_actividad": "Congresos",
                "horas_pdf": 24,
                "incluye_carnet": False,
                "incluye_nombre_actividad": True,
                "incluye_tipo_actividad": True,
                "incluye_horas_totales": True,
                "incluye_nota": False,
                "nota": None,
            },
        ],
        pagos_derecho_academico=[
            {
                "carnet": "2020334455",
                "actividad": "CURSO EXTERNO DE PRUEBA",
                "pagado": True,
            }
        ],
        solicitudes=[],
    )


@pytest.fixture
def environment(convalidacion_db: ConvalidacionCLCDB) -> Environment:
    # use_rag=False: los tests de tools usan la política completa y no construyen
    # el índice ChromaDB (que requeriría API key). Mismo patrón que el dominio burger.
    return get_environment(convalidacion_db, use_rag=False)


@pytest.fixture
def get_estudiante_details_call() -> ToolCall:
    return ToolCall(
        id="0", name="get_estudiante_details", arguments={"carnet": "2020123456"}
    )


def test_get_estudiante_details(
    environment: Environment, get_estudiante_details_call: ToolCall
):
    response = environment.get_response(get_estudiante_details_call)
    assert not response.error
    data = json.loads(response.content)
    assert data["nombre_completo"] == "SUAREZ PEÑA PABLO"
    assert data["clcs_validados"] == [2]
    assert data["clcs_validados_ids"] == ["clc2"]
    assert data["cantidad_clcs_validados"] == 1

    # Test non-existent carnet
    get_estudiante_details_call.arguments["carnet"] = "0000000000"
    response = environment.get_response(get_estudiante_details_call)
    assert response.error


@pytest.fixture
def listar_actividades_call() -> ToolCall:
    return ToolCall(
        id="1", name="listar_actividades_preaprobadas", arguments={"programa": "IME"}
    )


def test_listar_actividades_preaprobadas(
    environment: Environment, listar_actividades_call: ToolCall
):
    response = environment.get_response(listar_actividades_call)
    assert not response.error
    activities = json.loads(response.content)
    assert "CONEIMERA" in activities
    assert "INTERCON" in activities


@pytest.fixture
def get_estudiante_clc_status_call() -> ToolCall:
    return ToolCall(
        id="1b", name="get_estudiante_clc_status", arguments={"carnet": "2020123456"}
    )


def test_get_estudiante_clc_status(
    environment: Environment, get_estudiante_clc_status_call: ToolCall
):
    response = environment.get_response(get_estudiante_clc_status_call)
    assert not response.error
    data = json.loads(response.content)
    assert data["programa"] == "IME"
    assert data["cantidad_clcs_validados"] == "1"
    assert data["clcs_validados"] == ["2"]
    assert data["clcs_validados_ids"] == ["clc2"]
    assert data["maximo_clcs"] == "4"
    assert data["clcs_disponibles"] == ["1", "3", "4"]
    assert data["clcs_disponibles_ids"] == ["clc1", "clc3", "clc4"]
    assert data["tiene_todos_los_clcs"] == "False"


@pytest.fixture
def get_clcs_permitidos_call() -> ToolCall:
    return ToolCall(
        id="1c",
        name="get_clcs_permitidos_para_actividad",
        arguments={"programa": "ARQ", "categoria_actividad": "Congresos/Bienales"},
    )


def test_get_clcs_permitidos_para_actividad(
    environment: Environment, get_clcs_permitidos_call: ToolCall
):
    response = environment.get_response(get_clcs_permitidos_call)
    assert not response.error
    data = json.loads(response.content)
    assert data["programa"] == "ARQ"
    assert data["clcs_permitidos"] == ["7", "8"]
    assert data["clcs_permitidos_ids"] == ["clc7", "clc8"]

    get_clcs_permitidos_call.arguments["categoria_actividad"] = "Categoria invalida"
    response = environment.get_response(get_clcs_permitidos_call)
    assert response.error


@pytest.fixture
def verificar_pago_call() -> ToolCall:
    return ToolCall(
        id="2",
        name="verificar_pago_derecho_academico",
        arguments={"carnet": "2020334455", "actividad": "CURSO EXTERNO DE PRUEBA"},
    )


def test_verificar_pago_derecho_academico(
    environment: Environment, verificar_pago_call: ToolCall
):
    response = environment.get_response(verificar_pago_call)
    assert not response.error
    assert json.loads(response.content) == "True"

    # Test non-existent payment
    verificar_pago_call.arguments["actividad"] = "ACTIVIDAD INEXISTENTE"
    response = environment.get_response(verificar_pago_call)
    assert json.loads(response.content) == "False"


@pytest.fixture
def verificar_horas_certificado_call() -> ToolCall:
    return ToolCall(
        id="2b",
        name="verificar_horas_certificado",
        arguments={
            "carnet": "2020123456",
            "actividad": "YOUTH FOR DEVELOPMENT 2024",
        },
    )


def test_verificar_horas_certificado(
    environment: Environment, verificar_horas_certificado_call: ToolCall
):
    response = environment.get_response(verificar_horas_certificado_call)
    assert not response.error
    data = json.loads(response.content)
    assert data["horas_pdf"] == "20"
    assert data["carnet"] == "2020123456"

    # Test non-existent activity
    verificar_horas_certificado_call.arguments["actividad"] = "ACTIVIDAD INEXISTENTE"
    response = environment.get_response(verificar_horas_certificado_call)
    assert response.error


@pytest.fixture
def verificar_detalles_certificado_call() -> ToolCall:
    return ToolCall(
        id="2c",
        name="verificar_detalles_certificado",
        arguments={
            "carnet": "2020123456",
            "actividad": "YOUTH FOR DEVELOPMENT 2024",
        },
    )


def test_verificar_detalles_certificado(
    environment: Environment, verificar_detalles_certificado_call: ToolCall
):
    response = environment.get_response(verificar_detalles_certificado_call)
    assert not response.error
    data = json.loads(response.content)
    assert data["tipo_actividad"] == "Actividades Externas"
    assert data["horas_pdf"] == "20"
    assert data["incluye_carnet"] == "True"
    assert data["incluye_nota"] == "True"
    assert data["nota"] == "15"
    assert data["campos_obligatorios_presentes"] == "True"
    assert data["nota_aprobatoria"] == "True"

    verificar_detalles_certificado_call.arguments["carnet"] = "0000000000"
    response = environment.get_response(verificar_detalles_certificado_call)
    assert response.error


@pytest.fixture
def crear_solicitud_call() -> ToolCall:
    return ToolCall(
        id="3",
        name="crear_solicitud",
        arguments={
            "carnet": "2020123456",
            "nombre_completo": "SUAREZ PEÑA PABLO",
            "programa": "IME",
            "actividad": "YOUTH FOR DEVELOPMENT 2024",
            "evaluado_con_nota": True,
            "clc": 3,
            "archivo": "IME - SUAREZ PEÑA PABLO_YOUTH FOR DEVELOPMENT 2024.pdf",
            "horas_declaradas": 20,
            "status": "IN PROCESS",
            "nota": 15,
        },
    )


def test_crear_solicitud(environment: Environment, crear_solicitud_call: ToolCall):
    response = environment.get_response(crear_solicitud_call)
    assert not response.error
    solicitud = json.loads(response.content)
    assert solicitud["carnet"] == "2020123456"
    assert solicitud["status"] == "IN PROCESS"
    assert solicitud["clc"] == 3
    assert solicitud["clc_id"] == "clc3"
    assert solicitud["nota"] == 15
    assert solicitud["request_id"].startswith("REQ-")

    # Test APPROVED status updates student profile
    crear_solicitud_call.arguments["status"] = "APPROVED"
    crear_solicitud_call.arguments["clc"] = 4
    response = environment.get_response(crear_solicitud_call)
    assert not response.error

    # Verify student has the new CLC
    estudiante = environment.tools.get_estudiante_details("2020123456")
    assert 4 in estudiante.clcs_validados
    assert "clc4" in estudiante.clcs_validados_ids
    assert estudiante.cantidad_clcs_validados == 2


@pytest.fixture
def consultar_estado_call() -> ToolCall:
    return ToolCall(
        id="4", name="consultar_estado_solicitud", arguments={"request_id": "REQ-NONE"}
    )


def test_consultar_estado_solicitud(
    environment: Environment,
    consultar_estado_call: ToolCall,
    crear_solicitud_call: ToolCall,
):
    # First create a request
    response_crear = environment.get_response(crear_solicitud_call)
    request_id = json.loads(response_crear.content)["request_id"]

    # Now consult it
    consultar_estado_call.arguments["request_id"] = request_id
    response = environment.get_response(consultar_estado_call)
    assert not response.error
    solicitud = json.loads(response.content)
    assert solicitud["request_id"] == request_id

    # Test non-existent request
    consultar_estado_call.arguments["request_id"] = "REQ-INVALID"
    response = environment.get_response(consultar_estado_call)
    assert response.error


@pytest.fixture
def transfer_call() -> ToolCall:
    return ToolCall(
        id="5",
        name="transfer_to_human_agent",
        arguments={"summary": "El usuario insiste en una excepción."},
    )


def test_transfer_to_human_agent(environment: Environment, transfer_call: ToolCall):
    response = environment.get_response(transfer_call)
    assert not response.error
    assert response.content == "YOU ARE BEING TRANSFERRED TO A HUMAN AGENT. PLEASE WAIT."


# ──────────────────────────────────────────────
# SMS verification tools
# ──────────────────────────────────────────────


@pytest.fixture
def send_sms_call() -> ToolCall:
    return ToolCall(
        id="sms-1",
        name="send_sms_verification",
        arguments={"user_id": "2020112233"},
    )


def test_send_sms_verification(environment: Environment, send_sms_call: ToolCall):
    response = environment.get_response(send_sms_call)
    assert not response.error
    # A code must have been stored for this user
    assert "2020112233" in environment.tools._sms_codes
    stored_code = environment.tools._sms_codes["2020112233"]
    assert len(stored_code) == 6
    assert stored_code.isdigit()


def test_verify_sms_code_correct(environment: Environment):
    # Send code first
    environment.tools.send_sms_verification("2020112233")
    correct_code = environment.tools._sms_codes["2020112233"]

    call = ToolCall(
        id="sms-2",
        name="verify_sms_code",
        arguments={"user_id": "2020112233", "code": correct_code},
    )
    response = environment.get_response(call)
    assert not response.error
    assert json.loads(response.content) == "True"


def test_verify_sms_code_incorrect(environment: Environment):
    # Send code first so a valid code exists
    environment.tools.send_sms_verification("2020112233")

    call = ToolCall(
        id="sms-3",
        name="verify_sms_code",
        arguments={"user_id": "2020112233", "code": "000000"},
    )
    response = environment.get_response(call)
    assert not response.error
    # "000000" is almost certainly not the randomly generated code
    assert json.loads(response.content) == "False"


def test_verify_sms_code_no_prior_send(environment: Environment):
    # No SMS was sent for this user — must return False, not error
    call = ToolCall(
        id="sms-4",
        name="verify_sms_code",
        arguments={"user_id": "9999999999", "code": "123456"},
    )
    response = environment.get_response(call)
    assert not response.error
    assert json.loads(response.content) == "False"


def test_receive_sms_code(environment: Environment):
    from tau2.domains.ConvalidacionCLCs_Coronado.user_tools import (
        ConvalidacionCLCUserTools,
    )

    # Before any SMS is sent, user tools should return an informative message
    user_tools = ConvalidacionCLCUserTools(environment.tools._sms_codes)
    result_before = user_tools.receive_sms_code()
    assert "No hay codigo" in result_before

    # Agent sends SMS — shared dict reference means user_tools sees the code immediately
    environment.tools.send_sms_verification("2020112233")
    stored_code = environment.tools._sms_codes["2020112233"]

    result_after = user_tools.receive_sms_code()
    assert result_after == stored_code
    assert len(result_after) == 6
    assert result_after.isdigit()


# ---------------------------------------------------------------------------
# E4: tests de integración RAG (no requieren API key — usan _fake_embed)
# ---------------------------------------------------------------------------

SAMPLE_POLICY = """
## Devoluciones
Puedes devolver cualquier artículo en 30 días con recibo.

## Cancelaciones
Puedes cancelar dentro de las 24 horas sin cargo.
"""


def _fake_embed(texts):
    import math
    import random

    def make_vec(text, dim=8):
        rng = random.Random(hash(text) & 0xFFFFFFFF)
        v = [rng.gauss(0, 1) for _ in range(dim)]
        n = math.sqrt(sum(x * x for x in v)) or 1.0
        return [x / n for x in v]

    return [make_vec(t) for t in texts]


def test_retrieve_policy_returns_text():
    index = ChromaPolicyIndex(SAMPLE_POLICY, strategy="headers", _embed_fn=_fake_embed)
    kit = ConvalidacionCLCTools(db=None, policy_index=index)
    result = kit.retrieve_policy(query="¿puedo convalidar una actividad externa?")
    assert isinstance(result, str) and len(result) > 0


def test_toolkit_has_think_tool():
    kit = ConvalidacionCLCTools(db=None)
    assert "think" in kit.tools
