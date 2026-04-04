import datetime
from typing import Dict, List, Literal, Union

from pydantic import BaseModel, Field, model_validator

from tau2.environment.db import DB

MINIMO_GALONES_PEDIDO = 250
ItemUnit = Literal["galones", "litros", "unidad", "balde", "paquete", "botella"]

OrderStatus = Literal[
    "pending",
    "delivered",
    "cancelled",
]

InvoiceStatus = Literal["pending", "sent", "not_requested"]
PaymentStatus = Literal["pending", "paid", "failed"]
ComplaintStatus = Literal["registered", "in_progress", "resolved", "cancelled"]
OrderPaymentStatus = Literal["pending", "paid"]


class Item(BaseModel):
    """Represents a product available for delivery order."""

    id_item: str = Field(description="Unique item identifier")
    nombre_producto: str = Field(description="Product name")
    tipo_producto: str = Field(description="Product type")
    unidad_medida: ItemUnit = Field(
        description="Unit of measure in which the product is sold"
    )
    precio: float = Field(description="Unit price of the product")
    cantidad_disponible: int = Field(description="Available stock quantity")

    @property
    def disponible(self) -> bool:
        return self.cantidad_disponible > 0

    @model_validator(mode="after")
    def validate_item(self) -> "Item":
        if self.precio <= 0:
            raise ValueError("Item price must be greater than zero")
        if self.cantidad_disponible < 0:
            raise ValueError("Available quantity cannot be negative")
        if self.tipo_producto == "lubricante" and self.unidad_medida != "unidad":
            raise ValueError("Lubricants must use 'unidad' as their unit of measure")
        if self.tipo_producto == "combustible" and self.unidad_medida != "galones":
            raise ValueError("Fuel products must use 'galones' as their unit of measure")
        return self


class Customer(BaseModel):
    """Represents a customer registered in the fuel station system."""

    id_cliente: str = Field(description="Unique customer identifier")
    nombre_contacto: str = Field(description="Primary customer contact name")
    razon_social: str = Field(description="Customer company legal name")
    ruc: str = Field(description="Customer company RUC")
    telefono: str = Field(description="Customer contact phone number")
    email: str = Field(description="Customer email address")
    direccion_fiscal: str = Field(description="Customer company tax address")
    direcciones_entrega: List[str] = Field(
        default_factory=list,
        description="List of authorized delivery addresses",
    )
    correo_facturacion: str | None = Field(
        default=None,
        description="Email address used for invoicing",
    )

    @model_validator(mode="after")
    def validate_delivery_addresses(self) -> "Customer":
        if not self.direcciones_entrega:
            self.direcciones_entrega = [self.direccion_fiscal]
        return self


class PaymentMethodBase(BaseModel):
    """Represents a payment method available for fuel station orders."""

    id: str = Field(description="Unique payment method identifier")
    source: str = Field(description="Payment method type")


class Credit(PaymentMethodBase):
    """Credit payment method."""

    source: Literal["credit"] = Field(
        description="Indicates that the payment method is credit"
    )
    brand: str = Field(description="Credit method brand")
    last_four: str = Field(description="Last four digits of the credit method")


class BankTransfer(PaymentMethodBase):
    """Bank transfer payment method."""

    source: Literal["bank_transfer"] = Field(
        description="Indicates that the payment method is bank transfer"
    )
    bank_name: str = Field(description="Origin bank name")
    account_reference: str = Field(
        description="Reference or account number associated with the transfer"
    )


class Cash(PaymentMethodBase):
    """Cash payment method."""

    source: Literal["cash"] = Field(
        description="Indicates that the payment method is cash"
    )


PaymentMethod = Union[Credit, BankTransfer, Cash]


class VirtualInvoice(BaseModel):
    """Represents the virtual invoice information associated with an order."""

    invoice_id: str | None = Field(
        default=None, description="Unique virtual invoice identifier"
    )
    email_envio: str | None = Field(
        default=None,
        description="Email address to which the virtual invoice will be sent",
    )
    estado_factura: InvoiceStatus = Field(description="Current virtual invoice status")

    @model_validator(mode="after")
    def validate_invoice_fields(self) -> "VirtualInvoice":
        if self.estado_factura == "not_requested":
            self.invoice_id = None
            self.email_envio = None
        elif self.email_envio is None:
            raise ValueError("email_envio is required when a virtual invoice is requested")
        return self


class Payment(BaseModel):
    """Represents a payment made for an order."""

    id_pago: str = Field(description="Unique payment identifier")
    id_order: str = Field(description="Identifier of the order associated with the payment")
    monto: float = Field(description="Amount paid")
    fecha_pago: datetime.datetime = Field(
        description="Payment date and time in YYYY-MM-DDTHH:MM:SS format"
    )
    payment_method_id: str = Field(
        description="Identifier of the payment method used"
    )
    estado_pago: PaymentStatus = Field(description="Current payment status")

    @model_validator(mode="after")
    def validate_payment(self) -> "Payment":
        if self.monto <= 0:
            raise ValueError("Payment amount must be greater than zero")
        return self


class Claim(BaseModel):
    """Represents a claim registered by a customer."""

    id_reclamacion: str = Field(description="Unique claim identifier")
    id_cliente: str = Field(description="Customer identifier")
    id_order: str | None = Field(
        default=None, description="Identifier of the related order"
    )
    motivo: str = Field(description="Main reason for the claim")
    descripcion: str = Field(description="Detailed claim description")
    fecha_reclamacion: datetime.datetime = Field(
        description="Claim registration date and time in YYYY-MM-DDTHH:MM:SS format"
    )
    estado_reclamacion: ComplaintStatus = Field(description="Current claim status")


class Order(BaseModel):
    """Represents an order placed with the fuel station."""

    id_order: str = Field(description="Unique order identifier")
    id_cliente: str = Field(description="Identifier of the customer placing the order")
    id_order_combustible_asociado: str | None = Field(
        default=None,
        description="Associated fuel order when the order depends on a minimum fuel purchase",
    )
    id_item: str = Field(description="Identifier of the requested item")
    nombre_producto_snapshot: str = Field(
        description="Product name at the time the order is created"
    )
    tipo_producto_snapshot: str = Field(
        description="Product type at the time the order is created"
    )
    unidad_medida: ItemUnit = Field(description="Order unit of measure")
    precio_unitario_snapshot: float = Field(
        description="Product unit price at the time the order is created"
    )
    cantidad_solicitada: int = Field(
        description="Total requested quantity in the product unit of measure"
    )
    cantidad_atendida: int = Field(
        description="Fulfilled quantity in the product unit of measure"
    )
    minimo_galones: int = Field(
        default=MINIMO_GALONES_PEDIDO,
        description="Minimum allowed quantity to register an order in gallons",
    )
    direccion_entrega: str = Field(description="Exact order delivery address")
    persona_contacto: str = Field(
        description="Name of the delivery contact person"
    )
    telefono_contacto: str = Field(
        description="Phone number of the delivery contact person"
    )
    fecha_hora_solicitada: datetime.datetime = Field(
        description="Requested delivery date and time in YYYY-MM-DDTHH:MM:SS format"
    )
    fecha_hora_programada: datetime.datetime = Field(
        description="Scheduled delivery date and time in YYYY-MM-DDTHH:MM:SS format"
    )
    fecha_hora_entrega_real: datetime.datetime | None = Field(
        default=None,
        description="Actual delivery date and time in YYYY-MM-DDTHH:MM:SS format",
    )
    precio_total: float = Field(description="Total order price")
    payment_method_id: str = Field(
        description="Selected payment method for the order"
    )
    estado_pago: OrderPaymentStatus = Field(
        default="pending",
        description="Aggregated payment status of the order",
    )
    comprobante_entrega: str | None = Field(
        default=None, description="Delivery proof number or reference"
    )
    placa_unidad: str | None = Field(
        default=None, description="License plate of the unit assigned for delivery"
    )
    fecha_hora_cancelacion: datetime.datetime | None = Field(
        default=None,
        description="Order cancellation date and time in YYYY-MM-DDTHH:MM:SS format",
    )
    motivo_cancelacion: str | None = Field(
        default=None, description="Recorded reason for order cancellation"
    )
    observaciones: str | None = Field(
        default=None, description="Additional order notes"
    )
    pago_ids: List[str] = Field(
        default_factory=list, description="List of payment identifiers for the order"
    )
    factura_virtual: VirtualInvoice = Field(
        description="Information associated with the virtual invoice for the order"
    )
    estado_pedido: OrderStatus = Field(description="Current order status")

    @model_validator(mode="after")
    def validate_order(self) -> "Order":
        if self.tipo_producto_snapshot == "lubricante" and self.unidad_medida != "unidad":
            raise ValueError("Lubricant orders must use 'unidad' as their unit of measure")
        if self.tipo_producto_snapshot == "combustible" and self.unidad_medida != "galones":
            raise ValueError("Fuel orders must use 'galones' as their unit of measure")
        if (
            self.tipo_producto_snapshot == "combustible"
            and self.unidad_medida == "galones"
            and self.cantidad_solicitada < self.minimo_galones
        ):
            raise ValueError(
                f"Requested quantity must be at least {self.minimo_galones} gallons"
            )
        if (
            self.unidad_medida == "galones"
            and self.tipo_producto_snapshot != "combustible"
            and self.id_order_combustible_asociado is None
        ):
            raise ValueError(
                "Non-fuel products measured in gallons must have an associated fuel order"
            )
        if self.precio_unitario_snapshot <= 0:
            raise ValueError("Order unit price must be greater than zero")
        if self.precio_total < 0:
            raise ValueError("Order total price cannot be negative")
        if self.cantidad_solicitada <= 0:
            raise ValueError("Requested quantity must be greater than zero")
        if self.cantidad_atendida < 0:
            raise ValueError("Fulfilled quantity cannot be negative")
        if self.cantidad_atendida > self.cantidad_solicitada:
            raise ValueError("Fulfilled quantity cannot be greater than requested quantity")
        if self.fecha_hora_programada < self.fecha_hora_solicitada:
            raise ValueError("Scheduled date and time cannot be earlier than the requested one")
        if (
            self.estado_pedido != "cancelled"
            and self.cantidad_atendida < self.cantidad_solicitada
        ):
            raise ValueError("Partial deliveries are not allowed")
        if self.estado_pedido == "cancelled" and self.cantidad_atendida > 0:
            raise ValueError("A cancelled order must not keep a fulfilled quantity")
        if self.estado_pedido == "delivered" and self.fecha_hora_entrega_real is None:
            raise ValueError("fecha_hora_entrega_real is required when the order is delivered")
        if (
            self.fecha_hora_entrega_real is not None
            and self.fecha_hora_entrega_real < self.fecha_hora_programada
        ):
            raise ValueError("Actual delivery date and time cannot be earlier than the scheduled one")
        return self


class FuelStationDB(DB):
    """Database for the fuel station delivery-order domain."""

    clientes: Dict[str, Customer] = Field(
        default_factory=dict,
        description="Dictionary of customers indexed by id_cliente",
    )
    items: Dict[str, Item] = Field(
        default_factory=dict,
        description="Dictionary of available products indexed by id_item",
    )
    payment_methods: Dict[str, PaymentMethod] = Field(
        default_factory=dict,
        description="Dictionary of payment methods indexed by identifier",
    )
    pagos: Dict[str, Payment] = Field(
        default_factory=dict,
        description="Dictionary of payments indexed by id_pago",
    )
    reclamaciones: Dict[str, Claim] = Field(
        default_factory=dict,
        description="Dictionary of claims indexed by id_reclamacion",
    )
    orders: Dict[str, Order] = Field(
        default_factory=dict,
        description="Dictionary of registered orders indexed by id_order",
    )


# Backward-compatible aliases for the rest of the project.
Cliente = Customer
Pago = Payment
Reclamacion = Claim
GrifoDB = FuelStationDB

