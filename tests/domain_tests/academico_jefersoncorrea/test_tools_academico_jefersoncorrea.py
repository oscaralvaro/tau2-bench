import pytest
from src.tau2.domains.academico_jefersoncorrea.environment import get_environment, get_tasks
from src.tau2.domains.academico_jefersoncorrea.user_tools import AcademicUserTools

def test_environment_initialization():
    """Verifica que el entorno se pueda inicializar correctamente sin errores."""
    env = get_environment()
    assert env is not None, "El entorno no debe ser nulo"

def test_tasks_loading():
    """Verifica que las tareas se carguen correctamente desde los archivos JSON."""
    tasks = get_tasks()
    assert isinstance(tasks, list), "Las tareas deben devolverse en una lista"
    assert len(tasks) >= 10, "Deben existir al menos 10 tareas configuradas"


def test_environment_exposes_sms_user_tool():
    """Verifica que el usuario simulado pueda consultar la clave dinamica."""
    env = get_environment()
    user_tool_names = {tool.name for tool in env.get_user_tools()}

    assert "check_verification_sms" in user_tool_names


def test_user_sms_tool_reads_generated_code():
    """Verifica el flujo send_verification_sms -> check_verification_sms."""
    env = get_environment()
    user_tools = AcademicUserTools(env.tools.db)

    env.tools.send_verification_sms("u2024002")
    message = user_tools.check_verification_sms("u2024002")
    code = env.tools.db.students["u2024002"].current_sms_code

    assert code is not None
    assert code in message


def test_sms_verification_validates_required_role():
    """Verifica que verify_sms_code rechace roles no autorizados."""
    env = get_environment()

    env.tools.send_verification_sms("u2024002")
    code = env.tools.db.students["u2024002"].current_sms_code
    result = env.tools.verify_sms_code(
        "u2024002",
        code,
        required_role="employee",
    )

    assert "Autorizaci" in result
    assert env.tools.db.students["u2024002"].current_sms_code == code
