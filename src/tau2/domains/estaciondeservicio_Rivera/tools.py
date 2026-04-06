"""Toolkit for the estaciondeservicio_Rivera domain."""

import datetime
import re
from typing import List, Optional

from pydantic import BaseModel, Field

from tau2.domains.estaciondeservicio_Rivera.data_model import (
    BankTransfer,
    Claim,
    Cash,
    Customer,
    CustomerCredit,
    FuelStationDB,
    Item,
    Order,
    Payment,
    PaymentMethod,
    VirtualInvoice,
)
from tau2.environment.toolkit import ToolKitBase, ToolType, is_tool


class StockInfo(BaseModel):
    """Stock summary for a catalog product."""

    id_item: str = Field(description="Item identifier")
    nombre_producto: str = Field(description="Product name")
    tipo_producto: str = Field(description="Product type")
    cantidad_disponible: int = Field(description="Available stock quantity")
    disponible: bool = Field(description="Whether the item is currently in stock")


class OrderStatusInfo(BaseModel):
    """Operational summary of an order status."""

    id_order: str = Field(description="Order identifier")
    estado_pedido: str = Field(description="Current order status")
    cantidad_solicitada: int = Field(description="Requested quantity")
    cantidad_atendida: int = Field(description="Fulfilled quantity")
    fecha_hora_programada: datetime.datetime = Field(
        description="Scheduled delivery date and time"
    )
    fecha_hora_entrega_real: Optional[datetime.datetime] = Field(
        default=None, description="Actual delivery date and time"
    )


class InvoiceEmissionResult(BaseModel):
    """Result of issuing or updating a virtual invoice."""

    id_order: str = Field(description="Order identifier")
    factura_virtual: VirtualInvoice = Field(
        description="Current virtual invoice state for the order"
    )


class PaymentResult(BaseModel):
    """Result of registering a payment."""

    pago: Payment = Field(description="Registered payment")
    total_pagado: float = Field(description="Total paid amount for the order")
    saldo_pendiente: float = Field(description="Remaining amount pending")


class PaymentStatusInfo(BaseModel):
    """Summary of the payment status of an order."""

    id_order: str = Field(description="Order identifier")
    estado_pago: str = Field(description="Aggregated payment status of the order")
    total_pagado: float = Field(description="Total amount paid for the order")
    saldo_pendiente: float = Field(description="Remaining amount pending for the order")
    payment_method_id: Optional[str] = Field(
        default=None, description="Payment method used for the order, if any"
    )


class EstacionDeServicioRiveraTools(ToolKitBase):
    """Toolkit for the fuel-station delivery-order domain."""

    db: FuelStationDB

    def __init__(self, db: FuelStationDB) -> None:
        super().__init__(db)

    def _get_now(self) -> datetime.datetime:
        return datetime.datetime.now()

    def _generate_id(self, prefix: str, existing_ids: set[str]) -> str:
        index = len(existing_ids) + 1
        while f"{prefix}_{index:04d}" in existing_ids:
            index += 1
        return f"{prefix}_{index:04d}"

    def _next_event_timestamp(self) -> datetime.datetime:
        """Builds a deterministic timestamp for persisted events."""
        candidates: list[datetime.datetime] = []

        for order in self.db.orders.values():
            candidates.append(order.fecha_hora_solicitada)
            candidates.append(order.fecha_hora_programada)
            if order.fecha_hora_entrega_real is not None:
                candidates.append(order.fecha_hora_entrega_real)
            if order.fecha_hora_cancelacion is not None:
                candidates.append(order.fecha_hora_cancelacion)

        for pago in self.db.pagos.values():
            candidates.append(pago.fecha_pago)

        for claim in self.db.reclamaciones.values():
            candidates.append(claim.fecha_reclamacion)

        if not candidates:
            return datetime.datetime(2026, 1, 1, 0, 0, 0)
        return max(candidates) + datetime.timedelta(seconds=1)

    def _normalize_claim_reason(self, motivo: str) -> str:
        motivo_clean = " ".join(motivo.strip().split())
        if motivo_clean.lower() == "late delivery":
            return "Late delivery"
        return motivo_clean

    def _normalize_claim_description(
        self, descripcion: str, id_order: Optional[str] = None
    ) -> str:
        descripcion_clean = " ".join(descripcion.strip().split())
        if id_order is not None:
            descripcion_clean = re.sub(
                rf"\s+for\s+{re.escape(id_order)}\.?$",
                "",
                descripcion_clean,
                flags=re.IGNORECASE,
            )
        return descripcion_clean

    def _get_cliente(self, id_cliente: str) -> Customer:
        if id_cliente not in self.db.clientes:
            raise ValueError("Customer not found")
        return self.db.clientes[id_cliente]

    def _get_cliente_by_ruc(self, ruc: str) -> Customer:
        for cliente in self.db.clientes.values():
            if cliente.ruc == ruc:
                return cliente
        raise ValueError("Customer not found")

    def _get_item(self, id_item: str) -> Item:
        if id_item not in self.db.items:
            raise ValueError("Item not found")
        return self.db.items[id_item]

    def _get_order(self, id_order: str) -> Order:
        if id_order not in self.db.orders:
            raise ValueError("Order not found")
        return self.db.orders[id_order]

    def _get_payment_method(self, payment_method_id: str) -> PaymentMethod:
        if payment_method_id not in self.db.payment_methods:
            raise ValueError("Payment method not found")
        return self.db.payment_methods[payment_method_id]

    def _get_claim(self, id_reclamacion: str) -> Claim:
        if id_reclamacion not in self.db.reclamaciones:
            raise ValueError("Claim not found")
        return self.db.reclamaciones[id_reclamacion]

    def _get_total_pagado(self, order: Order) -> float:
        total = 0.0
        for pago_id in order.pago_ids:
            pago = self.db.pagos[pago_id]
            if pago.estado_pago == "paid":
                total += pago.monto
        return round(total, 2)

    def _refresh_order_payment_status(self, order: Order) -> None:
        total_pagado = self._get_total_pagado(order)
        if total_pagado <= 0:
            order.estado_pago = "pending"
        else:
            order.estado_pago = "paid"

    def _get_order_payment_method_id(self, order: Order) -> Optional[str]:
        if order.pago_ids:
            first_payment_id = order.pago_ids[0]
            return self.db.pagos[first_payment_id].payment_method_id
        return order.payment_method_id

    def _validate_linked_fuel_order(self, id_cliente: str, id_order: str) -> Order:
        order = self._get_order(id_order)
        if order.id_cliente != id_cliente:
            raise ValueError(
                "The associated fuel order must belong to the same customer"
            )
        if order.tipo_producto_snapshot != "combustible":
            raise ValueError("The associated order must be a fuel order")
        if order.unidad_medida != "galones":
            raise ValueError("The associated fuel order must be expressed in gallons")
        if order.cantidad_solicitada < 250:
            raise ValueError("The associated fuel order must be at least 250 gallons")
        if order.estado_pedido == "cancelled":
            raise ValueError("The associated fuel order cannot be cancelled")
        return order

    def _build_invoice(
        self, solicitar_factura_virtual: bool, email_factura: Optional[str]
    ) -> VirtualInvoice:
        if not solicitar_factura_virtual:
            return VirtualInvoice(
                invoice_id=None,
                email_envio=None,
                estado_factura="not_requested",
            )
        return VirtualInvoice(
            invoice_id=None,
            email_envio=email_factura,
            estado_factura="pending",
        )

    @is_tool(ToolType.READ)
    def get_client_details(self, id_cliente: str) -> Customer:
        """Gets the full details of a registered customer."""
        return self._get_cliente(id_cliente)

    @is_tool(ToolType.READ)
    def get_order_details(self, id_order: str) -> Order:
        """Gets the full details of a registered order."""
        return self._get_order(id_order)

    @is_tool(ToolType.READ)
    def search_client_by_ruc(self, ruc: str) -> Customer:
        """Finds a registered customer by RUC."""
        return self._get_cliente_by_ruc(ruc)

    @is_tool(ToolType.READ)
    def get_orders_by_client(self, id_cliente: str) -> List[Order]:
        """Lists all registered orders for a customer."""
        self._get_cliente(id_cliente)
        return [
            order for order in self.db.orders.values() if order.id_cliente == id_cliente
        ]

    @is_tool(ToolType.READ)
    def show_catalog(self) -> List[Item]:
        """Shows the full product catalog available in the system."""
        return list(self.db.items.values())

    @is_tool(ToolType.READ)
    def search_items_by_name_or_type(self, query: str) -> List[Item]:
        """Searches catalog items by product name or type."""
        query_normalized = query.strip().lower()
        results = [
            item
            for item in self.db.items.values()
            if query_normalized in item.nombre_producto.lower()
            or query_normalized in item.tipo_producto.lower()
        ]
        if not results:
            raise ValueError("No items were found for the requested search")
        return results

    @is_tool(ToolType.READ)
    def consult_stock(self, id_item: str) -> StockInfo:
        """Checks the available stock for a catalog product."""
        item = self._get_item(id_item)
        return StockInfo(
            id_item=item.id_item,
            nombre_producto=item.nombre_producto,
            tipo_producto=item.tipo_producto,
            cantidad_disponible=item.cantidad_disponible,
            disponible=item.disponible,
        )

    @is_tool(ToolType.READ)
    def list_available_payment_methods(self) -> List[PaymentMethod]:
        """Lists the payment methods available in the database."""
        return list(self.db.payment_methods.values())

    @is_tool(ToolType.READ)
    def get_payment_method_details(self, payment_method_id: str) -> PaymentMethod:
        """Gets the details of a registered payment method."""
        return self._get_payment_method(payment_method_id)

    @is_tool(ToolType.WRITE)
    def register_client(
        self,
        nombre_contacto: str,
        razon_social: str,
        ruc: str,
        telefono: str,
        email: str,
        direccion_fiscal: str,
        direcciones_entrega: Optional[List[str]] = None,
        correo_facturacion: Optional[str] = None,
    ) -> Customer:
        """Registers a new corporate customer in the database."""
        try:
            self._get_cliente_by_ruc(ruc)
            raise ValueError("A customer with that RUC is already registered")
        except ValueError as exc:
            if str(exc) != "Customer not found":
                raise

        id_cliente = self._generate_id("cliente", set(self.db.clientes.keys()))
        cliente = Customer(
            id_cliente=id_cliente,
            nombre_contacto=nombre_contacto,
            razon_social=razon_social,
            ruc=ruc,
            telefono=telefono,
            email=email,
            direccion_fiscal=direccion_fiscal,
            direcciones_entrega=direcciones_entrega or [],
            correo_facturacion=correo_facturacion,
        )
        self.db.clientes[id_cliente] = cliente
        return cliente

    @is_tool(ToolType.WRITE)
    def update_client(
        self,
        id_cliente: str,
        nombre_contacto: Optional[str] = None,
        telefono: Optional[str] = None,
        email: Optional[str] = None,
        direccion_fiscal: Optional[str] = None,
        direcciones_entrega: Optional[List[str]] = None,
        correo_facturacion: Optional[str] = None,
    ) -> Customer:
        """Updates the data of a registered customer."""
        cliente = self._get_cliente(id_cliente)
        if nombre_contacto is not None:
            cliente.nombre_contacto = nombre_contacto
        if telefono is not None:
            cliente.telefono = telefono
        if email is not None:
            cliente.email = email
        if direccion_fiscal is not None:
            cliente.direccion_fiscal = direccion_fiscal
        if direcciones_entrega is not None:
            cliente.direcciones_entrega = direcciones_entrega
        if correo_facturacion is not None:
            cliente.correo_facturacion = correo_facturacion
        return Customer.model_validate(cliente.model_dump())

    @is_tool(ToolType.WRITE)
    def add_delivery_address_to_client(
        self, id_cliente: str, direccion_entrega: str
    ) -> Customer:
        """Adds a new authorized delivery address for a customer."""
        cliente = self._get_cliente(id_cliente)
        if direccion_entrega not in cliente.direcciones_entrega:
            cliente.direcciones_entrega.append(direccion_entrega)
        return Customer.model_validate(cliente.model_dump())

    @is_tool(ToolType.WRITE)
    def update_order_payment_method(
        self, id_order: str, payment_method_id: str
    ) -> Order:
        """Changes the selected payment method of a pending order before payment."""
        order = self._get_order(id_order)
        if order.estado_pedido != "pending":
            raise ValueError("The payment method can only be changed for pending orders")
        if order.pago_ids:
            raise ValueError("The payment method cannot be changed after a payment is registered")
        self._get_payment_method(payment_method_id)
        order.payment_method_id = payment_method_id
        return Order.model_validate(order.model_dump())

    @is_tool(ToolType.WRITE)
    def remove_delivery_address_from_client(
        self, id_cliente: str, direccion_entrega: str
    ) -> Customer:
        """Removes an authorized delivery address from a customer."""
        cliente = self._get_cliente(id_cliente)
        if direccion_entrega not in cliente.direcciones_entrega:
            raise ValueError("The delivery address does not exist for the customer")
        if len(cliente.direcciones_entrega) == 1:
            raise ValueError("The customer must keep at least one delivery address")
        cliente.direcciones_entrega.remove(direccion_entrega)
        return Customer.model_validate(cliente.model_dump())

    @is_tool(ToolType.WRITE)
    def register_payment_method(
        self,
        source: str,
        bank_name: Optional[str] = None,
        account_reference: Optional[str] = None,
        credit_agreement: Optional[str] = None,
    ) -> PaymentMethod:
        """Registers a payment method that can be used in orders."""
        id_metodo = self._generate_id("payment", set(self.db.payment_methods.keys()))
        if source == "bank_transfer":
            if not bank_name or not account_reference:
                raise ValueError("Registering a bank transfer requires bank_name and account_reference")
            metodo = BankTransfer(
                id=id_metodo,
                source="bank_transfer",
                bank_name=bank_name,
                account_reference=account_reference,
            )
        elif source == "cash":
            metodo = Cash(
                id=id_metodo,
                source="cash",
            )
        elif source == "customer_credit":
            if not credit_agreement:
                raise ValueError("Registering customer credit requires credit_agreement")
            metodo = CustomerCredit(
                id=id_metodo,
                source="customer_credit",
                credit_agreement=credit_agreement,
            )
        else:
            raise ValueError("The payment method type is invalid")

        self.db.payment_methods[id_metodo] = metodo
        return metodo

    @is_tool(ToolType.WRITE)
    def register_order(
        self,
        id_cliente: str,
        id_item: str,
        cantidad_solicitada: int,
        direccion_entrega: str,
        persona_contacto: str,
        telefono_contacto: str,
        fecha_hora_programada: datetime.datetime,
        payment_method_id: str,
        id_order_combustible_asociado: Optional[str] = None,
        solicitar_factura_virtual: bool = False,
        email_factura: Optional[str] = None,
        observaciones: Optional[str] = None,
    ) -> Order:
        """Registers a new delivery order for a customer."""
        cliente = self._get_cliente(id_cliente)
        item = self._get_item(id_item)
        self._get_payment_method(payment_method_id)

        if direccion_entrega not in cliente.direcciones_entrega:
            raise ValueError("The delivery address is not authorized for the customer")

        if item.cantidad_disponible <= 0:
            raise ValueError("There is no stock available for that product")

        if item.tipo_producto == "lubricante":
            if id_order_combustible_asociado is None:
                raise ValueError(
                    "Oils and lubricants may only be requested together with an associated fuel order of at least 250 gallons"
                )
            self._validate_linked_fuel_order(id_cliente, id_order_combustible_asociado)

        cantidad_atendida = min(cantidad_solicitada, item.cantidad_disponible)
        if cantidad_atendida < cantidad_solicitada:
            raise ValueError("There is not enough stock to fulfill the complete order")

        id_order = self._generate_id("order", set(self.db.orders.keys()))
        fecha_hora_solicitada = self._get_now()
        min_fecha_programada = fecha_hora_solicitada + datetime.timedelta(hours=24)
        if fecha_hora_programada < min_fecha_programada:
            raise ValueError("The order must be scheduled at least 24 hours in advance")
        order = Order(
            id_order=id_order,
            id_cliente=id_cliente,
            id_order_combustible_asociado=id_order_combustible_asociado,
            id_item=id_item,
            nombre_producto_snapshot=item.nombre_producto,
            tipo_producto_snapshot=item.tipo_producto,
            unidad_medida=item.unidad_medida,
            precio_unitario_snapshot=item.precio,
            cantidad_solicitada=cantidad_solicitada,
            cantidad_atendida=cantidad_atendida,
            direccion_entrega=direccion_entrega,
            persona_contacto=persona_contacto,
            telefono_contacto=telefono_contacto,
            fecha_hora_solicitada=fecha_hora_solicitada,
            fecha_hora_programada=fecha_hora_programada,
            precio_total=round(item.precio * cantidad_atendida, 2),
            payment_method_id=payment_method_id,
            observaciones=observaciones,
            pago_ids=[],
            factura_virtual=self._build_invoice(
                solicitar_factura_virtual, email_factura or cliente.correo_facturacion
            ),
            estado_pedido="pending",
        )
        item.cantidad_disponible -= cantidad_atendida
        self.db.orders[id_order] = order
        return order

    @is_tool(ToolType.WRITE)
    def update_order(
        self,
        id_order: str,
        cantidad_solicitada: Optional[int] = None,
        direccion_entrega: Optional[str] = None,
        persona_contacto: Optional[str] = None,
        telefono_contacto: Optional[str] = None,
        fecha_hora_programada: Optional[datetime.datetime] = None,
        observaciones: Optional[str] = None,
    ) -> Order:
        """Updates a pending order before delivery."""
        order = self._get_order(id_order)
        if order.estado_pedido != "pending":
            raise ValueError("Only pending orders can be updated")
        if order.pago_ids:
            raise ValueError("An order that already has registered payments cannot be updated")

        cliente = self._get_cliente(order.id_cliente)
        item = self._get_item(order.id_item)
        if item.tipo_producto == "lubricante":
            if order.id_order_combustible_asociado is None:
                raise ValueError(
                    "A lubricant order must keep an associated fuel order"
                )
            self._validate_linked_fuel_order(
                order.id_cliente, order.id_order_combustible_asociado
            )

        now = self._get_now()
        nueva_cantidad = (
            cantidad_solicitada
            if cantidad_solicitada is not None
            else order.cantidad_solicitada
        )

        stock_total_disponible = item.cantidad_disponible + order.cantidad_atendida
        nueva_cantidad_atendida = min(nueva_cantidad, stock_total_disponible)

        if nueva_cantidad_atendida < nueva_cantidad:
            raise ValueError("There is not enough stock to fulfill the complete order")

        item.cantidad_disponible = stock_total_disponible - nueva_cantidad_atendida
        order.cantidad_solicitada = nueva_cantidad
        order.cantidad_atendida = nueva_cantidad_atendida
        order.precio_total = round(
            order.precio_unitario_snapshot * order.cantidad_atendida, 2
        )

        if direccion_entrega is not None:
            if direccion_entrega not in cliente.direcciones_entrega:
                raise ValueError(
                    "The delivery address is not authorized for the customer"
                )
            order.direccion_entrega = direccion_entrega
        if persona_contacto is not None:
            order.persona_contacto = persona_contacto
        if telefono_contacto is not None:
            order.telefono_contacto = telefono_contacto
        if fecha_hora_programada is not None:
            if fecha_hora_programada < now + datetime.timedelta(hours=12):
                raise ValueError(
                    "The new scheduled date must have at least 12 hours of advance notice"
                )
            order.fecha_hora_programada = fecha_hora_programada
        if observaciones is not None:
            order.observaciones = observaciones

        return Order.model_validate(order.model_dump())

    @is_tool(ToolType.WRITE)
    def reschedule_order(
        self, id_order: str, nueva_fecha_hora_programada: datetime.datetime
    ) -> Order:
        """Reschedules the delivery date and time of a pending order."""
        order = self._get_order(id_order)
        if order.estado_pedido != "pending":
            raise ValueError("Only pending orders can be rescheduled")
        if order.fecha_hora_programada - self._get_now() < datetime.timedelta(hours=12):
            raise ValueError(
                "The order can only be rescheduled up to 12 hours before the scheduled delivery time"
            )
        if nueva_fecha_hora_programada < self._get_now() + datetime.timedelta(hours=12):
            raise ValueError(
                "The new scheduled date must have at least 12 hours of advance notice"
            )
        order.fecha_hora_programada = nueva_fecha_hora_programada
        return Order.model_validate(order.model_dump())

    @is_tool(ToolType.WRITE)
    def cancel_order(self, id_order: str, motivo: str) -> Order:
        """Cancels a pending order and restores the reserved stock."""
        order = self._get_order(id_order)
        if order.estado_pedido != "pending":
            raise ValueError("Only pending orders can be cancelled")
        if order.fecha_hora_programada - self._get_now() < datetime.timedelta(hours=12):
            raise ValueError(
                "The order can only be cancelled up to 12 hours before the scheduled delivery time"
            )

        item = self._get_item(order.id_item)
        item.cantidad_disponible += order.cantidad_atendida
        order.cantidad_atendida = 0
        order.precio_total = 0
        order.estado_pago = "pending"
        order.fecha_hora_cancelacion = self._get_now()
        order.motivo_cancelacion = motivo
        order.observaciones = (
            f"{order.observaciones} | Cancellation reason: {motivo}"
            if order.observaciones
            else f"Cancellation reason: {motivo}"
        )
        order.estado_pedido = "cancelled"
        return Order.model_validate(order.model_dump())

    @is_tool(ToolType.READ)
    def get_order_status(self, id_order: str) -> OrderStatusInfo:
        """Checks the operational status of a registered order."""
        order = self._get_order(id_order)
        return OrderStatusInfo(
            id_order=order.id_order,
            estado_pedido=order.estado_pedido,
            cantidad_solicitada=order.cantidad_solicitada,
            cantidad_atendida=order.cantidad_atendida,
            fecha_hora_programada=order.fecha_hora_programada,
            fecha_hora_entrega_real=order.fecha_hora_entrega_real,
        )

    @is_tool(ToolType.READ)
    def get_payment_status(self, id_order: str) -> PaymentStatusInfo:
        """Checks the payment status of an order."""
        order = self._get_order(id_order)
        self._refresh_order_payment_status(order)
        total_pagado = self._get_total_pagado(order)
        return PaymentStatusInfo(
            id_order=id_order,
            estado_pago=order.estado_pago,
            total_pagado=total_pagado,
            saldo_pendiente=round(order.precio_total - total_pagado, 2),
            payment_method_id=self._get_order_payment_method_id(order),
        )

    @is_tool(ToolType.WRITE)
    def register_claim(
        self,
        id_cliente: str,
        motivo: str,
        descripcion: str,
        id_order: Optional[str] = None,
    ) -> Claim:
        """Registers a claim associated with a customer and optionally an order."""
        self._get_cliente(id_cliente)
        if id_order is not None:
            self._get_order(id_order)

        id_reclamacion = self._generate_id(
            "reclamacion", set(self.db.reclamaciones.keys())
        )
        motivo_normalizado = self._normalize_claim_reason(motivo)
        descripcion_normalizada = self._normalize_claim_description(
            descripcion, id_order=id_order
        )
        reclamacion = Claim(
            id_reclamacion=id_reclamacion,
            id_cliente=id_cliente,
            id_order=id_order,
            motivo=motivo_normalizado,
            descripcion=descripcion_normalizada,
            fecha_reclamacion=self._next_event_timestamp(),
            estado_reclamacion="registered",
        )
        self.db.reclamaciones[id_reclamacion] = reclamacion
        return reclamacion

    @is_tool(ToolType.READ)
    def get_claim_details(self, id_reclamacion: str) -> Claim:
        """Gets the details of a claim."""
        return self._get_claim(id_reclamacion)

    @is_tool(ToolType.READ)
    def get_claims_by_client(self, id_cliente: str) -> List[Claim]:
        """Lists the claims registered for a customer."""
        self._get_cliente(id_cliente)
        return [
            claim
            for claim in self.db.reclamaciones.values()
            if claim.id_cliente == id_cliente
        ]

    @is_tool(ToolType.WRITE)
    def update_claim_status(
        self, id_reclamacion: str, estado_reclamacion: str
    ) -> Claim:
        """Updates the status of a claim."""
        claim = self._get_claim(id_reclamacion)
        valid_statuses = {"registered", "in_progress", "resolved", "cancelled"}
        if estado_reclamacion not in valid_statuses:
            raise ValueError("The claim status is invalid")
        claim.estado_reclamacion = estado_reclamacion
        return Claim.model_validate(claim.model_dump())

    @is_tool(ToolType.WRITE)
    def emit_virtual_invoice(
        self, id_order: str, email_envio: Optional[str] = None
    ) -> InvoiceEmissionResult:
        """Issues or updates the virtual invoice of an order."""
        order = self._get_order(id_order)
        cliente = self._get_cliente(order.id_cliente)

        destino = email_envio or order.factura_virtual.email_envio or cliente.correo_facturacion or cliente.email
        invoice_id = self._generate_id("factura", {order.factura_virtual.invoice_id} - {None})
        order.factura_virtual = VirtualInvoice(
            invoice_id=invoice_id,
            email_envio=destino,
            estado_factura="sent",
        )
        return InvoiceEmissionResult(
            id_order=id_order, factura_virtual=order.factura_virtual
        )

    @is_tool(ToolType.WRITE)
    def mark_order_delivered(
        self,
        id_order: str,
        comprobante_entrega: str,
        placa_unidad: Optional[str] = None,
    ) -> Order:
        """Marks a pending order as delivered and records the delivery proof."""
        order = self._get_order(id_order)
        if order.estado_pedido != "pending":
            raise ValueError("Only pending orders can be marked as delivered")
        order.comprobante_entrega = comprobante_entrega
        if placa_unidad is not None:
            order.placa_unidad = placa_unidad
        order.fecha_hora_entrega_real = self._get_now()
        order.estado_pedido = "delivered"
        return Order.model_validate(order.model_dump())

    @is_tool(ToolType.WRITE)
    def make_payment(
        self, id_order: str, payment_method_id: str, monto: float
    ) -> PaymentResult:
        """Registers a payment for an order using bank transfer, cash, or customer credit."""
        order = self._get_order(id_order)
        payment_method = self._get_payment_method(payment_method_id)
        if not isinstance(payment_method, (BankTransfer, Cash, CustomerCredit)):
            raise ValueError("The payment method is not valid for this domain")

        total_pagado_actual = self._get_total_pagado(order)
        saldo_pendiente = round(order.precio_total - total_pagado_actual, 2)
        if saldo_pendiente <= 0:
            raise ValueError("The order is already fully paid")
        if order.payment_method_id != payment_method_id:
            raise ValueError(
                "The payment must be made with the payment method selected for the order"
            )
        if order.pago_ids:
            raise ValueError("The order must be paid in a single transaction")
        if monto != saldo_pendiente:
            raise ValueError(
                "The payment must cover the full pending amount in a single transaction"
            )

        id_pago = self._generate_id("pago", set(self.db.pagos.keys()))
        pago = Payment(
            id_pago=id_pago,
            id_order=id_order,
            monto=monto,
            fecha_pago=self._next_event_timestamp(),
            payment_method_id=payment_method_id,
            estado_pago="paid",
        )
        self.db.pagos[id_pago] = pago
        order.pago_ids.append(id_pago)

        total_pagado = self._get_total_pagado(order)
        self._refresh_order_payment_status(order)
        return PaymentResult(
            pago=pago,
            total_pagado=total_pagado,
            saldo_pendiente=round(order.precio_total - total_pagado, 2),
        )

    @is_tool(ToolType.GENERIC)
    def transfer_to_human_agents(self, summary: str) -> str:
        """Transfers the case to a human agent when requested or when tools are insufficient."""
        return "Transfer successful"

