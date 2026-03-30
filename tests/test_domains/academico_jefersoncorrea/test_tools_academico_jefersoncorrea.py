import pytest
from tau2.domains.academico_jefersoncorrea.data_model import AcademicDB, Student, Course, Enrollment
from tau2.domains.academico_jefersoncorrea.tools import AcademicTools

@pytest.fixture
def tools():
    """Fixture que crea una base de datos en memoria limpia antes de cada test."""
    db = AcademicDB(
        students={
            "u2024001": Student(student_id="u2024001", name="Carlos Mendoza", approved_credits=10, approved_courses=[]),
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