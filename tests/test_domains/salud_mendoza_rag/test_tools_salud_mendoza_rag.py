from tau2.domains.salud_mendoza_rag.environment import get_environment, get_tasks


def test_rag_environment_loading():
    """Prueba que el entorno del RAG cargue sin errores."""
    env = get_environment()
    assert env is not None
    assert env.tools is not None
    assert env.tools.db is not None


def test_rag_tools_existence():
    """Prueba que las herramientas esten registradas."""
    env = get_environment()
    tool_names = set(env.tools.get_tools().keys())
    assert "buscar_protocolo_rag" in tool_names
    assert "validar_interconsulta" in tool_names
    assert "adjuntar_examen_a_solicitud" in tool_names


def test_rag_task_loading():
    """Prueba que las tasks del dominio carguen y el split base sea valido."""
    tasks = get_tasks("base")
    assert len(tasks) == 10
    assert tasks[0].id == "0"
