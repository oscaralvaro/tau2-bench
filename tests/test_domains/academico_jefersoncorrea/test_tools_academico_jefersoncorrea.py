import math
import random

import pytest
from tau2.domains.academico_jefersoncorrea.data_model import AcademicDB, Student, Course, Enrollment
from tau2.domains.academico_jefersoncorrea.environment import get_environment
from tau2.domains.academico_jefersoncorrea.tools import AcademicTools
from tau2.domains.academico_jefersoncorrea.user_tools import AcademicUserTools
from tau2.environment.rag import ChromaPolicyIndex

@pytest.fixture
def tools():
    """Fixture que crea una base de datos en memoria limpia antes de cada test."""
    db = AcademicDB(
        students={
            "u2024001": Student(
                student_id="u2024001",
                name="Carlos Mendoza",
                approved_credits=10,
                approved_courses=[],
                phone_number="912345678",
            ),
        },
        courses={
            "MAT101": Course(course_id="MAT101", name="Mate I", credits=4, prerequisites=[], schedule="Lunes", available_seats=2),
            "IND305": Course(course_id="IND305", name="Gestión", credits=4, prerequisites=[], schedule="Jueves", available_seats=0), # Sin vacantes
            "HUM101": Course(course_id="HUM101", name="Ética", credits=2, prerequisites=[], schedule="Viernes", available_seats=5)
        },
        enrollments={
            "ENROLL-TEST": Enrollment(enrollment_id="ENROLL-TEST", student_id="u2024001", course_id="HUM101", status="active")
        }
    )
    return AcademicTools(db)

# ==========================================
# 1. Tests para get_student_details
# ==========================================
def test_get_student_details_success(tools):
    """Éxito: Obtiene detalles de un estudiante existente."""
    result = tools.get_student_details("u2024001")
    assert result["student_info"]["name"] == "Carlos Mendoza"
    assert len(result["active_enrollments"]) == 1

def test_get_student_details_error_not_found(tools):
    """Error: El estudiante no existe."""
    with pytest.raises(ValueError, match="no encontrado"):
        tools.get_student_details("u9999999")

# ==========================================
# 2. Tests para search_courses
# ==========================================
def test_search_courses_success(tools):
    """Éxito: Busca cursos por nombre o ID."""
    results = tools.search_courses("Mate")
    assert len(results) == 1
    assert results[0].course_id == "MAT101"
    
    all_results = tools.search_courses("")
    assert len(all_results) == 3


def test_search_courses_exposes_end_date():
    """El catalogo real debe exponer la fecha de fin usada por tareas con plazo."""
    environment = get_environment()
    courses = environment.tools.search_courses("SIS201")

    assert courses[0].end_date == "2026-05-15"


def test_real_db_uses_one_enrollment_per_course():
    """Las matriculas activas no deben compactar varios cursos en un course_id."""
    environment = get_environment()
    details = environment.tools.get_student_details("u2024002")
    active_course_ids = {
        enrollment["course_id"] for enrollment in details["active_enrollments"]
    }

    assert {"IND301", "SIS201", "MAT101"}.issubset(active_course_ids)
    assert all("," not in course_id for course_id in active_course_ids)

# ==========================================
# 3. Tests para create_enrollment
# ==========================================
def test_create_enrollment_success(tools):
    """Éxito: Crea una matrícula y descuenta la vacante."""
    initial_seats = tools.db.courses["MAT101"].available_seats
    new_enrollment = tools.create_enrollment("u2024001", "MAT101")
    
    assert new_enrollment.status == "active"
    assert tools.db.courses["MAT101"].available_seats == initial_seats - 1

def test_create_enrollment_error_no_seats(tools):
    """Error: El curso no tiene vacantes."""
    with pytest.raises(ValueError, match="no tiene vacantes"):
        tools.create_enrollment("u2024001", "IND305")

def test_create_enrollment_error_duplicate(tools):
    """Error: El estudiante ya está matriculado en ese curso."""
    with pytest.raises(ValueError, match="ya está en"):
        tools.create_enrollment("u2024001", "HUM101") # Ya está matriculado en el fixture

def test_create_enrollment_error_invalid_course(tools):
    """Error: El curso no existe en el catálogo."""
    with pytest.raises(ValueError, match="no encontrado"):
        tools.create_enrollment("u2024001", "CURSO_INVENTADO")

# ==========================================
# 4. Tests para update_enrollment_swap
# ==========================================
def test_update_enrollment_swap_success(tools):
    """Éxito: Cambia un curso por otro y ajusta ambas vacantes."""
    initial_hum_seats = tools.db.courses["HUM101"].available_seats
    initial_mat_seats = tools.db.courses["MAT101"].available_seats
    
    result = tools.update_enrollment_swap("u2024001", "HUM101", "MAT101")
    
    assert result["status"] == "success"
    assert tools.db.courses["HUM101"].available_seats == initial_hum_seats + 1 # Liberó
    assert tools.db.courses["MAT101"].available_seats == initial_mat_seats - 1 # Ocupó

def test_update_enrollment_swap_error_not_enrolled(tools):
    """Error: Intenta cambiar un curso en el que no está matriculado."""
    with pytest.raises(ValueError, match="No hay matrícula activa"):
        # Se invierten los cursos: intenta salir de IND305 (no matriculado) para ir a MAT101 (sí hay vacantes)
        tools.update_enrollment_swap("u2024001", "IND305", "MAT101")
        
# ==========================================
# 5. Tests para cancel_enrollment
# ==========================================
def test_cancel_enrollment_success(tools):
    """Éxito: Cancela una matrícula activa y libera la vacante."""
    initial_seats = tools.db.courses["HUM101"].available_seats
    canceled = tools.cancel_enrollment("u2024001", "HUM101")
    
    assert canceled.status == "dropped"
    assert tools.db.courses["HUM101"].available_seats == initial_seats + 1

def test_cancel_enrollment_error_not_found(tools):
    """Error: Intenta cancelar un curso que no está llevando."""
    with pytest.raises(ValueError, match="No hay matrícula activa"):
        tools.cancel_enrollment("u2024001", "MAT101")


def test_academic_environment_exposes_user_sms_tools():
    environment = get_environment()

    user_tool_names = {tool.name for tool in environment.get_user_tools()}

    assert "check_verification_sms" in user_tool_names


def test_user_tools_can_read_agent_sms_code(tools):
    user_tools = AcademicUserTools(tools.db)

    tools.send_verification_sms("u2024001")
    message = user_tools.check_verification_sms("u2024001")
    code = tools.db.students["u2024001"].current_sms_code

    assert code is not None
    assert code in message
    verification_result = tools.verify_sms_code("u2024001", code)
    assert "exitosa" in verification_result
    assert "proceder" in verification_result


def test_sms_verification_rejects_wrong_role(tools):
    tools.send_verification_sms("u2024001")
    code = tools.db.students["u2024001"].current_sms_code

    verification_result = tools.verify_sms_code(
        "u2024001",
        code,
        required_role="employee",
    )

    assert "Autorizaci" in verification_result
    assert tools.db.students["u2024001"].current_sms_code == code

def _fake_embed(texts):
    def make_vec(text, dim=8):
        rng = random.Random(hash(text) & 0xFFFFFFFF)
        vec = [rng.gauss(0, 1) for _ in range(dim)]
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [x / norm for x in vec]

    return [make_vec(text) for text in texts]


SAMPLE_POLICY = """
## Matriculas
Antes de matricular un curso, valida prerrequisitos, vacantes y cruce de horario.

## Retiros
Antes de retirar un curso activo, verifica identidad y clave dinamica.
"""


def test_retrieve_policy_returns_text():
    index = ChromaPolicyIndex(SAMPLE_POLICY, strategy="headers", _embed_fn=_fake_embed)
    kit = AcademicTools(db=None, policy_index=index)

    result = kit.retrieve_policy(query="puedo matricular un curso con cruce de horario")

    assert isinstance(result, str)
    assert len(result) > 0


def test_toolkit_has_think_tool():
    kit = AcademicTools(db=None)

    assert "think" in kit.tools
