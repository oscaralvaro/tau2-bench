from typing import List, Optional

from tau2.domains.restaurante_joaquin_cachay.user_data_model import (
    CartItem,
    CartModifierSelection,
    DeliveryContact,
    OrderRequest,
    PaymentIntent,
    ReservationRequest,
    RestaurantUserDB,
    UserMenuItemSnapshot,
)
from tau2.environment.toolkit import ToolKitBase, ToolType, is_tool


class RestauranteJoaquinCachayUserTools(ToolKitBase):
    """Customer-side tools for interacting with the restaurant."""

    db: RestaurantUserDB

    def __init__(self, db: RestaurantUserDB) -> None:
        super().__init__(db)

    def _next_cart_item_id(self) -> str:
        return f"CART-{len(self.db.cart) + 1:03d}"

    def _get_visible_menu_item(self, menu_item_id: str) -> UserMenuItemSnapshot:
        if menu_item_id not in self.db.visible_menu:
            raise ValueError(f"Menu item '{menu_item_id}' is not visible to the user")
        return self.db.visible_menu[menu_item_id]

    def _estimate_modifier_delta(
        self, modifier_selections: Optional[List[dict]]
    ) -> float:
        total = 0.0
        for modifier in modifier_selections or []:
            group_id = modifier["modifier_group_id"]
            option_id = modifier["option_id"]
            if group_id not in self.db.visible_modifier_groups:
                continue
            group = self.db.visible_modifier_groups[group_id]
            if option_id not in group.options:
                continue
            total += group.options[option_id].price_delta
        return round(total, 2)

    @is_tool(ToolType.READ)
    def view_profile(self) -> dict:
        """Return the current customer identity and dining preferences."""
        return {
            "identity": self.db.identity.model_dump(),
            "preferences": self.db.preferences.model_dump(),
        }

    @is_tool(ToolType.WRITE)
    def update_profile(
        self,
        name: Optional[str] = None,
        phone_number: Optional[str] = None,
        email: Optional[str] = None,
    ) -> dict:
        """Update the visible customer profile used by the restaurant environment."""
        if name is not None:
            self.db.identity.name = name
        if phone_number is not None:
            self.db.identity.phone_number = phone_number
        if email is not None:
            self.db.identity.email = email
        return self.db.identity.model_dump()

    @is_tool(ToolType.WRITE)
    def set_dining_preferences(
        self,
        party_size: int,
        preferred_order_type: str = "dine_in",
        preferred_area_id: Optional[str] = None,
        dietary_preferences: Optional[List[str]] = None,
    ) -> dict:
        """Update dining preferences such as party size, order type, area, and dietary restrictions."""
        self.db.preferences.party_size = party_size
        self.db.preferences.preferred_order_type = preferred_order_type
        self.db.preferences.preferred_area_id = preferred_area_id
        if dietary_preferences is not None:
            self.db.preferences.dietary_preferences = dietary_preferences
        return self.db.preferences.model_dump()

    @is_tool(ToolType.READ)
    def browse_menu(
        self, only_available: bool = True, category_id: Optional[str] = None
    ) -> list[UserMenuItemSnapshot]:
        """Browse the menu snapshot visible to the customer."""
        items = list(self.db.visible_menu.values())
        if only_available:
            items = [item for item in items if item.available]
        if category_id is not None:
            items = [item for item in items if item.category_id == category_id]
        return sorted(items, key=lambda item: (item.category_name, item.name))

    @is_tool(ToolType.READ)
    def view_cart(self) -> list[CartItem]:
        """Return the current cart."""
        return self.db.cart

    @is_tool(ToolType.WRITE)
    def add_item_to_cart(
        self,
        menu_item_id: str,
        quantity: int = 1,
        modifier_selections: Optional[List[dict]] = None,
        special_instructions: Optional[str] = None,
    ) -> CartItem:
        """Add a menu item to the cart using the menu snapshot visible to the user."""
        if quantity < 1:
            raise ValueError("Quantity must be at least 1")
        menu_item = self._get_visible_menu_item(menu_item_id)
        if not menu_item.available:
            raise ValueError(f"Menu item '{menu_item.name}' is unavailable")
        modifiers = [
            CartModifierSelection(
                modifier_group_id=modifier["modifier_group_id"],
                option_id=modifier["option_id"],
            )
            for modifier in modifier_selections or []
        ]
        modifier_delta = self._estimate_modifier_delta(modifier_selections)
        cart_item = CartItem(
            cart_item_id=self._next_cart_item_id(),
            menu_item_id=menu_item.item_id,
            name=menu_item.name,
            quantity=quantity,
            base_price=menu_item.base_price,
            modifiers=modifiers,
            special_instructions=special_instructions,
            estimated_subtotal=round(
                (menu_item.base_price + modifier_delta) * quantity, 2
            ),
        )
        self.db.cart.append(cart_item)
        return cart_item

    @is_tool(ToolType.WRITE)
    def remove_item_from_cart(self, cart_item_id: str) -> list[CartItem]:
        """Remove one cart line by its cart item id."""
        original_count = len(self.db.cart)
        self.db.cart = [
            cart_item for cart_item in self.db.cart if cart_item.cart_item_id != cart_item_id
        ]
        if len(self.db.cart) == original_count:
            raise ValueError(f"Cart item '{cart_item_id}' not found")
        return self.db.cart

    @is_tool(ToolType.WRITE)
    def clear_cart(self) -> str:
        """Clear the current cart."""
        self.db.cart = []
        return "Cart cleared."

    @is_tool(ToolType.WRITE)
    def request_reservation(
        self,
        reservation_date: str,
        reservation_time: str,
        party_size: Optional[int] = None,
        special_requests: Optional[List[str]] = None,
        preferred_area_id: Optional[str] = None,
    ) -> ReservationRequest:
        """Prepare a reservation request. Use confirm_reservation_request to send it to the restaurant."""
        self.db.reservation_request = ReservationRequest(
            party_size=party_size or self.db.preferences.party_size,
            reservation_date=reservation_date,
            reservation_time=reservation_time,
            special_requests=special_requests or [],
            preferred_area_id=preferred_area_id or self.db.preferences.preferred_area_id,
            confirmed=False,
            processed=False,
            reservation_id=None,
        )
        return self.db.reservation_request

    @is_tool(ToolType.WRITE)
    def confirm_reservation_request(self) -> ReservationRequest:
        """Confirm the current reservation request so the environment can create it."""
        if self.db.reservation_request is None:
            raise ValueError("There is no reservation request to confirm")
        self.db.reservation_request.confirmed = True
        return self.db.reservation_request

    @is_tool(ToolType.WRITE)
    def cancel_active_reservation(self) -> str:
        """Request cancellation of the currently active reservation."""
        if self.db.active_reservation_id is None:
            raise ValueError("There is no active reservation to cancel")
        self.db.reservation_cancellation_request_id = self.db.active_reservation_id
        return f"Cancellation requested for reservation {self.db.active_reservation_id}."

    @is_tool(ToolType.READ)
    def view_active_reservation(self) -> Optional[dict]:
        """Return the currently tracked reservation snapshot."""
        if self.db.active_reservation_id is None:
            return None
        reservation = self.db.tracked_reservations.get(self.db.active_reservation_id)
        return reservation.model_dump() if reservation is not None else None

    @is_tool(ToolType.WRITE)
    def submit_order(
        self,
        order_type: Optional[str] = None,
        table_id: Optional[str] = None,
        reservation_id: Optional[str] = None,
        delivery_contact: Optional[dict] = None,
        special_note: Optional[str] = None,
    ) -> OrderRequest:
        """Submit the current cart as an order request to the restaurant."""
        if len(self.db.cart) == 0:
            raise ValueError("The cart is empty")
        delivery = (
            DeliveryContact(
                address=delivery_contact["address"],
                contact_name=delivery_contact["contact_name"],
                contact_phone=delivery_contact["contact_phone"],
            )
            if delivery_contact is not None
            else None
        )
        self.db.order_request = OrderRequest(
            order_type=order_type or self.db.preferences.preferred_order_type,
            items=[cart_item.model_copy(deep=True) for cart_item in self.db.cart],
            table_id=table_id,
            reservation_id=reservation_id or self.db.active_reservation_id,
            delivery_contact=delivery,
            special_note=special_note,
            submitted=True,
            processed=False,
            order_id=None,
        )
        return self.db.order_request

    @is_tool(ToolType.READ)
    def view_active_order(self) -> Optional[dict]:
        """Return the currently tracked order snapshot."""
        if self.db.active_order_id is None:
            return None
        order = self.db.tracked_orders.get(self.db.active_order_id)
        return order.model_dump() if order is not None else None

    @is_tool(ToolType.WRITE)
    def request_payment(
        self,
        order_id: Optional[str] = None,
        method_type: str = "cash",
        amount: Optional[float] = None,
        tip: float = 0.0,
        metadata: Optional[dict] = None,
    ) -> PaymentIntent:
        """Prepare a payment intent for the active order. Use confirm_payment to process it."""
        resolved_order_id = order_id or self.db.active_order_id
        if resolved_order_id is None:
            raise ValueError("There is no order to pay")
        tracked_order = self.db.tracked_orders.get(resolved_order_id)
        if tracked_order is None and amount is None:
            raise ValueError("Amount is required when the order is not tracked")
        self.db.payment_intent = PaymentIntent(
            order_id=resolved_order_id,
            method_type=method_type,
            amount=amount if amount is not None else tracked_order.total,
            tip=tip,
            metadata=metadata or {},
            confirmed=False,
            paid=False,
        )
        return self.db.payment_intent

    @is_tool(ToolType.WRITE)
    def confirm_payment(self) -> PaymentIntent:
        """Confirm the current payment intent so the environment can process it."""
        if self.db.payment_intent is None:
            raise ValueError("There is no payment intent to confirm")
        self.db.payment_intent.confirmed = True
        return self.db.payment_intent

    @is_tool(ToolType.WRITE)
    def set_presence(
        self, currently_in_restaurant: bool, seated_table_id: Optional[str] = None
    ) -> dict:
        """Update whether the customer is in the restaurant and optionally where they are seated."""
        self.db.surroundings.currently_in_restaurant = currently_in_restaurant
        self.db.surroundings.seated_table_id = seated_table_id
        return self.db.surroundings.model_dump()

