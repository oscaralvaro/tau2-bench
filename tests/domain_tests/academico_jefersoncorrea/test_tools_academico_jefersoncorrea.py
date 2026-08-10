import pytest
from src.tau2.domains.academico_jefersoncorrea.environment import get_environment, get_tasks

def test_environment_initialization():
    """Verifica que el entorno se pueda inicializar correctamente sin errores."""
    env = get_environment()
    assert env is not None, "El entorno no debe ser nulo"

def test_tasks_loading():
    """Verifica que las tareas se carguen correctamente desde los archivos JSON."""
    tasks = get_tasks()
    assert isinstance(tasks, list), "Las tareas deben devolverse en una lista"
    assert len(tasks) >= 10, "Deben existir al menos 10 tareas configuradas"
