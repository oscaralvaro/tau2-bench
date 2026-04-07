import pytest
from tau2.domains.healthcare_enrique.data_model import HealthcareDB
from tau2.domains.healthcare_enrique.tools import HealthcareToolkit


@pytest.fixture
def toolkit():
    db = HealthcareDB(
        pacientes={
            "111": {
                "rut": "111",
                "prevision": "FONASA",
                "inscrito": True
            },
            "222": {
                "rut": "222",
                "prevision": "ISAPRE",
                "inscrito": True
            }
        },
        interconsultas={
            "ic1": {
                "id": "ic1",
                "rut_paciente": "111",
                "estado": "validada"
            }
        },
        registros_clinicos={},
        bloques_agenda={}
    )
    return HealthcareToolkit(db)


# -------------------------
# TESTS
# -------------------------

def test_get_paciente(toolkit):
    paciente = toolkit.get_paciente("111")
    assert paciente is not None


def test_validar_prevision_ok(toolkit):
    assert toolkit.validar_prevision("111") is True


def test_validar_prevision_fail(toolkit):
    assert toolkit.validar_prevision("222") is False


def test_validar_inscripcion(toolkit):
    assert toolkit.validar_inscripcion("111") is True


def test_validar_interconsulta(toolkit):
    assert toolkit.validar_interconsulta("111") is True


def test_agendar_bloque(toolkit):
    bloque = toolkit.agendar_bloque("b1", "Control", ["p1"])
    assert bloque is not None


def test_cancelar_bloque(toolkit):
    toolkit.agendar_bloque("b2", "Control", ["p1"])
    bloque = toolkit.cancelar_bloque("b2")
    assert bloque.estado_cupo == "disponible"


# -------------------------
# CASOS ERROR
# -------------------------

def test_paciente_no_existe(toolkit):
    paciente = toolkit.get_paciente("999")
    assert paciente is None