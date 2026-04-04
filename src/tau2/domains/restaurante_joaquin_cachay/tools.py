from datetime import datetime
from typing import Dict, List, Optional

from tau2.domains.restaurante_joaquin_cachay.data_model import (
    Address,
    CardPayment,
    CashPayment,
    CustomerProfile,
    DeliveryInfo,
    DigitalWalletPayment,
    GiftCardPayment,
    MenuItem,
    MenuCategory,
    OrderItem,
    OrderItemStatus,
    Payment,
    Reservation,
    RestaurantInfo,
    RestaurantOrder,
    RestaurantTable,
    RestauranteJoaquinCachayDB,
    Review,
    SelectedModifier,
)
from tau2.environment.toolkit import ToolKitBase, ToolType, is_tool


class RestauranteJoaquinCachayTools(ToolKitBase):
    """Operational tools for the restaurant domain."""

    db: RestauranteJoaquinCachayDB

    def __init__(self, db: RestauranteJoaquinCachayDB) -> None:
        super().__init__(db)

    def _now(self) -> str:
        return datetime.now().isoformat(timespec="seconds")

    def _next_id(self, prefix: str, data: Dict[str, object]) -> str:
        return f"{prefix}-{len(data) + 1:03d}"

    def _get_customer(self, customer_id: str) -> CustomerProfile:
        if customer_id not in self.db.customers:
            raise ValueError(f"Customer '{customer_id}' not found")
        return self.db.customers[customer_id]

    def _get_reservation(self, reservation_id: str) -> Reservation:
        if reservation_id not in self.db.reservations:
            raise ValueError(f"Reservation '{reservation_id}' not found")
        return self.db.reservations[reservation_id]

    def _get_order(self, order_id: str) -> RestaurantOrder:
        if order_id not in self.db.orders:
            raise ValueError(f"Order '{order_id}' not found")
        return self.db.orders[order_id]

    def _get_table(self, table_id: str) -> RestaurantTable:
        if table_id not in self.db.tables:
            raise ValueError(f"Table '{table_id}' not found")
        return self.db.tables[table_id]

    def _get_menu_item(self, menu_item_id: str) -> MenuItem:
        if menu_item_id not in self.db.menu_items:
            raise ValueError(f"Menu item '{menu_item_id}' not found")
        return self.db.menu_items[menu_item_id]

    def _find_customer_by_phone(self, phone_number: str) -> Optional[CustomerProfile]:
        for customer in self.db.customers.values():
            if customer.phone_number == phone_number:
                return customer
        return None

    def _get_available_tables(
        self, party_size: int, area_id: Optional[str] = None
    ) -> list[RestaurantTable]:
        candidates = [
            table
            for table in self.db.tables.values()
            if table.status == "available"
            and table.capacity >= party_size
            and (area_id is None or table.area_id == area_id)
        ]
        if area_id is not None and not candidates:
            candidates = [
                table
                for table in self.db.tables.values()
                if table.status == "available" and table.capacity >= party_size
            ]
        return sorted(candidates, key=lambda table: (table.capacity, table.table_number))

    def _parse_selected_modifiers(
        self, modifiers: Optional[List[dict]]
    ) -> list[SelectedModifier]:
        parsed: list[SelectedModifier] = []
        for modifier in modifiers or []:
            group_id = modifier["modifier_group_id"]
            option_id = modifier["option_id"]
            if group_id not in self.db.modifier_groups:
                raise ValueError(f"Modifier group '{group_id}' not found")
            group = self.db.modifier_groups[group_id]
            if option_id not in group.options:
                raise ValueError(
                    f"Modifier option '{option_id}' not found in group '{group_id}'"
                )
            option = group.options[option_id]
            if not option.available:
                raise ValueError(f"Modifier option '{option.name}' is unavailable")
            parsed.append(
                SelectedModifier(
                    modifier_group_id=group_id,
                    option_id=option_id,
                    option_name=option.name,
                    price_delta=option.price_delta,
                )
            )
        return parsed

    def _build_order_item(
        self,
        order_item_id: str,
        menu_item_id: str,
        quantity: int,
        modifiers: Optional[List[dict]] = None,
        special_instructions: Optional[str] = None,
    ) -> OrderItem:
        if quantity < 1:
            raise ValueError("Quantity must be at least 1")
        menu_item = self._get_menu_item(menu_item_id)
        if not menu_item.available:
            raise ValueError(f"Menu item '{menu_item.name}' is currently unavailable")
        selected_modifiers = self._parse_selected_modifiers(modifiers)
        modifier_total = sum(modifier.price_delta for modifier in selected_modifiers)
        subtotal = round((menu_item.base_price + modifier_total) * quantity, 2)
        return OrderItem(
            order_item_id=order_item_id,
            menu_item_id=menu_item.item_id,
            name=menu_item.name,
            quantity=quantity,
            unit_price=menu_item.base_price,
            modifiers=selected_modifiers,
            special_instructions=special_instructions,
            status="pending",
            subtotal=subtotal,
        )

    def _build_payment(self, payment: dict) -> Payment:
        method_type = payment["method_type"]
        payload = {
            "payment_id": payment.get("payment_id", f"PAY-{sum(len(order.payments) for order in self.db.orders.values()) + 1:03d}"),
            "method_type": method_type,
            "amount": round(float(payment["amount"]), 2),
            "status": payment.get("status", "paid"),
            "paid_at": payment.get("paid_at", self._now()),
        }
        if method_type in {"credit_card", "debit_card"}:
            return CardPayment(
                **payload,
                card_brand=payment.get("card_brand", "unknown"),
                last_four=payment.get("last_four", "0000"),
            )
        if method_type == "cash":
            return CashPayment(
                **payload,
                change_given=round(float(payment.get("change_given", 0.0)), 2),
            )
        if method_type == "mobile_wallet":
            return DigitalWalletPayment(
                **payload,
                provider=payment.get("provider", "wallet"),
            )
        if method_type == "gift_card":
            return GiftCardPayment(
                **payload,
                gift_card_id=payment.get("gift_card_id", "gift-card"),
            )
        raise ValueError(f"Unsupported payment method '{method_type}'")

    @is_tool(ToolType.READ)
    def get_restaurant_info(self) -> RestaurantInfo:
        """Return the canonical restaurant profile.

        Use this before answering questions about phone number, address,
        business hours, delivery availability, or other general restaurant
        information. Do not answer those details from memory.
        """
        return self.db.restaurant

    @is_tool(ToolType.READ)
    def get_menu(self, only_available: bool = True) -> list[MenuItem]:
        """Return the restaurant menu. Set only_available to False to include unavailable items."""
        items = list(self.db.menu_items.values())
        if only_available:
            items = [item for item in items if item.available]
        return sorted(items, key=lambda item: (item.category_id, item.name))

    @is_tool(ToolType.READ)
    def get_menu_item_details(self, menu_item_id: str) -> MenuItem:
        """Return the full details of a menu item."""
        return self._get_menu_item(menu_item_id)

    @is_tool(ToolType.READ)
    def get_available_tables(
        self, party_size: int, area_id: Optional[str] = None
    ) -> list[RestaurantTable]:
        """Return available tables for the requested party size and optional dining area."""
        return self._get_available_tables(party_size, area_id)

    @is_tool(ToolType.READ)
    def get_customer_profile(self, customer_id: str) -> CustomerProfile:
        """Return the profile of a registered customer."""
        return self._get_customer(customer_id)

    @is_tool(ToolType.READ)
    def get_reservation_details(self, reservation_id: str) -> Reservation:
        """Return the details of a reservation."""
        return self._get_reservation(reservation_id)

    @is_tool(ToolType.READ)
    def get_order_details(self, order_id: str) -> RestaurantOrder:
        """Return the details of an order."""
        return self._get_order(order_id)

    @is_tool(ToolType.WRITE)
    def create_customer_profile(
        self,
        full_name: str,
        phone_number: str,
        email: Optional[str] = None,
        dietary_preferences: Optional[List[str]] = None,
        default_address: Optional[dict] = None,
    ) -> CustomerProfile:
        """Create a customer profile or return the existing one if the phone number is already registered."""
        existing = self._find_customer_by_phone(phone_number)
        if existing is not None:
            if email is not None:
                existing.email = email
            if dietary_preferences is not None:
                existing.dietary_preferences = dietary_preferences
            if default_address is not None:
                existing.default_address = Address(**default_address)
            return existing

        customer_id = self._next_id("CUST", self.db.customers)
        customer = CustomerProfile(
            customer_id=customer_id,
            full_name=full_name,
            phone_number=phone_number,
            email=email,
            loyalty_points=0,
            dietary_preferences=dietary_preferences or [],
            favorite_item_ids=[],
            default_address=(
                Address(**default_address) if default_address is not None else None
            ),
        )
        self.db.customers[customer_id] = customer
        return customer

    @is_tool(ToolType.WRITE)
    def create_reservation(
        self,
        customer_id: str,
        party_size: int,
        reservation_date: str,
        reservation_time: str,
        special_requests: Optional[List[str]] = None,
        preferred_area_id: Optional[str] = None,
    ) -> Reservation:
        """Create a reservation and reserve the best available table when possible."""
        self._get_customer(customer_id)
        if party_size < 1:
            raise ValueError("Party size must be at least 1")
        reservation_id = self._next_id("RES", self.db.reservations)
        table = None
        available_tables = self._get_available_tables(party_size, preferred_area_id)
        if available_tables:
            table = available_tables[0]
            table.status = "reserved"
        reservation = Reservation(
            reservation_id=reservation_id,
            customer_id=customer_id,
            party_size=party_size,
            reservation_date=reservation_date,
            reservation_time=reservation_time,
            status="confirmed" if table is not None else "pending",
            assigned_table_ids=[table.table_id] if table is not None else [],
            special_requests=special_requests or [],
            created_at=self._now(),
        )
        self.db.reservations[reservation_id] = reservation
        return reservation

    @is_tool(ToolType.WRITE)
    def seat_reservation(self, reservation_id: str) -> Reservation:
        """Mark a reservation as seated and occupy its assigned table."""
        reservation = self._get_reservation(reservation_id)
        if reservation.status == "cancelled":
            raise ValueError("Cancelled reservations cannot be seated")
        reservation.status = "seated"
        for table_id in reservation.assigned_table_ids:
            self._get_table(table_id).status = "occupied"
        return reservation

    @is_tool(ToolType.WRITE)
    def cancel_reservation(self, reservation_id: str) -> Reservation:
        """Cancel a reservation and free any table assigned to it."""
        reservation = self._get_reservation(reservation_id)
        reservation.status = "cancelled"
        for table_id in reservation.assigned_table_ids:
            table = self._get_table(table_id)
            if table.status == "reserved":
                table.status = "available"
        return reservation

    @is_tool(ToolType.WRITE)
    def create_order(
        self,
        order_type: str,
        items: List[dict],
        customer_id: Optional[str] = None,
        table_id: Optional[str] = None,
        reservation_id: Optional[str] = None,
        server_id: Optional[str] = None,
        delivery_info: Optional[dict] = None,
    ) -> RestaurantOrder:
        """Create an order from item requests, calculate totals, and update table or reservation state as needed."""
        if len(items) == 0:
            raise ValueError("At least one item is required to create an order")
        if customer_id is not None:
            self._get_customer(customer_id)
        if reservation_id is not None:
            reservation = self._get_reservation(reservation_id)
            if table_id is None and reservation.assigned_table_ids:
                table_id = reservation.assigned_table_ids[0]
            reservation.status = "seated"
        if order_type == "delivery" and delivery_info is None:
            raise ValueError("Delivery orders require delivery_info")

        order_id = self._next_id("ORD", self.db.orders)
        order_items: list[OrderItem] = []
        for index, item in enumerate(items, start=1):
            order_items.append(
                self._build_order_item(
                    order_item_id=f"{order_id}-ITEM-{index:02d}",
                    menu_item_id=item["menu_item_id"],
                    quantity=item["quantity"],
                    modifiers=item.get("modifiers"),
                    special_instructions=item.get("special_instructions"),
                )
            )

        subtotal = round(sum(item.subtotal for item in order_items), 2)
        tax = round(subtotal * 0.18, 2)
        service_charge = round(subtotal * 0.1, 2) if order_type == "dine_in" else 0.0
        discount = 0.0
        delivery = None
        delivery_fee = 0.0
        if delivery_info is not None:
            address = (
                delivery_info["address"]
                if isinstance(delivery_info["address"], Address)
                else Address(**delivery_info["address"])
            )
            delivery = DeliveryInfo(
                address=address,
                contact_name=delivery_info["contact_name"],
                contact_phone=delivery_info["contact_phone"],
                driver_id=delivery_info.get("driver_id"),
                delivery_fee=round(float(delivery_info.get("delivery_fee", 0.0)), 2),
                estimated_arrival_time=delivery_info.get("estimated_arrival_time"),
            )
            delivery_fee = delivery.delivery_fee

        total = round(subtotal + tax + service_charge + delivery_fee - discount, 2)
        order = RestaurantOrder(
            order_id=order_id,
            customer_id=customer_id,
            order_type=order_type,
            status="received",
            table_id=table_id,
            reservation_id=reservation_id,
            server_id=server_id,
            items=order_items,
            subtotal=subtotal,
            tax=tax,
            service_charge=service_charge,
            discount=discount,
            total=total,
            payments=[],
            delivery_info=delivery,
            created_at=self._now(),
            closed_at=None,
        )
        self.db.orders[order_id] = order
        if table_id is not None:
            self._get_table(table_id).status = "occupied"
        return order

    @is_tool(ToolType.WRITE)
    def update_order_item_status(
        self, order_id: str, order_item_id: str, status: OrderItemStatus
    ) -> RestaurantOrder:
        """Update the status of one order item and recalculate the order status from its lines."""
        order = self._get_order(order_id)
        item = next(
            (order_item for order_item in order.items if order_item.order_item_id == order_item_id),
            None,
        )
        if item is None:
            raise ValueError(f"Order item '{order_item_id}' not found")
        item.status = status
        line_statuses = {order_item.status for order_item in order.items}
        if line_statuses == {"served"}:
            order.status = "served"
        elif line_statuses.issubset({"ready", "served"}):
            order.status = "ready"
        elif "preparing" in line_statuses:
            order.status = "in_preparation"
        elif "cancelled" in line_statuses and len(line_statuses) == 1:
            order.status = "cancelled"
        return order

    @is_tool(ToolType.WRITE)
    def record_payment(self, order_id: str, payment: dict) -> RestaurantOrder:
        """Attach a payment to an order."""
        order = self._get_order(order_id)
        new_payment = self._build_payment(payment)
        order.payments.append(new_payment)
        return order

    @is_tool(ToolType.WRITE)
    def close_order(self, order_id: str) -> RestaurantOrder:
        """Close an order and release its table when applicable."""
        order = self._get_order(order_id)
        order.status = "completed"
        order.closed_at = self._now()
        if order.table_id is not None:
            self._get_table(order.table_id).status = "available"
        if order.reservation_id is not None:
            self._get_reservation(order.reservation_id).status = "completed"
        return order

    @is_tool(ToolType.WRITE)
    def cancel_order(self, order_id: str) -> RestaurantOrder:
        """Cancel an order and release any assigned table."""
        order = self._get_order(order_id)
        order.status = "cancelled"
        order.closed_at = self._now()
        for item in order.items:
            item.status = "cancelled"
        if order.table_id is not None:
            self._get_table(order.table_id).status = "available"
        return order

    @is_tool(ToolType.WRITE)
    def update_table_status(self, table_id: str, status: str) -> RestaurantTable:
        """Change the status of a restaurant table."""
        table = self._get_table(table_id)
        table.status = status
        return table

    @is_tool(ToolType.WRITE)
    def submit_review(
        self,
        rating: int,
        comment: Optional[str] = None,
        customer_id: Optional[str] = None,
        order_id: Optional[str] = None,
    ) -> Review:
        """Create a customer review for the restaurant."""
        if rating < 1 or rating > 5:
            raise ValueError("Rating must be between 1 and 5")
        if customer_id is not None:
            self._get_customer(customer_id)
        if order_id is not None:
            self._get_order(order_id)
        review_id = self._next_id("REV", self.db.reviews)
        review = Review(
            review_id=review_id,
            customer_id=customer_id,
            order_id=order_id,
            rating=rating,
            comment=comment,
            created_at=self._now(),
        )
        self.db.reviews[review_id] = review
        return review

    @is_tool(ToolType.GENERIC)
    def calculate(self, expression: str) -> str:
        """Evaluate a simple arithmetic expression."""
        if not all(char in "0123456789+-*/(). " for char in expression):
            raise ValueError("Invalid characters in expression")
        return str(round(float(eval(expression, {"__builtins__": None}, {})), 2))


