from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

try:
    from tau2.domains.ecommerce_zulemalopez.utils import ECOMMERCE_DB_PATH
except ModuleNotFoundError:
    # Allow running this file directly with:
    # python src/tau2/domains/ecommerce_zulemalopez/data_model.py
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).resolve().parents[3]))
    from tau2.domains.ecommerce_zulemalopez.utils import ECOMMERCE_DB_PATH

from tau2.environment.db import DB

OrderStatus = Literal[
    "pending", "paid", "shipped", "delivered", "cancelled", "return_requested"
]


class User(BaseModel):
    user_id: str = Field(description="Unique user identifier")
    name: str = Field(description="Full name")
    email: str = Field(description="Email address")
    phone: str = Field(description="Phone number")
    address: str = Field(description="Default shipping address")
    saved_addresses: List[str] = Field(description="Saved addresses for quick checkout")
    preferred_sizes: List[int] = Field(
        description="Preferred sneaker sizes (EU scale)"
    )


class Product(BaseModel):
    product_id: str = Field(description="Unique product identifier")
    name: str = Field(description="Product name")
    brand: str = Field(description="Brand name")
    category: str = Field(description="Product category")
    price: float = Field(description="Unit price")
    sizes: List[int] = Field(description="Available sizes")
    stock_by_size: Dict[str, int] = Field(description="Stock by size")
    returnable: bool = Field(description="Whether the product can be returned")


class OrderItem(BaseModel):
    product_id: str = Field(description="Product identifier")
    size: int = Field(description="Product size")
    quantity: int = Field(description="Quantity")
    unit_price: float = Field(description="Unit price at purchase time")


class Order(BaseModel):
    order_id: str = Field(description="Unique order identifier")
    user_id: str = Field(description="Order owner")
    items: List[OrderItem] = Field(description="Items in the order")
    shipping_address: str = Field(description="Shipping destination")
    status: OrderStatus = Field(description="Order status")
    created_at: str = Field(description="Order creation date (YYYY-MM-DD)")
    delivered_at: Optional[str] = Field(
        default=None, description="Delivery date (YYYY-MM-DD)"
    )
    total_amount: float = Field(description="Order total amount")
    cancellation_reason: Optional[str] = Field(
        default=None, description="Cancellation reason"
    )
    return_reason: Optional[str] = Field(default=None, description="Return reason")


class EcommerceDB(DB):
    current_date: str = Field(
        description="Reference date used for deterministic policy checks"
    )
    users: Dict[str, User] = Field(description="Users indexed by user id")
    products: Dict[str, Product] = Field(description="Products indexed by product id")
    orders: Dict[str, Order] = Field(description="Orders indexed by order id")
    next_order_id: int = Field(description="Next numeric id for new orders")

    def get_statistics(self) -> dict[str, Any]:
        return {
            "num_users": len(self.users),
            "num_products": len(self.products),
            "num_orders": len(self.orders),
        }


def get_db() -> EcommerceDB:
    return EcommerceDB.load(ECOMMERCE_DB_PATH)
