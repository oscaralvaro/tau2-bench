import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import AliasChoices, Field, model_validator

from tau2.environment.db import DB
from tau2.utils.pydantic_utils import BaseModelNoExtra

try:
    from tau2.domains.fishtrader_garbich.utils import FISHTRADER_GARBICH_DB_PATH
except ImportError:  # pragma: no cover - allows incremental domain scaffolding
    FISHTRADER_GARBICH_DB_PATH = None


class Address(BaseModelNoExtra):
    street: str = Field(description="Primary street address")
    district: Optional[str] = Field(None, description="District or neighborhood")
    city: str = Field(description="City name")
    state: Optional[str] = Field(None, description="State or region")
    country: str = Field(description="Country name")
    postal_code: Optional[str] = Field(None, description="Postal code")


class ContactPerson(BaseModelNoExtra):
    full_name: str = Field(description="Full name of the business contact")
    role: Optional[str] = Field(None, description="Job title or role")
    email: str = Field(description="Email address of the contact")
    phone: str = Field(description="Phone number of the contact")


class Incoterm(str, Enum):
    EXW = "EXW"
    FCA = "FCA"
    FOB = "FOB"
    CFR = "CFR"
    CIF = "CIF"
    CPT = "CPT"
    CIP = "CIP"
    DAP = "DAP"
    DDP = "DDP"


class PaymentMethodType(str, Enum):
    BANK_TRANSFER = "bank_transfer"
    LETTER_OF_CREDIT = "letter_of_credit"
    CASH_AGAINST_DOCUMENTS = "cash_against_documents"
    OPEN_ACCOUNT = "open_account"
    ADVANCE_PAYMENT = "advance_payment"


class CustomerStatus(str, Enum):
    ACTIVE = "active"
    CREDIT_HOLD = "credit_hold"
    INACTIVE = "inactive"


class SupplierStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    BLOCKED = "blocked"


class ProductStatus(str, Enum):
    ACTIVE = "active"
    DISCONTINUED = "discontinued"
    OUT_OF_STOCK = "out_of_stock"


class InventoryStatus(str, Enum):
    AVAILABLE = "available"
    RESERVED = "reserved"
    QUARANTINED = "quarantined"
    EXHAUSTED = "exhausted"


class OrderStatus(str, Enum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    PARTIALLY_ALLOCATED = "partially_allocated"
    READY_TO_SHIP = "ready_to_ship"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    ISSUED = "issued"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class ClaimStatus(str, Enum):
    OPEN = "open"
    IN_REVIEW = "in_review"
    RESOLVED = "resolved"
    REJECTED = "rejected"


class ShipmentStatus(str, Enum):
    PENDING = "pending"
    BOOKED = "booked"
    IN_TRANSIT = "in_transit"
    ARRIVED = "arrived"
    DELIVERED = "delivered"
    DELAYED = "delayed"
    CANCELLED = "cancelled"


class CompanyCustomer(BaseModelNoExtra):
    customer_id: str = Field(description="Unique identifier for the customer company")
    legal_name: str = Field(description="Registered legal name of the customer")
    trade_name: Optional[str] = Field(
        None, description="Commercial or trade name used by the customer"
    )
    ruc: str = Field(description="Tax identification number (RUC) of the customer")
    address: Address = Field(description="Main billing address of the customer")
    shipping_address: Optional[Address] = Field(
        None, description="Default shipping address for orders"
    )
    incoterm: Incoterm = Field(description="Default agreed Incoterm with the customer")
    payment_method: PaymentMethodType = Field(
        description="Default payment method used by the customer"
    )
    payment_terms_days: int = Field(
        description="Number of calendar days granted for payment"
    )
    shipping_lead_time_days: int = Field(
        description="Typical shipping lead time agreed with the customer"
    )
    default_currency: str = Field(
        description="Preferred transaction currency, e.g. USD, EUR, PEN"
    )
    contact_persons: List[ContactPerson] = Field(
        default_factory=list, description="Business contacts for this customer"
    )
    preferred_destination_port: Optional[str] = Field(
        None, description="Preferred port or delivery destination"
    )
    credit_limit: Optional[float] = Field(
        None, description="Maximum credit line allowed for the customer"
    )
    status: CustomerStatus = Field(
        CustomerStatus.ACTIVE, description="Current commercial status"
    )
    notes: Optional[str] = Field(None, description="Internal commercial notes")
    order_ids: List[str] = Field(
        default_factory=list, description="Orders placed by this customer"
    )
    invoice_ids: List[str] = Field(
        default_factory=list, description="Invoices issued to this customer"
    )


class Supplier(BaseModelNoExtra):
    supplier_id: str = Field(description="Unique identifier for the supplier")
    legal_name: str = Field(description="Registered legal name of the supplier")
    trade_name: Optional[str] = Field(
        None, description="Commercial or trade name of the supplier"
    )
    tax_id: Optional[str] = Field(
        None, description="Tax identification number of the supplier"
    )
    address: Address = Field(description="Supplier address")
    contact_persons: List[ContactPerson] = Field(
        default_factory=list, description="Main contacts for the supplier"
    )
    origin_country: str = Field(description="Country where the supplier operates")
    payment_method: Optional[PaymentMethodType] = Field(
        None, description="Preferred payment method used with this supplier"
    )
    lead_time_days: Optional[int] = Field(
        None, description="Typical procurement lead time from the supplier"
    )
    status: SupplierStatus = Field(
        SupplierStatus.ACTIVE, description="Current supplier status"
    )
    notes: Optional[str] = Field(None, description="Internal supplier notes")


class FishProduct(BaseModelNoExtra):
    product_id: str = Field(description="Unique identifier for the fish product")
    name: str = Field(description="Commercial name of the product")
    description: str = Field(
        description="Written technical description of the product"
    )
    species: Optional[str] = Field(
        None, description="Biological or commercial fish species"
    )
    presentation: Optional[str] = Field(
        None, description="Commercial presentation, e.g. fillet, whole, frozen"
    )
    unit_of_measure: str = Field(
        description="Commercial unit, e.g. kg, box, pallet, container"
    )
    price: float = Field(description="Standard selling price per unit")
    max_negotiable_price: float = Field(
        description="Minimum acceptable negotiated price per unit"
    )
    currency: str = Field(description="Currency of the product price")
    supplier_id: str = Field(description="Supplier that provides this product")
    origin_country: Optional[str] = Field(
        None, description="Country of origin of the fish product"
    )
    status: ProductStatus = Field(
        ProductStatus.ACTIVE, description="Current commercial availability status"
    )


class InventoryItem(BaseModelNoExtra):
    inventory_id: str = Field(description="Unique identifier for the inventory record")
    product_id: str = Field(description="Identifier of the stored product")
    warehouse_name: str = Field(description="Warehouse or cold storage location")
    quantity_available: float = Field(description="Currently available stock quantity")
    quantity_reserved: float = Field(description="Stock already reserved for orders")
    unit_of_measure: str = Field(description="Unit used for stock quantities")
    last_updated_at: datetime.datetime = Field(
        description="Last inventory update timestamp in ISO format"
    )
    status: InventoryStatus = Field(
        InventoryStatus.AVAILABLE, description="Operational inventory status"
    )


class OrderLineItem(BaseModelNoExtra):
    line_id: str = Field(description="Unique identifier for the order line")
    product_id: str = Field(description="Product included in the order")
    product_name: str = Field(description="Name of the product at order time")
    quantity: float = Field(description="Ordered quantity")
    unit_of_measure: str = Field(description="Unit used for the ordered quantity")
    unit_price: float = Field(description="Final unit price agreed for this line")
    subtotal: float = Field(description="Line subtotal before taxes or other charges")
    supplier_id: str = Field(description="Supplier associated with the ordered product")


class Order(BaseModelNoExtra):
    order_id: str = Field(description="Unique identifier for the sales order")
    customer_id: str = Field(description="Customer company that placed the order")
    issue_date: datetime.date = Field(
        description="Date the order was issued in YYYY-MM-DD format"
    )
    delivery_date: datetime.date = Field(
        description="Expected or committed delivery date in YYYY-MM-DD format"
    )
    incoterm: Incoterm = Field(description="Incoterm applied to this order")
    payment_method: PaymentMethodType = Field(
        description="Payment method agreed for this order"
    )
    currency: str = Field(description="Currency used in the order")
    shipping_address: Address = Field(description="Delivery destination for the order")
    items: List[OrderLineItem] = Field(
        default_factory=list, description="Products included in the order"
    )
    total_amount: float = Field(description="Total amount of the order")
    status: OrderStatus = Field(
        OrderStatus.DRAFT, description="Current operational order status"
    )
    notes: Optional[str] = Field(None, description="Internal or customer-facing notes")
    invoice_ids: List[str] = Field(
        default_factory=list, description="Invoices generated from this order"
    )
    shipment_ids: List[str] = Field(
        default_factory=list, description="Shipments associated with this order"
    )


class InvoiceLineItem(BaseModelNoExtra):
    line_id: str = Field(description="Unique identifier for the invoice line")
    product_id: str = Field(description="Product billed in this line")
    description: str = Field(description="Invoice line description")
    quantity: float = Field(description="Billed quantity")
    unit_of_measure: str = Field(description="Unit used in the invoice line")
    unit_price: float = Field(description="Unit price billed")
    subtotal: float = Field(description="Line subtotal")


class Invoice(BaseModelNoExtra):
    invoice_id: str = Field(description="Unique identifier for the invoice record")
    invoice_number: str = Field(
        description="Fiscal or commercial invoice number shown to the customer"
    )
    order_id: str = Field(description="Order associated with this invoice")
    customer_id: str = Field(description="Customer billed in this invoice")
    customer_legal_name: str = Field(
        description="Legal name of the billed customer at invoice time"
    )
    customer_ruc: str = Field(description="RUC of the billed customer")
    billing_address: Address = Field(description="Billing address shown on the invoice")
    issue_date: datetime.date = Field(
        description="Invoice issue date in YYYY-MM-DD format"
    )
    due_date: datetime.date = Field(description="Invoice due date in YYYY-MM-DD format")
    currency: str = Field(description="Invoice currency")
    payment_method: PaymentMethodType = Field(
        description="Payment method agreed for this invoice"
    )
    payment_terms_days: int = Field(
        description="Payment term in days used to compute the due date"
    )
    line_items: List[InvoiceLineItem] = Field(
        default_factory=list, description="Detailed billed items"
    )
    subtotal: float = Field(description="Subtotal before taxes")
    tax_amount: float = Field(description="Tax amount applied to the invoice")
    total_amount: float = Field(description="Final invoice total")
    paid_amount: float = Field(description="Accumulated amount paid so far")
    status: InvoiceStatus = Field(
        InvoiceStatus.DRAFT, description="Current financial status of the invoice"
    )
    issued_at: Optional[datetime.datetime] = Field(
        None, description="Timestamp when the invoice was officially issued"
    )
    paid_at: Optional[datetime.datetime] = Field(
        None, description="Timestamp when the invoice was fully paid"
    )
    payment_records: List["PaymentRecord"] = Field(
        default_factory=list, description="Payments applied to the invoice"
    )


class PaymentRecord(BaseModelNoExtra):
    payment_id: str = Field(description="Unique identifier for the payment")
    invoice_id: str = Field(description="Invoice paid with this record")
    amount: float = Field(description="Amount paid")
    payment_method: PaymentMethodType = Field(description="Payment method used")
    payment_date: datetime.datetime = Field(
        description="Payment timestamp in ISO format"
    )
    reference: Optional[str] = Field(
        None, description="Bank transfer, SWIFT, or transaction reference"
    )


class Claim(BaseModelNoExtra):
    claim_id: str = Field(description="Unique identifier for the claim")
    customer_id: str = Field(description="Customer who filed the claim")
    order_id: Optional[str] = Field(
        None, description="Order associated with the claim, if any"
    )
    invoice_id: Optional[str] = Field(
        None, description="Invoice associated with the claim, if any"
    )
    subject: str = Field(description="Short subject of the claim")
    description: str = Field(description="Detailed claim description")
    created_at: datetime.datetime = Field(
        description="Claim creation timestamp in ISO format"
    )
    status: ClaimStatus = Field(
        ClaimStatus.OPEN, description="Current status of the claim"
    )
    resolution_notes: Optional[str] = Field(
        None, description="Internal or final resolution notes"
    )


class Shipment(BaseModelNoExtra):
    shipment_id: str = Field(description="Unique identifier for the shipment")
    order_id: str = Field(description="Order associated with this shipment")
    customer_id: str = Field(description="Customer receiving the shipment")
    carrier_name: str = Field(
        description="Shipping line, carrier, or logistics operator name"
    )
    container_number: Optional[str] = Field(
        None, description="Container identifier if the shipment uses a container"
    )
    tracking_number: Optional[str] = Field(
        None, description="Tracking or booking reference for the shipment"
    )
    departure_port: str = Field(description="Port or location of departure")
    arrival_port: str = Field(description="Port or location of arrival")
    estimated_departure_date: Optional[datetime.date] = Field(
        None, description="Estimated departure date in YYYY-MM-DD format"
    )
    estimated_arrival_date: Optional[datetime.date] = Field(
        None, description="Estimated arrival date in YYYY-MM-DD format"
    )
    actual_departure_date: Optional[datetime.date] = Field(
        None, description="Actual departure date in YYYY-MM-DD format"
    )
    actual_arrival_date: Optional[datetime.date] = Field(
        None, description="Actual arrival date in YYYY-MM-DD format"
    )
    incoterm: Incoterm = Field(description="Incoterm applied to this shipment")
    status: ShipmentStatus = Field(
        ShipmentStatus.PENDING, description="Current logistics status"
    )
    notes: Optional[str] = Field(
        None, description="Operational notes about the shipment"
    )


class FishTraderDB(DB):
    """Database for the fish trading domain."""

    users: Dict[str, CompanyCustomer] = Field(
        default_factory=dict,
        description="Customer companies indexed by customer id",
        validation_alias=AliasChoices("users", "customers"),
    )
    suppliers: Dict[str, Supplier] = Field(
        default_factory=dict, description="Suppliers indexed by supplier id"
    )
    products: Dict[str, FishProduct] = Field(
        default_factory=dict, description="Products indexed by product id"
    )
    inventory: Dict[str, InventoryItem] = Field(
        default_factory=dict, description="Inventory records indexed by inventory id"
    )
    orders: Dict[str, Order] = Field(
        default_factory=dict, description="Sales orders indexed by order id"
    )
    invoices: Dict[str, Invoice] = Field(
        default_factory=dict, description="Invoices indexed by invoice id"
    )
    claims: Dict[str, Claim] = Field(
        default_factory=dict, description="Claims indexed by claim id"
    )
    shipments: Dict[str, Shipment] = Field(
        default_factory=dict, description="Shipments indexed by shipment id"
    )

    @model_validator(mode="before")
    @classmethod
    def _normalize_user_keys(cls, data: Any) -> Any:
        if isinstance(data, dict) and "users" not in data and "customers" in data:
            normalized = dict(data)
            normalized["users"] = normalized.pop("customers")
            return normalized
        return data

    @property
    def customers(self) -> Dict[str, CompanyCustomer]:
        return self.users

    @customers.setter
    def customers(self, value: Dict[str, CompanyCustomer]) -> None:
        self.users = value

    def get_statistics(self) -> Dict[str, Any]:
        return {
            "num_users": len(self.users),
            "num_customers": len(self.users),
            "num_suppliers": len(self.suppliers),
            "num_products": len(self.products),
            "num_inventory_records": len(self.inventory),
            "num_orders": len(self.orders),
            "num_invoices": len(self.invoices),
            "num_claims": len(self.claims),
            "num_shipments": len(self.shipments),
        }


def get_db():
    if FISHTRADER_GARBICH_DB_PATH is None:
        raise ValueError(
            "FISHTRADER_GARBICH_DB_PATH is not defined yet in fishtrader_garbich.utils"
        )
    return FishTraderDB.load(FISHTRADER_GARBICH_DB_PATH)
