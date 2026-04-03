import pytest

from tau2.data_model.message import ToolCall
from tau2.domains.ecommerce_zulemalopez.data_model import EcommerceDB
from tau2.domains.ecommerce_zulemalopez.environment import get_environment
from tau2.domains.ecommerce_zulemalopez.utils import ECOMMERCE_DB_PATH
from tau2.environment.environment import Environment


@pytest.fixture
def ecommerce_db() -> EcommerceDB:
    return EcommerceDB.load(ECOMMERCE_DB_PATH)


@pytest.fixture
def environment(ecommerce_db: EcommerceDB) -> Environment:
    return get_environment(ecommerce_db)


def test_find_user_id_by_email(environment: Environment):
    call = ToolCall(
        id="1",
        name="find_user_id_by_email",
        arguments={"email": "zulema.lopez@example.com"},
    )
    response = environment.get_response(call)
    assert not response.error
    assert response.content == "u100"

    call.arguments["email"] = "notfound@example.com"
    response = environment.get_response(call)
    assert response.error


def test_get_order_details(environment: Environment):
    call = ToolCall(id="2", name="get_order_details", arguments={"order_id": "1001"})
    response = environment.get_response(call)
    assert not response.error

    call.arguments["order_id"] = "9999"
    response = environment.get_response(call)
    assert response.error


def test_list_products(environment: Environment):
    call = ToolCall(id="3", name="list_products", arguments={})
    response = environment.get_response(call)
    assert not response.error


def test_list_available_models(environment: Environment):
    call = ToolCall(id="3b", name="list_available_models", arguments={})
    response = environment.get_response(call)
    assert not response.error
    assert "Nova Street One" in response.content


def test_get_product_sizes(environment: Environment):
    call = ToolCall(id="4", name="get_product_sizes", arguments={"product_id": "p102"})
    response = environment.get_response(call)
    assert not response.error


def test_add_user_preferred_size(environment: Environment):
    call = ToolCall(
        id="4b",
        name="add_user_preferred_size",
        arguments={"user_id": "u100", "size": 42},
    )
    response = environment.get_response(call)
    assert not response.error
    assert 42 in environment.tools.db.users["u100"].preferred_sizes

    call.arguments["size"] = 100
    response = environment.get_response(call)
    assert response.error


def test_add_user_address(environment: Environment):
    call = ToolCall(
        id="4c",
        name="add_user_address",
        arguments={
            "user_id": "u101",
            "address": "Av. Sanchez Cerro 600, Piura",
            "set_default": True,
        },
    )
    response = environment.get_response(call)
    assert not response.error
    assert "Av. Sanchez Cerro 600, Piura" in environment.tools.db.users["u101"].saved_addresses
    assert environment.tools.db.users["u101"].address == "Av. Sanchez Cerro 600, Piura"


def test_create_order(environment: Environment):
    call = ToolCall(
        id="5",
        name="create_order",
        arguments={
            "user_id": "u101",
            "product_id": "p101",
            "size": 41,
            "quantity": 1,
            "address": "Jr. Los Cedros 203, Piura",
        },
    )
    response = environment.get_response(call)
    assert not response.error

    latest_order_id = str(environment.tools.db.next_order_id - 1)
    created_order = environment.tools.db.orders[latest_order_id]
    assert created_order.user_id == "u101"

    call.arguments["size"] = 47
    response = environment.get_response(call)
    assert response.error


def test_cancel_order(environment: Environment):
    call = ToolCall(
        id="6",
        name="cancel_order",
        arguments={"order_id": "1001", "reason": "compra duplicada"},
    )
    response = environment.get_response(call)
    assert not response.error
    assert environment.tools.db.orders["1001"].status == "cancelled"

    call.arguments["order_id"] = "1002"
    response = environment.get_response(call)
    assert response.error


def test_update_order_address(environment: Environment):
    call = ToolCall(
        id="7",
        name="update_order_address",
        arguments={"order_id": "1006", "new_address": "Av. Benavides 990, Lima"},
    )
    response = environment.get_response(call)
    assert not response.error
    assert environment.tools.db.orders["1006"].shipping_address == "Av. Benavides 990, Lima"

    call.arguments["order_id"] = "1008"
    response = environment.get_response(call)
    assert response.error


def test_request_return(environment: Environment):
    call = ToolCall(
        id="8",
        name="request_return",
        arguments={"order_id": "1003", "reason": "talla incorrecta"},
    )
    response = environment.get_response(call)
    assert not response.error
    assert environment.tools.db.orders["1003"].status == "return_requested"

    call.arguments["order_id"] = "1004"
    response = environment.get_response(call)
    assert response.error

    call.arguments["order_id"] = "1007"
    response = environment.get_response(call)
    assert response.error


def test_transfer_to_human_agents(environment: Environment):
    call = ToolCall(
        id="9",
        name="transfer_to_human_agents",
        arguments={"summary": "Cliente solicita ayuda legal"},
    )
    response = environment.get_response(call)
    assert not response.error
    assert response.content == "Transfer successful"
