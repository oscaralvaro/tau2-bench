from datetime import date, timedelta

import pytest
from tau2.data_model.message import ToolCall
from tau2.domains.ecommerce_calle.data_model import (
    EcommerceDB, User, Product, Order, Shipment,
    CustomerType, AccountStatus, OrderStatus, SMSCode,
)
from tau2.domains.ecommerce_calle.environment import get_environment
from tau2.domains.ecommerce_calle.tools import EcommerceToolKit
from tau2.environment.environment import Environment
from tau2.environment.rag import ChromaPolicyIndex


# ---------------------------------------------------------------------------
# Fixture principal: base de datos de prueba
# ---------------------------------------------------------------------------

@pytest.fixture
def test_db() -> EcommerceDB:
    """
    Base de datos en memoria para los tests.
    Fechas relativas para que los plazos de devolucion no dependan del calendario.
    """
    today = date.today()
    ten_days_ago = (today - timedelta(days=10)).isoformat()
    twenty_days_ago = (today - timedelta(days=20)).isoformat()
    forty_days_ago = (today - timedelta(days=40)).isoformat()

    return EcommerceDB(
        users={
            "U001": User(
                user_id="U001", name="Ana Garcia", email="ana@mail.com",
                phone="987654321", address="Av. Lima 123",
                customer_type="regular", status="active",
            ),
            "U002": User(
                user_id="U002", name="Carlos Ruiz", email="carlos@mail.com",
                phone="987654322", address="Jr. Miraflores 456",
                customer_type="premium", status="active",
            ),
            "U003": User(
                user_id="U003", name="Lucia Torres", email="lucia@mail.com",
                phone="987654323", address="Calle Real 789",
                customer_type="regular", status="active",
            ),
        },
        products={
            "P001": Product(product_id="P001", name="Laptop HP",
                            category="electronica", price=2500.0, return_allowed=True),
            "P002": Product(product_id="P002", name="Auriculares Sony",
                            category="electronica", price=350.0, return_allowed=True),
            "P003": Product(product_id="P003", name="Ropa Interior",
                            category="ropa", price=80.0, return_allowed=False),
        },
        orders={
            # processing → se puede cancelar y cambiar dirección
            "ORD-001": Order(
                order_id="ORD-001", user_id="U001", date=ten_days_ago,
                status="processing", total=2500.0,
                shipping_address="Av. Lima 123", items=["P001"],
            ),
            # delivered dentro de 30 días → devolución válida (P002 permite devol.)
            "ORD-002": Order(
                order_id="ORD-002", user_id="U001", date=ten_days_ago,
                status="delivered", total=350.0,
                shipping_address="Av. Lima 123", items=["P002"],
            ),
            # delivered, P003 NO permite devolución
            "ORD-003": Order(
                order_id="ORD-003", user_id="U002", date=twenty_days_ago,
                status="delivered", total=80.0,
                shipping_address="Jr. Miraflores 456", items=["P003"],
            ),
            # shipped → no se puede cancelar ni cambiar dirección
            "ORD-004": Order(
                order_id="ORD-004", user_id="U003", date=ten_days_ago,
                status="shipped", total=800.0,
                shipping_address="Calle Real 789", items=["P001"],
            ),
            # delivered → reemplazo válido
            "ORD-007": Order(
                order_id="ORD-007", user_id="U002", date=forty_days_ago,
                status="delivered", total=2500.0,
                shipping_address="Jr. Miraflores 456", items=["P001"],
            ),
        },
        shipments={
            "SH-004": Shipment(
                shipment_id="SH-004", order_id="ORD-004",
                tracking_number="TRK99887766", shipment_status="in_transit",
                estimated_delivery="2026-05-22",
            ),
        },
        returns={},
        sms_codes={},   # requerido por las herramientas SMS
    )


@pytest.fixture
def environment(test_db: EcommerceDB) -> Environment:
    return get_environment(test_db)


# ---------------------------------------------------------------------------
# Tests: get_user_details
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Tests: get_order_details
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Tests: search_orders_by_user
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Tests: track_shipment
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Tests: cancel_order
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Tests: update_shipping_address
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Tests: request_return
# ---------------------------------------------------------------------------

def test_request_return_success(environment: Environment):
    """ORD-002: delivered, dentro de 30 días, P002 permite devolución."""
    response = environment.get_response(
        ToolCall(id="13a", name="request_return",
                 arguments={"order_id": "ORD-002", "reason": "producto defectuoso",
                             "user_id": "U001"})
    )
    assert not response.error
    assert "RET-ORD-002" in environment.tools.db.returns


def test_request_return_not_allowed(environment: Environment):
    """ORD-003: P003 tiene return_allowed=False → rechazo."""
    response = environment.get_response(
        ToolCall(id="13", name="request_return",
                 arguments={"order_id": "ORD-003", "reason": "no me gusto",
                             "user_id": "U002"})
    )
    assert response.error or "error" in str(response.content).lower()


def test_request_return_wrong_user(environment: Environment):
    """U001 intenta devolver ORD-004 que pertenece a U003 → rechazo."""
    response = environment.get_response(
        ToolCall(id="13b", name="request_return",
                 arguments={"order_id": "ORD-004", "reason": "no me gusto",
                             "user_id": "U001"})
    )
    assert response.error or "error" in str(response.content).lower()


# ---------------------------------------------------------------------------
# Tests: request_replacement
# ---------------------------------------------------------------------------

def test_request_replacement_success(environment: Environment):
    response = environment.get_response(
        ToolCall(id="14", name="request_replacement",
                 arguments={"order_id": "ORD-007", "reason": "llego roto"})
    )
    assert not response.error


def test_request_replacement_not_delivered(environment: Environment):
    """ORD-001 está en processing → no se puede pedir reemplazo."""
    response = environment.get_response(
        ToolCall(id="14b", name="request_replacement",
                 arguments={"order_id": "ORD-001", "reason": "llego roto"})
    )
    assert response.error or "error" in str(response.content).lower()


# ---------------------------------------------------------------------------
# Tests: issue_refund
# ---------------------------------------------------------------------------

def test_issue_refund_no_return(environment: Environment):
    """Sin devolución registrada → rechazo."""
    response = environment.get_response(
        ToolCall(id="15", name="issue_refund", arguments={"order_id": "ORD-002"})
    )
    assert response.error or "error" in str(response.content).lower()


# ---------------------------------------------------------------------------
# Tests: escalate_to_human
# ---------------------------------------------------------------------------

def test_escalate_to_human(environment: Environment):
    response = environment.get_response(
        ToolCall(id="16", name="escalate_to_human",
                 arguments={"order_id": "ORD-002", "reason": "cliente molesto"})
    )
    assert not response.error


# ---------------------------------------------------------------------------
# Tests: send_verification_sms  (herramienta nueva)
# ---------------------------------------------------------------------------

def test_send_verification_sms_success(environment: Environment):
    """Enviar SMS a usuario existente genera un código en la DB."""
    response = environment.get_response(
        ToolCall(id="17", name="send_verification_sms", arguments={"user_id": "U001"})
    )
    assert not response.error
    # El código debe haberse guardado en la DB
    assert "U001" in environment.tools.db.sms_codes
    sms = environment.tools.db.sms_codes["U001"]
    assert len(sms.code) == 4
    assert sms.code.isdigit()
    assert sms.used is False


def test_send_verification_sms_user_not_found(environment: Environment):
    """Enviar SMS a usuario inexistente → error."""
    response = environment.get_response(
        ToolCall(id="18", name="send_verification_sms", arguments={"user_id": "U999"})
    )
    assert response.error or "error" in str(response.content).lower()


# ---------------------------------------------------------------------------
# Tests: verify_sms_code  (herramienta nueva)
# ---------------------------------------------------------------------------

def test_verify_sms_code_success(environment: Environment):
    """Flujo correcto: enviar SMS → verificar con código correcto."""
    # Paso 1: enviar SMS (guarda el código en DB)
    environment.get_response(
        ToolCall(id="19a", name="send_verification_sms", arguments={"user_id": "U001"})
    )
    # Paso 2: obtener el código real desde la DB (simula lo que el usuario recibiría)
    real_code = environment.tools.db.sms_codes["U001"].code

    # Paso 3: verificar con el código correcto
    response = environment.get_response(
        ToolCall(id="19b", name="verify_sms_code",
                 arguments={"user_id": "U001", "code": real_code})
    )
    assert not response.error
    # El código debe marcarse como usado
    assert environment.tools.db.sms_codes["U001"].used is True


def test_verify_sms_code_wrong_code(environment: Environment):
    """Código incorrecto → error, la operación no debe continuar."""
    environment.get_response(
        ToolCall(id="20a", name="send_verification_sms", arguments={"user_id": "U001"})
    )
    response = environment.get_response(
        ToolCall(id="20b", name="verify_sms_code",
                 arguments={"user_id": "U001", "code": "0000"})
    )
    assert response.error or "error" in str(response.content).lower()
    # El código NO debe marcarse como usado
    assert environment.tools.db.sms_codes["U001"].used is False


def test_verify_sms_code_no_active_code(environment: Environment):
    """Verificar sin haber enviado SMS primero → error."""
    response = environment.get_response(
        ToolCall(id="21", name="verify_sms_code",
                 arguments={"user_id": "U001", "code": "1234"})
    )
    assert response.error or "error" in str(response.content).lower()


def test_verify_sms_code_already_used(environment: Environment):
    """Reutilizar un código ya verificado → error (previene replay attacks)."""
    # Enviar y verificar correctamente la primera vez
    environment.get_response(
        ToolCall(id="22a", name="send_verification_sms", arguments={"user_id": "U001"})
    )
    real_code = environment.tools.db.sms_codes["U001"].code
    environment.get_response(
        ToolCall(id="22b", name="verify_sms_code",
                 arguments={"user_id": "U001", "code": real_code})
    )
    # Intentar verificar de nuevo con el mismo código
    response = environment.get_response(
        ToolCall(id="22c", name="verify_sms_code",
                 arguments={"user_id": "U001", "code": real_code})
    )
    assert response.error or "error" in str(response.content).lower()


# ---------------------------------------------------------------------------
# Test de integración: flujo SMS completo → cancelación
# ---------------------------------------------------------------------------

def test_full_sms_flow_cancel_order(environment: Environment):
    """
    Flujo en cascada (Dimensión 22):
    send_verification_sms → verify_sms_code → cancel_order.
    La cancelación solo debe ocurrir si la verificación fue exitosa.
    """
    # 1. Agente envía SMS
    environment.get_response(
        ToolCall(id="23a", name="send_verification_sms", arguments={"user_id": "U001"})
    )
    real_code = environment.tools.db.sms_codes["U001"].code

    # 2. Usuario proporciona el código correcto; agente verifica
    verify_response = environment.get_response(
        ToolCall(id="23b", name="verify_sms_code",
                 arguments={"user_id": "U001", "code": real_code})
    )
    assert not verify_response.error

    # 3. Solo tras verificación exitosa, el agente cancela el pedido
    cancel_response = environment.get_response(
        ToolCall(id="23c", name="cancel_order", arguments={"order_id": "ORD-001"})
    )
    assert not cancel_response.error
    assert environment.tools.db.orders["ORD-001"].status == OrderStatus.cancelled


def test_retrieve_policy_returns_text():
    index = ChromaPolicyIndex(
        SAMPLE_POLICY,
        strategy="headers",
        _embed_fn=_fake_embed,
    )
    kit = EcommerceToolKit(db=None, policy_index=index)
    result = kit.retrieve_policy(query="puedo cancelar mi pedido?")
    assert isinstance(result, str) and len(result) > 0


def test_toolkit_has_think_tool():
    kit = EcommerceToolKit(db=None)
    assert "think" in kit.tools


def _fake_embed(texts):
    import math
    import random

    def make_vec(text, dim=8):
        rng = random.Random(hash(text) & 0xFFFFFFFF)
        values = [rng.gauss(0, 1) for _ in range(dim)]
        norm = math.sqrt(sum(value * value for value in values)) or 1.0
        return [value / norm for value in values]

    return [make_vec(text) for text in texts]


SAMPLE_POLICY = """
## Devoluciones
Puedes devolver cualquier articulo en 30 dias con recibo.

## Cancelaciones
Puedes cancelar dentro de las 24 horas sin cargo.
"""
