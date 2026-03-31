import datetime

import pytest

from tau2.domains.estaciondeservicio_Rivera.data_model import (
    BankTransfer,
    Cash,
    Claim,
    Credit,
    Customer,
    FuelStationDB,
    Item,
    Order,
    Payment,
    VirtualInvoice,
)
from tau2.domains.estaciondeservicio_Rivera.tools import (
    EstacionDeServicioRiveraTools,
)


@pytest.fixture
def fixed_now() -> datetime.datetime:
    return datetime.datetime(2026, 3, 30, 10, 0, 0)


@pytest.fixture
def fuel_station_db(fixed_now: datetime.datetime) -> FuelStationDB:
    customer_1 = Customer(
        id_cliente="cliente_0001",
        nombre_contacto="Elena Paredes",
        razon_social="Transporte Rivera Norte SAC",
        ruc="20601234567",
        telefono="987654321",
        email="elena@riveranorte.pe",
        direccion_fiscal="Calle San Martin 145, Sullana, Piura",
        direcciones_entrega=[
            "Planta Sullana, Zona Industrial Lote 12, Sullana, Piura",
            "Almacen Sur, Sullana, Piura",
        ],
        correo_facturacion="facturacion@riveranorte.pe",
    )
    customer_2 = Customer(
        id_cliente="cliente_0002",
        nombre_contacto="Mario Salazar",
        razon_social="Logistica Salazar SAC",
        ruc="20550010001",
        telefono="999000111",
        email="mario@logsalazar.pe",
        direccion_fiscal="Calle Dos 120, Sullana, Piura",
        direcciones_entrega=["Sede Bellavista, Sullana, Piura"],
        correo_facturacion="facturas@logsalazar.pe",
    )

    items = {
        "item_0087": Item(
            id_item="item_0087",
            nombre_producto="Gasolina Regular",
            tipo_producto="combustible",
            unidad_medida="galones",
            precio=15.5,
            cantidad_disponible=1000,
        ),
        "item_0088": Item(
            id_item="item_0088",
            nombre_producto="Gasolina Premium",
            tipo_producto="combustible",
            unidad_medida="galones",
            precio=18.2,
            cantidad_disponible=800,
        ),
        "item_0089": Item(
            id_item="item_0089",
            nombre_producto="GLP",
            tipo_producto="combustible",
            unidad_medida="galones",
            precio=8.9,
            cantidad_disponible=700,
        ),
        "item_0090": Item(
            id_item="item_0090",
            nombre_producto="Petroleo",
            tipo_producto="combustible",
            unidad_medida="galones",
            precio=14.3,
            cantidad_disponible=900,
        ),
        "item_0001": Item(
            id_item="item_0001",
            nombre_producto="Aceite Sintetico 2T",
            tipo_producto="lubricante",
            unidad_medida="unidad",
            precio=35.0,
            cantidad_disponible=100,
        ),
    }

    payment_methods = {
        "payment_credit_0001": Credit(
            id="payment_credit_0001",
            source="credit",
            brand="visa",
            last_four="4242",
        ),
        "payment_bank_0001": BankTransfer(
            id="payment_bank_0001",
            source="bank_transfer",
            bank_name="BCP",
            account_reference="CCI-123456",
        ),
        "payment_cash_0001": Cash(
            id="payment_cash_0001",
            source="cash",
        ),
    }

    orders = {
        "order_pending_0001": Order(
            id_order="order_pending_0001",
            id_cliente="cliente_0001",
            id_order_combustible_asociado=None,
            id_item="item_0087",
            nombre_producto_snapshot="Gasolina Regular",
            tipo_producto_snapshot="combustible",
            unidad_medida="galones",
            precio_unitario_snapshot=15.5,
            cantidad_solicitada=300,
            cantidad_atendida=300,
            minimo_galones=250,
            direccion_entrega="Planta Sullana, Zona Industrial Lote 12, Sullana, Piura",
            persona_contacto="Elena Paredes",
            telefono_contacto="987654321",
            fecha_hora_solicitada=fixed_now - datetime.timedelta(days=1),
            fecha_hora_programada=fixed_now + datetime.timedelta(days=2),
            fecha_hora_entrega_real=None,
            precio_total=4650.0,
            payment_method_id="payment_credit_0001",
            estado_pago="pending",
            comprobante_entrega=None,
            placa_unidad=None,
            fecha_hora_cancelacion=None,
            motivo_cancelacion=None,
            observaciones=None,
            pago_ids=[],
            factura_virtual=VirtualInvoice(
                invoice_id=None,
                email_envio=None,
                estado_factura="not_requested",
            ),
            estado_pedido="pending",
        ),
        "order_lubricant_base": Order(
            id_order="order_lubricant_base",
            id_cliente="cliente_0001",
            id_order_combustible_asociado=None,
            id_item="item_0090",
            nombre_producto_snapshot="Petroleo",
            tipo_producto_snapshot="combustible",
            unidad_medida="galones",
            precio_unitario_snapshot=14.3,
            cantidad_solicitada=500,
            cantidad_atendida=500,
            minimo_galones=250,
            direccion_entrega="Planta Sullana, Zona Industrial Lote 12, Sullana, Piura",
            persona_contacto="Elena Paredes",
            telefono_contacto="987654321",
            fecha_hora_solicitada=fixed_now - datetime.timedelta(days=1),
            fecha_hora_programada=fixed_now + datetime.timedelta(days=1, hours=6),
            fecha_hora_entrega_real=None,
            precio_total=7150.0,
            payment_method_id="payment_bank_0001",
            estado_pago="pending",
            comprobante_entrega=None,
            placa_unidad=None,
            fecha_hora_cancelacion=None,
            motivo_cancelacion=None,
            observaciones=None,
            pago_ids=[],
            factura_virtual=VirtualInvoice(
                invoice_id=None,
                email_envio=None,
                estado_factura="not_requested",
            ),
            estado_pedido="pending",
        ),
        "order_paid_0001": Order(
            id_order="order_paid_0001",
            id_cliente="cliente_0001",
            id_order_combustible_asociado=None,
            id_item="item_0088",
            nombre_producto_snapshot="Gasolina Premium",
            tipo_producto_snapshot="combustible",
            unidad_medida="galones",
            precio_unitario_snapshot=18.2,
            cantidad_solicitada=300,
            cantidad_atendida=300,
            minimo_galones=250,
            direccion_entrega="Planta Sullana, Zona Industrial Lote 12, Sullana, Piura",
            persona_contacto="Elena Paredes",
            telefono_contacto="987654321",
            fecha_hora_solicitada=fixed_now - datetime.timedelta(days=2),
            fecha_hora_programada=fixed_now + datetime.timedelta(days=1),
            fecha_hora_entrega_real=None,
            precio_total=5460.0,
            payment_method_id="payment_credit_0001",
            estado_pago="paid",
            comprobante_entrega=None,
            placa_unidad=None,
            fecha_hora_cancelacion=None,
            motivo_cancelacion=None,
            observaciones=None,
            pago_ids=["pago_0001"],
            factura_virtual=VirtualInvoice(
                invoice_id=None,
                email_envio="facturacion@riveranorte.pe",
                estado_factura="pending",
            ),
            estado_pedido="pending",
        ),
        "order_due_delivery": Order(
            id_order="order_due_delivery",
            id_cliente="cliente_0001",
            id_order_combustible_asociado=None,
            id_item="item_0089",
            nombre_producto_snapshot="GLP",
            tipo_producto_snapshot="combustible",
            unidad_medida="galones",
            precio_unitario_snapshot=8.9,
            cantidad_solicitada=260,
            cantidad_atendida=260,
            minimo_galones=250,
            direccion_entrega="Planta Sullana, Zona Industrial Lote 12, Sullana, Piura",
            persona_contacto="Elena Paredes",
            telefono_contacto="987654321",
            fecha_hora_solicitada=fixed_now - datetime.timedelta(days=2),
            fecha_hora_programada=fixed_now - datetime.timedelta(hours=1),
            fecha_hora_entrega_real=None,
            precio_total=2314.0,
            payment_method_id="payment_cash_0001",
            estado_pago="pending",
            comprobante_entrega=None,
            placa_unidad=None,
            fecha_hora_cancelacion=None,
            motivo_cancelacion=None,
            observaciones=None,
            pago_ids=[],
            factura_virtual=VirtualInvoice(
                invoice_id=None,
                email_envio=None,
                estado_factura="not_requested",
            ),
            estado_pedido="pending",
        ),
        "order_delivered_0001": Order(
            id_order="order_delivered_0001",
            id_cliente="cliente_0001",
            id_order_combustible_asociado=None,
            id_item="item_0087",
            nombre_producto_snapshot="Gasolina Regular",
            tipo_producto_snapshot="combustible",
            unidad_medida="galones",
            precio_unitario_snapshot=15.5,
            cantidad_solicitada=280,
            cantidad_atendida=280,
            minimo_galones=250,
            direccion_entrega="Planta Sullana, Zona Industrial Lote 12, Sullana, Piura",
            persona_contacto="Elena Paredes",
            telefono_contacto="987654321",
            fecha_hora_solicitada=fixed_now - datetime.timedelta(days=3),
            fecha_hora_programada=fixed_now - datetime.timedelta(days=1),
            fecha_hora_entrega_real=fixed_now - datetime.timedelta(hours=12),
            precio_total=4340.0,
            payment_method_id="payment_bank_0001",
            estado_pago="pending",
            comprobante_entrega="GR-001",
            placa_unidad="ABC-123",
            fecha_hora_cancelacion=None,
            motivo_cancelacion=None,
            observaciones=None,
            pago_ids=[],
            factura_virtual=VirtualInvoice(
                invoice_id="factura_0001",
                email_envio="facturacion@riveranorte.pe",
                estado_factura="sent",
            ),
            estado_pedido="delivered",
        ),
        "order_too_late_0001": Order(
            id_order="order_too_late_0001",
            id_cliente="cliente_0002",
            id_order_combustible_asociado=None,
            id_item="item_0090",
            nombre_producto_snapshot="Petroleo",
            tipo_producto_snapshot="combustible",
            unidad_medida="galones",
            precio_unitario_snapshot=14.3,
            cantidad_solicitada=260,
            cantidad_atendida=260,
            minimo_galones=250,
            direccion_entrega="Sede Bellavista, Sullana, Piura",
            persona_contacto="Mario Salazar",
            telefono_contacto="999000111",
            fecha_hora_solicitada=fixed_now - datetime.timedelta(days=2),
            fecha_hora_programada=fixed_now + datetime.timedelta(hours=6),
            fecha_hora_entrega_real=None,
            precio_total=3718.0,
            payment_method_id="payment_bank_0001",
            estado_pago="pending",
            comprobante_entrega=None,
            placa_unidad=None,
            fecha_hora_cancelacion=None,
            motivo_cancelacion=None,
            observaciones=None,
            pago_ids=[],
            factura_virtual=VirtualInvoice(
                invoice_id=None,
                email_envio=None,
                estado_factura="not_requested",
            ),
            estado_pedido="pending",
        ),
    }

    payments = {
        "pago_0001": Payment(
            id_pago="pago_0001",
            id_order="order_paid_0001",
            monto=5460.0,
            fecha_pago=fixed_now - datetime.timedelta(days=1),
            payment_method_id="payment_credit_0001",
            estado_pago="paid",
        )
    }

    claims = {
        "reclamacion_0001": Claim(
            id_reclamacion="reclamacion_0001",
            id_cliente="cliente_0001",
            id_order="order_delivered_0001",
            motivo="Late delivery",
            descripcion="Truck arrived late",
            fecha_reclamacion=fixed_now - datetime.timedelta(hours=3),
            estado_reclamacion="registered",
        )
    }

    return FuelStationDB(
        clientes={"cliente_0001": customer_1, "cliente_0002": customer_2},
        items=items,
        payment_methods=payment_methods,
        pagos=payments,
        reclamaciones=claims,
        orders=orders,
    )


@pytest.fixture
def tools(
    fuel_station_db: FuelStationDB, fixed_now: datetime.datetime
) -> EstacionDeServicioRiveraTools:
    toolkit = EstacionDeServicioRiveraTools(fuel_station_db)
    toolkit._get_now = lambda: fixed_now
    return toolkit


def test_get_client_details(tools: EstacionDeServicioRiveraTools):
    customer = tools.get_client_details("cliente_0001")
    assert customer.ruc == "20601234567"
    with pytest.raises(ValueError, match="Customer not found"):
        tools.get_client_details("missing_customer")


def test_get_order_details(tools: EstacionDeServicioRiveraTools):
    order = tools.get_order_details("order_pending_0001")
    assert order.id_item == "item_0087"
    with pytest.raises(ValueError, match="Order not found"):
        tools.get_order_details("missing_order")


def test_search_client_by_ruc(tools: EstacionDeServicioRiveraTools):
    customer = tools.search_client_by_ruc("20550010001")
    assert customer.id_cliente == "cliente_0002"
    with pytest.raises(ValueError, match="Customer not found"):
        tools.search_client_by_ruc("00000000000")


def test_get_orders_by_client(tools: EstacionDeServicioRiveraTools):
    orders = tools.get_orders_by_client("cliente_0001")
    assert len(orders) >= 4
    with pytest.raises(ValueError, match="Customer not found"):
        tools.get_orders_by_client("missing_customer")


def test_show_catalog(tools: EstacionDeServicioRiveraTools):
    catalog = tools.show_catalog()
    assert any(item.id_item == "item_0087" for item in catalog)


def test_search_items_by_name_or_type(tools: EstacionDeServicioRiveraTools):
    results = tools.search_items_by_name_or_type("premium")
    assert any(item.id_item == "item_0088" for item in results)
    with pytest.raises(ValueError, match="No items were found"):
        tools.search_items_by_name_or_type("nonexistent-product")


def test_consult_stock(tools: EstacionDeServicioRiveraTools):
    stock = tools.consult_stock("item_0089")
    assert stock.id_item == "item_0089"
    assert stock.disponible is True
    with pytest.raises(ValueError, match="Item not found"):
        tools.consult_stock("missing_item")


def test_list_available_payment_methods(tools: EstacionDeServicioRiveraTools):
    methods = tools.list_available_payment_methods()
    assert len(methods) == 3


def test_get_payment_method_details(tools: EstacionDeServicioRiveraTools):
    method = tools.get_payment_method_details("payment_credit_0001")
    assert method.source == "credit"
    with pytest.raises(ValueError, match="Payment method not found"):
        tools.get_payment_method_details("missing_payment")


def test_register_client(tools: EstacionDeServicioRiveraTools):
    customer = tools.register_client(
        nombre_contacto="Lucia Ramos",
        razon_social="Ramos Logistic SAC",
        ruc="20999999999",
        telefono="955444222",
        email="lucia@ramos.pe",
        direccion_fiscal="Av. Principal 123, Sullana, Piura",
        direcciones_entrega=["Base Oeste, Sullana, Piura"],
        correo_facturacion="facturacion@ramos.pe",
    )
    assert customer.id_cliente in tools.db.clientes
    with pytest.raises(ValueError, match="already registered"):
        tools.register_client(
            nombre_contacto="Dup",
            razon_social="Dup SAC",
            ruc="20601234567",
            telefono="111",
            email="dup@example.com",
            direccion_fiscal="Somewhere",
        )


def test_update_client(tools: EstacionDeServicioRiveraTools):
    customer = tools.update_client(
        "cliente_0001",
        telefono="900000000",
        correo_facturacion="nuevo@rivera.pe",
    )
    assert customer.telefono == "900000000"
    assert customer.correo_facturacion == "nuevo@rivera.pe"
    with pytest.raises(ValueError, match="Customer not found"):
        tools.update_client("missing_customer", telefono="1")


def test_add_delivery_address_to_client(tools: EstacionDeServicioRiveraTools):
    customer = tools.add_delivery_address_to_client(
        "cliente_0002", "Nuevo Patio, Sullana, Piura"
    )
    assert "Nuevo Patio, Sullana, Piura" in customer.direcciones_entrega
    with pytest.raises(ValueError, match="Customer not found"):
        tools.add_delivery_address_to_client("missing_customer", "x")


def test_update_order_payment_method(tools: EstacionDeServicioRiveraTools):
    order = tools.update_order_payment_method(
        "order_pending_0001", "payment_bank_0001"
    )
    assert order.payment_method_id == "payment_bank_0001"
    with pytest.raises(ValueError, match="cannot be changed after a payment"):
        tools.update_order_payment_method("order_paid_0001", "payment_bank_0001")


def test_remove_delivery_address_from_client(tools: EstacionDeServicioRiveraTools):
    customer = tools.remove_delivery_address_from_client(
        "cliente_0001", "Almacen Sur, Sullana, Piura"
    )
    assert "Almacen Sur, Sullana, Piura" not in customer.direcciones_entrega
    with pytest.raises(ValueError, match="must keep at least one delivery address"):
        tools.remove_delivery_address_from_client(
            "cliente_0002", "Sede Bellavista, Sullana, Piura"
        )


def test_register_payment_method(tools: EstacionDeServicioRiveraTools):
    credit_method = tools.register_payment_method(
        source="credit", brand="mastercard", last_four="5555"
    )
    transfer_method = tools.register_payment_method(
        source="bank_transfer",
        bank_name="BBVA",
        account_reference="CCI-999",
    )
    cash_method = tools.register_payment_method(source="cash")
    assert credit_method.source == "credit"
    assert transfer_method.source == "bank_transfer"
    assert cash_method.source == "cash"
    with pytest.raises(ValueError, match="invalid"):
        tools.register_payment_method(source="crypto")


def test_register_order(tools: EstacionDeServicioRiveraTools):
    order = tools.register_order(
        id_cliente="cliente_0001",
        id_item="item_0088",
        cantidad_solicitada=260,
        direccion_entrega="Planta Sullana, Zona Industrial Lote 12, Sullana, Piura",
        persona_contacto="Elena Paredes",
        telefono_contacto="987654321",
        fecha_hora_programada=tools._get_now() + datetime.timedelta(days=2),
        payment_method_id="payment_bank_0001",
        solicitar_factura_virtual=True,
        email_factura="facturacion@riveranorte.pe",
    )
    assert order.id_order in tools.db.orders
    lubricant_order = tools.register_order(
        id_cliente="cliente_0001",
        id_item="item_0001",
        cantidad_solicitada=1,
        direccion_entrega="Planta Sullana, Zona Industrial Lote 12, Sullana, Piura",
        persona_contacto="Elena Paredes",
        telefono_contacto="987654321",
        fecha_hora_programada=tools._get_now() + datetime.timedelta(days=2),
        payment_method_id="payment_bank_0001",
        id_order_combustible_asociado="order_lubricant_base",
    )
    assert lubricant_order.id_order_combustible_asociado == "order_lubricant_base"
    with pytest.raises(ValueError, match="at least 24 hours"):
        tools.register_order(
            id_cliente="cliente_0001",
            id_item="item_0087",
            cantidad_solicitada=260,
            direccion_entrega="Planta Sullana, Zona Industrial Lote 12, Sullana, Piura",
            persona_contacto="Elena Paredes",
            telefono_contacto="987654321",
            fecha_hora_programada=tools._get_now() + datetime.timedelta(hours=2),
            payment_method_id="payment_bank_0001",
        )


def test_update_order(tools: EstacionDeServicioRiveraTools):
    updated = tools.update_order(
        "order_pending_0001",
        cantidad_solicitada=320,
        direccion_entrega="Almacen Sur, Sullana, Piura",
        observaciones="Update test",
    )
    assert updated.cantidad_solicitada == 320
    assert updated.direccion_entrega == "Almacen Sur, Sullana, Piura"
    with pytest.raises(ValueError, match="already has registered payments"):
        tools.update_order("order_paid_0001", cantidad_solicitada=310)


def test_reschedule_order(tools: EstacionDeServicioRiveraTools):
    order = tools.reschedule_order(
        "order_pending_0001", tools._get_now() + datetime.timedelta(days=3)
    )
    assert order.fecha_hora_programada == tools._get_now() + datetime.timedelta(days=3)
    with pytest.raises(ValueError, match="only be rescheduled up to 12 hours"):
        tools.reschedule_order(
            "order_too_late_0001", tools._get_now() + datetime.timedelta(days=1)
        )


def test_cancel_order(tools: EstacionDeServicioRiveraTools):
    order = tools.cancel_order("order_pending_0001", "Customer request")
    assert order.estado_pedido == "cancelled"
    assert order.cantidad_atendida == 0
    with pytest.raises(ValueError, match="only be cancelled up to 12 hours"):
        tools.cancel_order("order_too_late_0001", "Too late")


def test_get_order_status(tools: EstacionDeServicioRiveraTools):
    status = tools.get_order_status("order_pending_0001")
    assert status.estado_pedido == "pending"
    with pytest.raises(ValueError, match="Order not found"):
        tools.get_order_status("missing_order")


def test_get_payment_status(tools: EstacionDeServicioRiveraTools):
    status = tools.get_payment_status("order_paid_0001")
    assert status.estado_pago == "paid"
    assert status.saldo_pendiente == 0
    pending_status = tools.get_payment_status("order_pending_0001")
    assert pending_status.estado_pago == "pending"


def test_register_claim(tools: EstacionDeServicioRiveraTools):
    claim = tools.register_claim(
        id_cliente="cliente_0001",
        motivo="Delay",
        descripcion="Delayed delivery",
        id_order="order_delivered_0001",
    )
    assert claim.id_reclamacion in tools.db.reclamaciones
    with pytest.raises(ValueError, match="Customer not found"):
        tools.register_claim("missing_customer", "x", "y")


def test_get_claim_details(tools: EstacionDeServicioRiveraTools):
    claim = tools.get_claim_details("reclamacion_0001")
    assert claim.motivo == "Late delivery"
    with pytest.raises(ValueError, match="Claim not found"):
        tools.get_claim_details("missing_claim")


def test_get_claims_by_client(tools: EstacionDeServicioRiveraTools):
    claims = tools.get_claims_by_client("cliente_0001")
    assert len(claims) == 1
    with pytest.raises(ValueError, match="Customer not found"):
        tools.get_claims_by_client("missing_customer")


def test_update_claim_status(tools: EstacionDeServicioRiveraTools):
    claim = tools.update_claim_status("reclamacion_0001", "resolved")
    assert claim.estado_reclamacion == "resolved"
    with pytest.raises(ValueError, match="invalid"):
        tools.update_claim_status("reclamacion_0001", "closed")


def test_emit_virtual_invoice(tools: EstacionDeServicioRiveraTools):
    result = tools.emit_virtual_invoice(
        "order_pending_0001", email_envio="billing@rivera.pe"
    )
    assert result.factura_virtual.estado_factura == "sent"
    assert result.factura_virtual.email_envio == "billing@rivera.pe"
    with pytest.raises(ValueError, match="Order not found"):
        tools.emit_virtual_invoice("missing_order")


def test_mark_order_delivered(tools: EstacionDeServicioRiveraTools):
    order = tools.mark_order_delivered(
        "order_due_delivery", comprobante_entrega="GR-999", placa_unidad="XYZ-123"
    )
    assert order.estado_pedido == "delivered"
    assert order.comprobante_entrega == "GR-999"
    with pytest.raises(ValueError, match="Only pending orders can be marked as delivered"):
        tools.mark_order_delivered("order_delivered_0001", "GR-000")


def test_make_payment(tools: EstacionDeServicioRiveraTools):
    result = tools.make_payment(
        "order_due_delivery", "payment_cash_0001", 2314.0
    )
    assert result.total_pagado == 2314.0
    assert result.saldo_pendiente == 0
    with pytest.raises(ValueError, match="selected for the order"):
        tools.make_payment("order_pending_0001", "payment_cash_0001", 4650.0)
    with pytest.raises(ValueError, match="single transaction"):
        tools.make_payment("order_pending_0001", "payment_credit_0001", 1000.0)


def test_transfer_to_human_agents(tools: EstacionDeServicioRiveraTools):
    result = tools.transfer_to_human_agents("Need human support")
    assert result == "Transfer successful"

