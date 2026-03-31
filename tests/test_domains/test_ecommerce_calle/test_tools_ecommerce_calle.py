import pytest
from tau2.data_model.message import ToolCall
from tau2.domains.ecommerce_calle.data_model import EcommerceDB, User, Product, Order, Shipment, CustomerType, AccountStatus, OrderStatus
from tau2.domains.ecommerce_calle.environment import get_environment
from tau2.environment.environment import Environment


@pytest.fixture
def test_db() -> EcommerceDB:
    return EcommerceDB(
        users={
            "U001": User(user_id="U001", name="Ana Garcia", email="ana@mail.com",
                         address="Av. Lima 123", customer_type="regular", status="active"),
            "U002": User(user_id="U002", name="Carlos Ruiz", email="carlos@mail.com",
                         address="Jr. Miraflores 456", customer_type="premium", status="active"),
            "U003": User(user_id="U003", name="Lucia Torres", email="lucia@mail.com",
                         address="Calle Real 789", customer_type="regular", status="active"),
        },
        products={
            "P001": Product(product_id="P001", name="Laptop HP", category="electronica",
                            price=2500.0, return_allowed=True),
            "P002": Product(product_id="P002", name="Auriculares Sony", category="electronica",
                            price=350.0, return_allowed=True),
            "P003": Product(product_id="P003", name="Ropa Interior", category="ropa",
                            price=80.0, return_allowed=False),
        },
        orders={
            "ORD-001": Order(order_id="ORD-001", user_id="U001", date="2025-03-20",
                             status="processing", total=2500.0,
                             shipping_address="Av. Lima 123", items=["P001"]),
            "ORD-002": Order(order_id="ORD-002", user_id="U001", date="2025-02-10",
                             status="delivered", total=350.0,
                             shipping_address="Av. Lima 123", items=["P002"]),
            "ORD-003": Order(order_id="ORD-003", user_id="U002", date="2025-01-05",
                             status="delivered", total=80.0,
                             shipping_address="Jr. Miraflores 456", items=["P003"]),
            "ORD-004": Order(order_id="ORD-004", user_id="U003", date="2025-03-25",
                             status="shipped", total=800.0,
                             shipping_address="Calle Real 789", items=["P001"]),
            "ORD-007": Order(order_id="ORD-007", user_id="U002", date="2025-03-01",
                             status="delivered", total=2500.0,
                             shipping_address="Jr. Miraflores 456", items=["P001"]),
        },
        shipments={
            "SH-004": Shipment(shipment_id="SH-004", order_id="ORD-004",
                               tracking_number="TRK99887766", shipment_status="in_transit",
                               estimated_delivery="2025-04-01"),
        },
        returns={},
    )


@pytest.fixture
def environment(test_db: EcommerceDB) -> Environment:
    return get_environment(test_db)


def test_get_user_details_found(environment: Environment):
    response = environment.get_response(
        ToolCall(id="1", name="get_user_details", arguments={"user_id": "U001"})
    )
    assert not response.error
    assert environment.tools.db.users["U001"].name == "Ana Garcia"


def test_get_user_details_not_found(environment: Environment):
    response = environment.get_response(
        ToolCall(id="2", name="get_user_details", arguments={"user_id": "U999"})
    )
    assert response.error or "error" in str(response.content).lower()


def test_get_order_details_found(environment: Environment):
    response = environment.get_response(
        ToolCall(id="3", name="get_order_details", arguments={"order_id": "ORD-001"})
    )
    assert not response.error


def test_get_order_details_not_found(environment: Environment):
    response = environment.get_response(
        ToolCall(id="4", name="get_order_details", arguments={"order_id": "ORD-999"})
    )
    assert response.error or "error" in str(response.content).lower()


def test_search_orders_by_user(environment: Environment):
    response = environment.get_response(
        ToolCall(id="5", name="search_orders_by_user", arguments={"user_id": "U001"})
    )
    assert not response.error


def test_search_orders_by_user_not_found(environment: Environment):
    response = environment.get_response(
        ToolCall(id="6", name="search_orders_by_user", arguments={"user_id": "U999"})
    )
    assert response.error or "error" in str(response.content).lower()


def test_track_shipment_found(environment: Environment):
    response = environment.get_response(
        ToolCall(id="7", name="track_shipment", arguments={"order_id": "ORD-004"})
    )
    assert not response.error


def test_track_shipment_not_found(environment: Environment):
    response = environment.get_response(
        ToolCall(id="8", name="track_shipment", arguments={"order_id": "ORD-001"})
    )
    assert response.error or "error" in str(response.content).lower()


def test_cancel_order_success(environment: Environment):
    response = environment.get_response(
        ToolCall(id="9", name="cancel_order", arguments={"order_id": "ORD-001"})
    )
    assert not response.error
    assert environment.tools.db.orders["ORD-001"].status == OrderStatus.cancelled


def test_cancel_order_already_shipped(environment: Environment):
    response = environment.get_response(
        ToolCall(id="10", name="cancel_order", arguments={"order_id": "ORD-004"})
    )
    assert response.error or "error" in str(response.content).lower()


def test_update_shipping_address_success(environment: Environment):
    response = environment.get_response(
        ToolCall(id="11", name="update_shipping_address",
                 arguments={"order_id": "ORD-001", "new_address": "Calle Nueva 123"})
    )
    assert not response.error
    assert environment.tools.db.orders["ORD-001"].shipping_address == "Calle Nueva 123"


def test_update_shipping_address_already_shipped(environment: Environment):
    response = environment.get_response(
        ToolCall(id="12", name="update_shipping_address",
                 arguments={"order_id": "ORD-004", "new_address": "Calle Falla 000"})
    )
    assert response.error or "error" in str(response.content).lower()


def test_request_return_not_allowed(environment: Environment):
    response = environment.get_response(
        ToolCall(id="13", name="request_return",
                 arguments={"order_id": "ORD-003", "reason": "no me gusto", "user_id": "U002"})
    )
    assert response.error or "error" in str(response.content).lower()


def test_request_replacement_success(environment: Environment):
    response = environment.get_response(
        ToolCall(id="14", name="request_replacement",
                 arguments={"order_id": "ORD-007", "reason": "llego roto"})
    )
    assert not response.error


def test_issue_refund_no_return(environment: Environment):
    response = environment.get_response(
        ToolCall(id="15", name="issue_refund", arguments={"order_id": "ORD-002"})
    )
    assert response.error or "error" in str(response.content).lower()


def test_escalate_to_human(environment: Environment):
    response = environment.get_response(
        ToolCall(id="16", name="escalate_to_human",
                 arguments={"order_id": "ORD-002", "reason": "cliente molesto"})
    )
    assert not response.error