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
from tau2.environment.environment import Environment


@pytest.fixture
def convalidacion_db() -> ConvalidacionCLCDB:
    return ConvalidacionCLCDB(
        estudiantes=[
            {
                "carnet": "2020123456",
                "nombre_completo": "SUAREZ PEÑA PABLO",
                "programa": "IME",
                "clcs_validados": [2],
            },
            {
                "carnet": "2020987654",
                "nombre_completo": "RAMIREZ LOPEZ ANA",
                "programa": "IC",
                "clcs_validados": [],
            },
        ],
        congresos_preaprobados={
            "IC": ["CONEIC"],
            "IIS": ["CONEII", "INTERCON"],
            "IME": ["CONEIMERA", "INTERCON"],
        },
        bienales_arquitectura=["BIENAL DE ARQUITECTURA 2025"],
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
    return get_environment(convalidacion_db)


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
            "status": "IN PROCESS",
        },
    )


def test_crear_solicitud(environment: Environment, crear_solicitud_call: ToolCall):
    response = environment.get_response(crear_solicitud_call)
    assert not response.error
    solicitud = json.loads(response.content)
    assert solicitud["carnet"] == "2020123456"
    assert solicitud["status"] == "IN PROCESS"
    assert solicitud["request_id"].startswith("REQ-")

    # Test APPROVED status updates student profile
    crear_solicitud_call.arguments["status"] = "APPROVED"
    crear_solicitud_call.arguments["clc"] = 4
    response = environment.get_response(crear_solicitud_call)
    assert not response.error

    # Verify student has the new CLC
    estudiante = environment.tools.get_estudiante_details("2020123456")
    assert 4 in estudiante.clcs_validados


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
