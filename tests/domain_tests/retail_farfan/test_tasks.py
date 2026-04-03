from tau2.domains.retail_farfan.environment import get_tasks


def test_load_all_tasks():
    tasks = get_tasks("base")
    assert len(tasks) == 20, f"Se esperaban 20 tareas, pero se cargaron {len(tasks)}"
