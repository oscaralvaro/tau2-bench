import pytest
from tau2.data_model.message import ToolCall
from tau2.domains.enosa_masias.data_model import EnosaDB, EnosaInfo, User, Supply
from tau2.domains.enosa_masias.environment import get_environment

@pytest.fixture
def enosa_db():
    return EnosaDB(
        enosa_info=EnosaInfo(company_name="ENOSA", city="Piura", emergency_phone="073-284040", office_hours="08:00-17:00"),
        users={"11111111": User(user_id="11111111", full_name="Juan Perez")},
        supplies={"SUP-01": Supply(supply_id="SUP-01", supply_number="S-101", owner_id="11111111", address="Av. Grau", status="active", debt_amount=0.0)},
        tickets={}
    )

def test_get_supply_details(enosa_db):
    env = get_environment(enosa_db)
    response = env.use_tool("get_supply_details", supply_number="S-101")
    assert response["supply_number"] == "S-101"
    assert response["status"] == "active"

def test_create_ticket(enosa_db):
    env = get_environment(enosa_db)
    # Usamos ToolCall para simular el comportamiento del agente
    response = env.get_response(ToolCall(
        id="call_1",
        name="create_ticket",
        arguments={"reporter_id": "11111111", "issue_type": "power_outage", "description": "No hay luz"}
    ))
    assert not response.error
    assert env.tools.db.tickets["T-001"].issue_type == "power_outage"
    
def test_retrieve_policy_returns_text():
    from tau2.environment.rag import ChromaPolicyIndex
    from tau2.domains.enosa_masias.tools import EnosaToolKit
    
    # Texto de prueba que simula la politica
    SAMPLE_POLICY = "## Reclamos\nTodo reclamo debe registrarse con DNI.\n## Pagos\nLos pagos son en linea."
    
    # Funcion mock para no consumir API real en el test
    def _fake_embed(texts):
        import math, random
        def make_vec(text, dim=8):
            rng = random.Random(hash(text) & 0xFFFFFFFF)
            v = [rng.gauss(0, 1) for _ in range(dim)]
            n = math.sqrt(sum(x*x for x in v)) or 1.0
            return [x/n for x in v]
        return [make_vec(t) for t in texts]
    
    # Instanciamos el indexador con headers y le pasamos la funcion mock
    index = ChromaPolicyIndex(SAMPLE_POLICY, strategy="headers", _embed_fn=_fake_embed)
    
    # Instanciamos el toolkit y pasamos la consulta
    kit = EnosaToolKit(db=None, policy_index=index)
    result = kit.retrieve_policy(query="reclamos")
    
    # Validamos que devuelva texto y no este vacio
    assert isinstance(result, str)
    assert len(result) > 0


def test_toolkit_has_think_tool():
    from tau2.domains.enosa_masias.tools import EnosaToolKit
    
    # Instanciamos el toolkit
    kit = EnosaToolKit(db=None)
    
    # Comprobamos que 'think' exista dentro de las herramientas disponibles
    assert "think" in kit.tools