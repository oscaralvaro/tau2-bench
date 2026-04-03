from datetime import date
from typing import Any, List

from tau2.domains.ecommerce_zulemalopez.data_model import EcommerceDB, Order, OrderItem
from tau2.environment.toolkit import ToolKitBase, ToolType, is_tool


class EcommerceTools(ToolKitBase):
    db: EcommerceDB

    def __init__(self, db: EcommerceDB) -> None:
        super().__init__(db)

    def _get_user(self, user_id: str):
        if user_id not in self.db.users:
            raise ValueError("User not found")
        return self.db.users[user_id]

    def _get_order(self, order_id: str):
        if order_id not in self.db.orders:
            raise ValueError("Order not found")
        return self.db.orders[order_id]

    def _get_product(self, product_id: str):
        if product_id not in self.db.products:
            raise ValueError("Product not found")
        return self.db.products[product_id]

    @is_tool(ToolType.READ)
    def find_user_id_by_email(self, email: str) -> str:
        """Find a user id by email."""
        for user_id, user in self.db.users.items():
            if user.email.lower() == email.lower():
                return user_id
        raise ValueError("User not found")

    @is_tool(ToolType.READ)
    def get_user_details(self, user_id: str):
        """Get user profile details."""
        return self._get_user(user_id)

    @is_tool(ToolType.READ)
    def get_order_details(self, order_id: str):
        """Get complete order details."""
        return self._get_order(order_id)

    @is_tool(ToolType.READ)
    def list_products(self):
        """List all products available in the catalog."""
        return list(self.db.products.values())

    @is_tool(ToolType.READ)
    def list_available_models(self) -> list[dict[str, Any]]:
        """List sneaker models that still have stock in at least one size."""
        models = []
        for product in self.db.products.values():
            available_sizes = [
                int(size)
                for size, stock in product.stock_by_size.items()
                if stock > 0
            ]
            if not available_sizes:
                continue
            models.append(
                {
                    "product_id": product.product_id,
                    "model": product.name,
                    "brand": product.brand,
                    "category": product.category,
                    "price": product.price,
                    "available_sizes": sorted(available_sizes),
                }
            )
        return models

    @is_tool(ToolType.READ)
    def get_product_sizes(self, product_id: str) -> List[int]:
        """Get available sizes for one product."""
        product = self._get_product(product_id)
        return product.sizes

    @is_tool(ToolType.WRITE)
    def add_user_preferred_size(self, user_id: str, size: int):
        """Save one preferred sneaker size to a user profile."""
        if size < 30 or size > 55:
            raise ValueError("Invalid sneaker size")
        user = self._get_user(user_id)
        if size not in user.preferred_sizes:
            user.preferred_sizes.append(size)
            user.preferred_sizes.sort()
        return user

    @is_tool(ToolType.WRITE)
    def add_user_address(self, user_id: str, address: str, set_default: bool = True):
        """Add a new saved address for the user and optionally set as default."""
        user = self._get_user(user_id)
        if address not in user.saved_addresses:
            user.saved_addresses.append(address)
        if set_default:
            user.address = address
        return user

    @is_tool(ToolType.WRITE)
    def create_order(
        self, user_id: str, product_id: str, size: int, quantity: int, address: str
    ) -> Order:
        """Create a new pending order."""
        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero")

        self._get_user(user_id)
        product = self._get_product(product_id)

        if size not in product.sizes:
            raise ValueError("Requested size is not available")

        size_key = str(size)
        available_stock = product.stock_by_size.get(size_key, 0)
        if available_stock < quantity:
            raise ValueError("Insufficient stock for requested size")

        product.stock_by_size[size_key] -= quantity

        order_id = str(self.db.next_order_id)
        self.db.next_order_id += 1
        order = Order(
            order_id=order_id,
            user_id=user_id,
            items=[
                OrderItem(
                    product_id=product_id,
                    size=size,
                    quantity=quantity,
                    unit_price=product.price,
                )
            ],
            shipping_address=address,
            status="pending",
            created_at=self.db.current_date,
            total_amount=round(quantity * product.price, 2),
        )
        self.db.orders[order_id] = order
        return order

    @is_tool(ToolType.WRITE)
    def cancel_order(self, order_id: str, reason: str) -> Order:
        """Cancel an order if it is still pending or paid."""
        order = self._get_order(order_id)
        if order.status not in {"pending", "paid"}:
            raise ValueError("Only pending or paid orders can be cancelled")
        order.status = "cancelled"
        order.cancellation_reason = reason
        return order

    @is_tool(ToolType.WRITE)
    def update_order_address(self, order_id: str, new_address: str) -> Order:
        """Update shipping address only before shipment."""
        order = self._get_order(order_id)
        if order.status not in {"pending", "paid"}:
            raise ValueError("Address can only be updated before shipment")
        order.shipping_address = new_address
        return order

    @is_tool(ToolType.WRITE)
    def request_return(self, order_id: str, reason: str) -> Order:
        """Request return for delivered orders within 30 days if item is returnable."""
        order = self._get_order(order_id)
        if order.status != "delivered":
            raise ValueError("Only delivered orders can request return")
        if order.delivered_at is None:
            raise ValueError("Missing delivery date")

        delivered_at = date.fromisoformat(order.delivered_at)
        current_date = date.fromisoformat(self.db.current_date)
        if (current_date - delivered_at).days > 30:
            raise ValueError("Return window expired")

        for item in order.items:
            product = self._get_product(item.product_id)
            if not product.returnable:
                raise ValueError("This order contains non-returnable items")

        order.status = "return_requested"
        order.return_reason = reason
        return order

    @is_tool(ToolType.GENERIC)
    def transfer_to_human_agents(self, summary: str) -> str:
        """Transfer the customer to a human support agent."""
        return "Transfer successful"
