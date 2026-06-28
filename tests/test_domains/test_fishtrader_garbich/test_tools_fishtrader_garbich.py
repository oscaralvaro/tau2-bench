import pytest

from tau2.data_model.message import ToolCall
from tau2.domains.fishtrader_garbich.data_model import FishTraderDB
from tau2.domains.fishtrader_garbich.environment import get_environment
from tau2.domains.fishtrader_garbich.tools import FishTraderTools
from tau2.environment.environment import Environment
from tau2.environment.rag import ChromaPolicyIndex


def _fake_embed(texts):
    import math
    import random

    def make_vec(text, dim=8):
        rng = random.Random(hash(text) & 0xFFFFFFFF)
        v = [rng.gauss(0, 1) for _ in range(dim)]
        n = math.sqrt(sum(x * x for x in v)) or 1.0
        return [x / n for x in v]

    return [make_vec(t) for t in texts]


SAMPLE_POLICY = """
## Devoluciones
Puedes devolver cualquier artículo en 30 días con recibo.

## Cancelaciones
Puedes cancelar dentro de las 24 horas sin cargo.
"""


@pytest.fixture
def fishtrader_db() -> FishTraderDB:
    return FishTraderDB(
        users={
            "CUST-001": {
                "customer_id": "CUST-001",
                "legal_name": "Pacific Fresh Imports SAC",
                "trade_name": "Pacific Fresh",
                "ruc": "20100000001",
                "address": {
                    "street": "Av. La Marina 1450",
                    "district": "San Miguel",
                    "city": "Lima",
                    "state": "Lima",
                    "country": "Peru",
                    "postal_code": "15087",
                },
                "shipping_address": {
                    "street": "Muelle 5, Zona Industrial",
                    "district": "Callao",
                    "city": "Callao",
                    "state": "Callao",
                    "country": "Peru",
                    "postal_code": "07001",
                },
                "incoterm": "FOB",
                "payment_method": "bank_transfer",
                "payment_terms_days": 30,
                "shipping_lead_time_days": 7,
                "default_currency": "USD",
                "contact_persons": [
                    {
                        "full_name": "Mariana Torres",
                        "role": "Procurement Manager",
                        "email": "mtorres@pacificfresh.pe",
                        "phone": "+51-999-111-001",
                    }
                ],
                "preferred_destination_port": "Callao",
                "credit_limit": 60000.0,
                "status": "active",
                "notes": "Main domestic wholesale account.",
                "order_ids": ["ORD-001", "ORD-002", "ORD-003"],
                "invoice_ids": ["INV-001", "INV-002"],
            },
            "CUST-002": {
                "customer_id": "CUST-002",
                "legal_name": "Inactive Seafood Buyer SAC",
                "trade_name": "Inactive Buyer",
                "ruc": "20100000002",
                "address": {
                    "street": "Av. Grau 210",
                    "district": "Piura",
                    "city": "Piura",
                    "state": "Piura",
                    "country": "Peru",
                    "postal_code": "20001",
                },
                "shipping_address": {
                    "street": "Parque Industrial Mz D-4",
                    "district": "Piura",
                    "city": "Piura",
                    "state": "Piura",
                    "country": "Peru",
                    "postal_code": "20001",
                },
                "incoterm": "EXW",
                "payment_method": "advance_payment",
                "payment_terms_days": 0,
                "shipping_lead_time_days": 4,
                "default_currency": "USD",
                "contact_persons": [],
                "preferred_destination_port": "Paita",
                "credit_limit": 15000.0,
                "status": "inactive",
                "notes": "Inactive account.",
                "order_ids": [],
                "invoice_ids": [],
            },
        },
        suppliers={
            "SUP-001": {
                "supplier_id": "SUP-001",
                "legal_name": "Pesquera del Sur SAC",
                "trade_name": "Pesquera del Sur",
                "tax_id": "10400000001",
                "address": {
                    "street": "Carretera Costera Km 12",
                    "district": "Pisco",
                    "city": "Pisco",
                    "state": "Ica",
                    "country": "Peru",
                    "postal_code": "11601",
                },
                "contact_persons": [],
                "origin_country": "Peru",
                "payment_method": "bank_transfer",
                "lead_time_days": 3,
                "status": "active",
                "notes": "Main supplier.",
            }
        },
        products={
            "PROD-001": {
                "product_id": "PROD-001",
                "name": "Frozen Mahi Mahi Fillet",
                "description": "Frozen fillet export grade.",
                "species": "Mahi Mahi",
                "presentation": "Fillet",
                "unit_of_measure": "kg",
                "price": 8.9,
                "max_negotiable_price": 7.8,
                "currency": "USD",
                "supplier_id": "SUP-001",
                "origin_country": "Peru",
                "status": "active",
            },
            "PROD-002": {
                "product_id": "PROD-002",
                "name": "Frozen Squid Rings",
                "description": "IQF rings.",
                "species": "Squid",
                "presentation": "Rings",
                "unit_of_measure": "kg",
                "price": 6.7,
                "max_negotiable_price": 5.9,
                "currency": "USD",
                "supplier_id": "SUP-001",
                "origin_country": "Peru",
                "status": "active",
            },
            "PROD-003": {
                "product_id": "PROD-003",
                "name": "Tilapia Whole Round",
                "description": "Whole round frozen tilapia.",
                "species": "Tilapia",
                "presentation": "Whole Round",
                "unit_of_measure": "kg",
                "price": 4.8,
                "max_negotiable_price": 4.2,
                "currency": "USD",
                "supplier_id": "SUP-001",
                "origin_country": "Peru",
                "status": "out_of_stock",
            },
        },
        inventory={
            "INVREC-001": {
                "inventory_id": "INVREC-001",
                "product_id": "PROD-001",
                "warehouse_name": "Callao Cold Store A",
                "quantity_available": 1000.0,
                "quantity_reserved": 100.0,
                "unit_of_measure": "kg",
                "last_updated_at": "2026-03-29T09:00:00",
                "status": "available",
            },
            "INVREC-002": {
                "inventory_id": "INVREC-002",
                "product_id": "PROD-002",
                "warehouse_name": "Callao Cold Store A",
                "quantity_available": 800.0,
                "quantity_reserved": 50.0,
                "unit_of_measure": "kg",
                "last_updated_at": "2026-03-29T09:05:00",
                "status": "available",
            },
            "INVREC-003": {
                "inventory_id": "INVREC-003",
                "product_id": "PROD-003",
                "warehouse_name": "Callao Cold Store B",
                "quantity_available": 0.0,
                "quantity_reserved": 0.0,
                "unit_of_measure": "kg",
                "last_updated_at": "2026-03-29T09:10:00",
                "status": "exhausted",
            },
        },
        orders={
            "ORD-001": {
                "order_id": "ORD-001",
                "customer_id": "CUST-001",
                "issue_date": "2026-03-26",
                "delivery_date": "2026-04-02",
                "incoterm": "FOB",
                "payment_method": "bank_transfer",
                "currency": "USD",
                "shipping_address": {
                    "street": "Muelle 5, Zona Industrial",
                    "district": "Callao",
                    "city": "Callao",
                    "state": "Callao",
                    "country": "Peru",
                    "postal_code": "07001",
                },
                "items": [
                    {
                        "line_id": "LINE-001",
                        "product_id": "PROD-001",
                        "product_name": "Frozen Mahi Mahi Fillet",
                        "quantity": 100.0,
                        "unit_of_measure": "kg",
                        "unit_price": 8.2,
                        "subtotal": 820.0,
                        "supplier_id": "SUP-001",
                    }
                ],
                "total_amount": 820.0,
                "status": "confirmed",
                "notes": "Modifiable order.",
                "invoice_ids": [],
                "shipment_ids": [],
            },
            "ORD-002": {
                "order_id": "ORD-002",
                "customer_id": "CUST-001",
                "issue_date": "2026-03-20",
                "delivery_date": "2026-04-10",
                "incoterm": "FOB",
                "payment_method": "bank_transfer",
                "currency": "USD",
                "shipping_address": {
                    "street": "Muelle 5, Zona Industrial",
                    "district": "Callao",
                    "city": "Callao",
                    "state": "Callao",
                    "country": "Peru",
                    "postal_code": "07001",
                },
                "items": [
                    {
                        "line_id": "LINE-002",
                        "product_id": "PROD-002",
                        "product_name": "Frozen Squid Rings",
                        "quantity": 120.0,
                        "unit_of_measure": "kg",
                        "unit_price": 6.3,
                        "subtotal": 756.0,
                        "supplier_id": "SUP-001",
                    }
                ],
                "total_amount": 756.0,
                "status": "shipped",
                "notes": "Already shipped.",
                "invoice_ids": ["INV-001"],
                "shipment_ids": ["SHIP-001"],
            },
            "ORD-003": {
                "order_id": "ORD-003",
                "customer_id": "CUST-001",
                "issue_date": "2026-03-27",
                "delivery_date": "2026-04-04",
                "incoterm": "FOB",
                "payment_method": "bank_transfer",
                "currency": "USD",
                "shipping_address": {
                    "street": "Muelle 5, Zona Industrial",
                    "district": "Callao",
                    "city": "Callao",
                    "state": "Callao",
                    "country": "Peru",
                    "postal_code": "07001",
                },
                "items": [
                    {
                        "line_id": "LINE-003",
                        "product_id": "PROD-001",
                        "product_name": "Frozen Mahi Mahi Fillet",
                        "quantity": 90.0,
                        "unit_of_measure": "kg",
                        "unit_price": 8.1,
                        "subtotal": 729.0,
                        "supplier_id": "SUP-001",
                    }
                ],
                "total_amount": 729.0,
                "status": "confirmed",
                "notes": "Order already invoiced.",
                "invoice_ids": ["INV-002"],
                "shipment_ids": [],
            },
        },
        invoices={
            "INV-001": {
                "invoice_id": "INV-001",
                "invoice_number": "F001-000001",
                "order_id": "ORD-002",
                "customer_id": "CUST-001",
                "customer_legal_name": "Pacific Fresh Imports SAC",
                "customer_ruc": "20100000001",
                "billing_address": {
                    "street": "Av. La Marina 1450",
                    "district": "San Miguel",
                    "city": "Lima",
                    "state": "Lima",
                    "country": "Peru",
                    "postal_code": "15087",
                },
                "issue_date": "2026-03-20",
                "due_date": "2026-04-19",
                "currency": "USD",
                "payment_method": "bank_transfer",
                "payment_terms_days": 30,
                "line_items": [
                    {
                        "line_id": "INVLINE-001",
                        "product_id": "PROD-002",
                        "description": "Frozen Squid Rings",
                        "quantity": 120.0,
                        "unit_of_measure": "kg",
                        "unit_price": 6.3,
                        "subtotal": 756.0,
                    }
                ],
                "subtotal": 756.0,
                "tax_amount": 136.08,
                "total_amount": 892.08,
                "paid_amount": 300.0,
                "status": "partially_paid",
                "issued_at": "2026-03-20T12:00:00",
                "paid_at": None,
                "payment_records": [
                    {
                        "payment_id": "PAY-001",
                        "invoice_id": "INV-001",
                        "amount": 300.0,
                        "payment_method": "bank_transfer",
                        "payment_date": "2026-03-21T10:00:00",
                        "reference": "TRX-001",
                    }
                ],
            },
            "INV-002": {
                "invoice_id": "INV-002",
                "invoice_number": "F001-000002",
                "order_id": "ORD-003",
                "customer_id": "CUST-001",
                "customer_legal_name": "Pacific Fresh Imports SAC",
                "customer_ruc": "20100000001",
                "billing_address": {
                    "street": "Av. La Marina 1450",
                    "district": "San Miguel",
                    "city": "Lima",
                    "state": "Lima",
                    "country": "Peru",
                    "postal_code": "15087",
                },
                "issue_date": "2026-03-27",
                "due_date": "2026-04-26",
                "currency": "USD",
                "payment_method": "bank_transfer",
                "payment_terms_days": 30,
                "line_items": [
                    {
                        "line_id": "INVLINE-002",
                        "product_id": "PROD-001",
                        "description": "Frozen Mahi Mahi Fillet",
                        "quantity": 90.0,
                        "unit_of_measure": "kg",
                        "unit_price": 8.1,
                        "subtotal": 729.0,
                    }
                ],
                "subtotal": 729.0,
                "tax_amount": 131.22,
                "total_amount": 860.22,
                "paid_amount": 0.0,
                "status": "issued",
                "issued_at": "2026-03-27T12:00:00",
                "paid_at": None,
                "payment_records": [],
            },
        },
        claims={},
        shipments={
            "SHIP-001": {
                "shipment_id": "SHIP-001",
                "order_id": "ORD-002",
                "customer_id": "CUST-001",
                "carrier_name": "Pacific Lines",
                "container_number": "PCLU5544332",
                "tracking_number": "TRK-ORD002",
                "departure_port": "Callao",
                "arrival_port": "Port of Miami",
                "estimated_departure_date": "2026-03-25",
                "estimated_arrival_date": "2026-04-08",
                "actual_departure_date": "2026-03-25",
                "actual_arrival_date": None,
                "incoterm": "FOB",
                "status": "in_transit",
                "notes": "Shipment in transit.",
            }
        },
    )


def test_make_payment_is_deterministic_for_evaluation_replay(
    fishtrader_db: FishTraderDB,
) -> None:
    env_one = get_environment(db=fishtrader_db.model_copy(deep=True), use_rag=False)
    env_two = get_environment(db=fishtrader_db.model_copy(deep=True), use_rag=False)
    tool_call = ToolCall(
        id="call_payment",
        name="make_payment",
        arguments={
            "invoice_id": "INV-002",
            "amount": 1937.56,
            "payment_method": "bank_transfer",
            "reference": "ORD-002 Cancellation Request",
        },
    )

    response_one = env_one.get_response(tool_call)
    response_two = env_two.get_response(tool_call)

    assert response_one.content == response_two.content


@pytest.fixture
def environment(fishtrader_db: FishTraderDB) -> Environment:
    return get_environment(fishtrader_db, use_rag=False)


def test_register_customer(environment: Environment):
    customer = environment.tools.register_customer(
        legal_name="Maritech Frozen Foods SAC",
        ruc="20100000006",
        address={
            "street": "Av. Industrial 410",
            "district": "Callao",
            "city": "Callao",
            "state": "Callao",
            "country": "Peru",
            "postal_code": "07001",
        },
        incoterm="FOB",
        payment_method="bank_transfer",
        payment_terms_days=30,
        shipping_lead_time_days=6,
        default_currency="USD",
    )
    assert customer.customer_id == "CUST-003"
    assert customer.ruc == "20100000006"

    with pytest.raises(ValueError):
        environment.tools.register_customer(
            legal_name="Duplicate RUC SAC",
            ruc="20100000001",
            address={
                "street": "X",
                "district": "Y",
                "city": "Lima",
                "state": "Lima",
                "country": "Peru",
                "postal_code": "15001",
            },
            incoterm="FOB",
            payment_method="bank_transfer",
            payment_terms_days=30,
            shipping_lead_time_days=6,
            default_currency="USD",
        )


def test_show_catalog(environment: Environment):
    catalog = environment.tools.show_catalog()
    product_ids = {product.product_id for product in catalog}
    assert "PROD-001" in product_ids
    assert "PROD-002" in product_ids
    assert "PROD-003" not in product_ids


def test_get_customer_details(environment: Environment):
    customer = environment.tools.get_customer_details("CUST-001")
    assert customer.legal_name == "Pacific Fresh Imports SAC"

    with pytest.raises(ValueError):
        environment.tools.get_customer_details("MISSING")


def test_get_invoice_details(environment: Environment):
    invoice = environment.tools.get_invoice_details("INV-001")
    assert invoice.total_amount == 892.08

    with pytest.raises(ValueError):
        environment.tools.get_invoice_details("MISSING")


def test_check_stock(environment: Environment):
    stock_info = environment.tools.check_stock("PROD-001")
    assert stock_info["total_available"] == 1000.0
    assert stock_info["total_reserved"] == 100.0

    with pytest.raises(ValueError):
        environment.tools.check_stock("UNKNOWN")


def test_register_order(environment: Environment):
    order = environment.tools.register_order(
        customer_id="CUST-001",
        items=[
            {
                "line_id": "LINE-NEW-001",
                "product_id": "PROD-001",
                "product_name": "Frozen Mahi Mahi Fillet",
                "quantity": 50.0,
                "unit_of_measure": "kg",
                "unit_price": 8.2,
                "subtotal": 410.0,
                "supplier_id": "SUP-001",
            }
        ],
        delivery_date="2026-04-05",
    )
    assert order.order_id == "ORD-004"
    assert order.total_amount == 410.0
    assert environment.tools.db.inventory["INVREC-001"].quantity_available == 950.0
    assert environment.tools.db.inventory["INVREC-001"].quantity_reserved == 150.0

    with pytest.raises(ValueError):
        environment.tools.register_order(
            customer_id="CUST-002",
            items=[
                {
                    "line_id": "LINE-FAIL-001",
                    "product_id": "PROD-001",
                    "product_name": "Frozen Mahi Mahi Fillet",
                    "quantity": 10.0,
                    "unit_of_measure": "kg",
                    "unit_price": 8.2,
                    "subtotal": 82.0,
                    "supplier_id": "SUP-001",
                }
            ],
            delivery_date="2026-04-05",
        )


def test_register_order_accepts_simplified_items(environment: Environment):
    order = environment.tools.register_order(
        customer_id="CUST-001",
        items=[
            {
                "product_id": "PROD-001",
                "quantity": 50.0,
                "unit_price": 8.2,
            }
        ],
        delivery_date="2026-04-05",
    )
    item = order.items[0]

    assert item.line_id == "LINE-004"
    assert item.product_name == "Frozen Mahi Mahi Fillet"
    assert item.unit_of_measure == "kg"
    assert item.unit_price == 8.2
    assert item.subtotal == 410.0
    assert item.supplier_id == "SUP-001"


def test_modify_order(environment: Environment):
    order = environment.tools.modify_order(
        order_id="ORD-001",
        items=[
            {
                "line_id": "LINE-001",
                "product_id": "PROD-001",
                "product_name": "Frozen Mahi Mahi Fillet",
                "quantity": 80.0,
                "unit_of_measure": "kg",
                "unit_price": 8.2,
                "subtotal": 656.0,
                "supplier_id": "SUP-001",
            }
        ],
        delivery_date="2026-04-03",
    )
    assert order.delivery_date.isoformat() == "2026-04-03"
    assert order.total_amount == 656.0

    with pytest.raises(ValueError):
        environment.tools.modify_order(
            order_id="ORD-002",
            delivery_date="2026-04-12",
        )


def test_modify_order_accepts_sparse_item_updates(environment: Environment):
    order = environment.tools.modify_order(
        order_id="ORD-001",
        items=[
            {
                "line_id": "LINE-001",
                "product_id": "PROD-001",
                "quantity": 80.0,
            }
        ],
        delivery_date="2026-04-03",
    )

    assert order.delivery_date.isoformat() == "2026-04-03"
    assert order.items[0].product_name == "Frozen Mahi Mahi Fillet"
    assert order.items[0].unit_of_measure == "kg"
    assert order.items[0].unit_price == 8.2
    assert order.items[0].subtotal == 656.0
    assert order.items[0].supplier_id == "SUP-001"
    assert order.total_amount == 656.0


def test_cancel_order(environment: Environment):
    order = environment.tools.cancel_order(
        order_id="ORD-001", reason="Customer requested cancellation"
    )
    assert order.status == "cancelled"
    assert environment.tools.db.inventory["INVREC-001"].quantity_available == 1100.0
    assert environment.tools.db.inventory["INVREC-001"].quantity_reserved == 0.0

    with pytest.raises(ValueError):
        environment.tools.cancel_order(
            order_id="ORD-002", reason="Cannot cancel shipped order"
        )


def test_get_order_status(environment: Environment):
    order_status = environment.tools.get_order_status("ORD-002")
    assert order_status["order"].status == "shipped"
    assert order_status["shipment_statuses"] == ["in_transit"]
    assert order_status["invoice_statuses"] == ["partially_paid"]

    with pytest.raises(ValueError):
        environment.tools.get_order_status("MISSING")


def test_register_claim(environment: Environment):
    claim = environment.tools.register_claim(
        customer_id="CUST-001",
        subject="Delayed shipment follow-up",
        description="Customer needs a formal status record.",
        order_id="ORD-002",
        invoice_id="INV-001",
    )
    assert claim.claim_id == "CLM-001"
    assert claim.status == "open"

    with pytest.raises(ValueError):
        environment.tools.register_claim(
            customer_id="MISSING",
            subject="Invalid claim",
            description="Should fail",
        )


def test_issue_invoice(environment: Environment):
    invoice = environment.tools.issue_invoice("ORD-001")
    assert invoice.invoice_id == "INV-003"
    assert invoice.status == "issued"
    assert "INV-003" in environment.tools.db.orders["ORD-001"].invoice_ids

    with pytest.raises(ValueError):
        environment.tools.issue_invoice("ORD-003")


def test_make_payment(environment: Environment):
    invoice = environment.tools.make_payment(
        invoice_id="INV-002",
        amount=200.0,
        payment_method="bank_transfer",
        reference="TRX-NEW-001",
    )
    assert invoice.paid_amount == 200.0
    assert invoice.status == "partially_paid"
    assert len(invoice.payment_records) == 1

    with pytest.raises(ValueError):
        environment.tools.make_payment(
            invoice_id="INV-001",
            amount=1000.0,
            payment_method="bank_transfer",
        )


# ---------------------------------------------------------------------------
# SMS verification tests
# ---------------------------------------------------------------------------


@pytest.fixture
def env_with_employees(fishtrader_db: FishTraderDB) -> Environment:
    from tau2.domains.fishtrader_garbich.data_model import Employee

    fishtrader_db.employees = {
        "EMP-001": Employee(
            employee_id="EMP-001",
            full_name="Carlos Mendoza",
            phone="+51-900-000-101",
            department="Operations",
        )
    }
    return get_environment(fishtrader_db, use_rag=False)


def test_send_verification_code_user(env_with_employees: Environment):
    result = env_with_employees.tools.send_verification_code("CUST-001")
    assert "CUST-001" in result
    assert env_with_employees.tools._pending_verification is not None
    assert env_with_employees.tools._pending_verification["role"] == "user"
    assert len(env_with_employees.tools._pending_verification["code"]) == 6


def test_send_verification_code_employee(env_with_employees: Environment):
    result = env_with_employees.tools.send_verification_code("EMP-001")
    assert "EMP-001" in result
    assert env_with_employees.tools._pending_verification["role"] == "employee"


def test_send_verification_code_invalid(env_with_employees: Environment):
    with pytest.raises(ValueError):
        env_with_employees.tools.send_verification_code("NONEXISTENT")


def test_verify_code_correct(env_with_employees: Environment):
    env_with_employees.tools.send_verification_code("CUST-001")
    code = env_with_employees.tools._pending_verification["code"]
    result = env_with_employees.tools.verify_code(code)
    assert "verified" in result.lower()
    assert env_with_employees.tools._verified is not None
    assert env_with_employees.tools._pending_verification is None


def test_verify_code_incorrect(env_with_employees: Environment):
    env_with_employees.tools.send_verification_code("CUST-001")
    result = env_with_employees.tools.verify_code("000000")
    assert "failed" in result.lower() or "incorrect" in result.lower()
    assert env_with_employees.tools._verified is None
    assert env_with_employees.tools._pending_verification is None


def test_verify_code_no_pending(env_with_employees: Environment):
    result = env_with_employees.tools.verify_code("123456")
    assert "no verification code" in result.lower()


def test_assert_identity_verified(env_with_employees: Environment):
    assert env_with_employees.tools.assert_identity_verified() is False
    env_with_employees.tools.send_verification_code("CUST-001")
    code = env_with_employees.tools._pending_verification["code"]
    env_with_employees.tools.verify_code(code)
    assert env_with_employees.tools.assert_identity_verified() is True


def test_assert_verified_role(env_with_employees: Environment):
    env_with_employees.tools.send_verification_code("EMP-001")
    code = env_with_employees.tools._pending_verification["code"]
    env_with_employees.tools.verify_code(code)
    assert env_with_employees.tools.assert_verified_role("employee") is True
    assert env_with_employees.tools.assert_verified_role("user") is False


def test_check_sms_after_sync(env_with_employees: Environment):
    from tau2.domains.fishtrader_garbich.environment import FishTraderEnvironment

    assert isinstance(env_with_employees, FishTraderEnvironment)
    assert env_with_employees.user_tools.check_sms() == "No verification code has been received yet."

    env_with_employees.tools.send_verification_code("CUST-001")
    env_with_employees.sync_tools()
    sms_result = env_with_employees.user_tools.check_sms()
    assert "SMS verification code" in sms_result

    code = env_with_employees.tools._pending_verification["code"]
    assert code in sms_result


def test_retrieve_policy_returns_text():
    index = ChromaPolicyIndex(
        SAMPLE_POLICY, strategy="headers", _embed_fn=_fake_embed
    )
    kit = FishTraderTools(db=None, policy_index=index)
    result = kit.retrieve_policy(query="¿puedo cancelar mi pedido?")
    assert isinstance(result, str) and len(result) > 0


def test_toolkit_has_think_tool():
    kit = FishTraderTools(db=None)
    assert "think" in kit.tools
