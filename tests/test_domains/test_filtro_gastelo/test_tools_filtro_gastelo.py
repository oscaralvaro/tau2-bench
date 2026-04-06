import pytest
from tau2.data_model.message import ToolCall
from tau2.domains.filtro_gastelo.data_model import FiltrosDB, Customer, Filter
from tau2.domains.filtro_gastelo.environment import get_environment
from tau2.environment.environment import Environment

@pytest.fixture
def filtro_db() -> FiltrosDB:
    return FiltrosDB(
        customers={
            "C-001": Customer(
                customer_id="C-001", 
                name="Francesco", 
                phone="999888777", 
                past_orders=5
            )
        },
        inventory={
            "JD-101": Filter(
                item_id="JD-101",
                brand="John Deere",
                name="Filtro de Aceite Premium",
                type="Aceite",
                price=120.0,
                stock=5,
                equivalent_id="CAT-202"
            ),
            "CAT-202": Filter(
                item_id="CAT-202",
                brand="Caterpillar",
                name="Filtro Aceite Heavy Duty",
                type="Aceite",
                price=125.0,
                stock=0,
                equivalent_id=None
            )
        },
        provider_orders={}
    )

@pytest.fixture
def environment(filtro_db: FiltrosDB) -> Environment:
    return get_environment(filtro_db)

def test_get_filter_status_success(environment: Environment):
    response = environment.get_response(
        ToolCall(
            id="1",
            name="get_filter_status",
            arguments={"item_id": "JD-101"},
        )
    )
    assert not response.error
    assert "120.0" in response.content
    assert "Entrega Inmediata" in response.content

def test_register_provider_order(environment: Environment):
    response = environment.get_response(
        ToolCall(
            id="2",
            name="register_provider_order",
            arguments={
                "customer_name": "Francesco",
                "customer_phone": "987654321",
                "item_id": "CAT-202",
                "quantity": 1
            },
        )
    )
    assert not response.error
    
    orders = environment.tools.db.provider_orders
    assert len(orders) > 0
    
    order = list(orders.values())[0]
    assert order["customer_name"] == "Francesco"
    assert order["item_id"] == "CAT-202"

def test_reject_car_filters(environment: Environment):
    response = environment.get_response(
        ToolCall(
            id="3",
            name="get_filter_status",
            arguments={"item_id": "CAR-OIL-001"},
        )
    )
    assert "No aceptamos pedidos de filtros de autos" in response.content