from pydantic import BaseModel
from typing import List, Optional


class UserOrderSummary(BaseModel):
    """Vista simplificada de un pedido desde la perspectiva del usuario."""
    order_id: str
    date: str
    status: str
    total: float
    items: List[str]


class UserProfile(BaseModel):
    """Informacion que el usuario conoce sobre si mismo."""
    user_id: str
    name: str
    email: str
    customer_type: str
    orders: List[UserOrderSummary] = []