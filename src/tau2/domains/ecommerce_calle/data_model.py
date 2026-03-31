from typing import Dict, List
from enum import Enum
from pydantic import BaseModel
from tau2.environment.db import DB


class OrderStatus(str, Enum):
    pending_payment = "pending_payment"
    processing = "processing"
    shipped = "shipped"
    out_for_delivery = "out_for_delivery"
    delivered = "delivered"
    cancelled = "cancelled"
    returned = "returned"


class CustomerType(str, Enum):
    regular = "regular"
    premium = "premium"


class AccountStatus(str, Enum):
    active = "active"
    blocked = "blocked"


class User(BaseModel):
    user_id: str
    name: str
    email: str
    address: str
    customer_type: CustomerType
    status: AccountStatus


class Product(BaseModel):
    product_id: str
    name: str
    category: str
    price: float
    return_allowed: bool


class Shipment(BaseModel):
    shipment_id: str
    order_id: str
    tracking_number: str
    shipment_status: str
    estimated_delivery: str


class Return(BaseModel):
    return_id: str
    order_id: str
    reason: str
    status: str
    approved: bool


class Order(BaseModel):
    order_id: str
    user_id: str
    date: str
    status: OrderStatus
    total: float
    shipping_address: str
    items: List[str]


class EcommerceDB(DB):
    users: Dict[str, User] = {}
    products: Dict[str, Product] = {}
    orders: Dict[str, Order] = {}
    shipments: Dict[str, Shipment] = {}
    returns: Dict[str, Return] = {}
    