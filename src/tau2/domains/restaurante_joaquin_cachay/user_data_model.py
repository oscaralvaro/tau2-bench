from typing import Any, Dict, List, Optional

from pydantic import Field

from tau2.domains.restaurante_joaquin_cachay.data_model import (
    Address,
    OrderType,
    PaymentMethodType,
)
from tau2.environment.db import DB
from tau2.utils.pydantic_utils import BaseModelNoExtra, update_pydantic_model_with_dict


class UserIdentity(BaseModelNoExtra):
    name: Optional[str] = Field(default=None, description="Customer display name")
    phone_number: Optional[str] = Field(
        default=None, description="Primary phone number used by the customer"
    )
    email: Optional[str] = Field(default=None, description="Customer email address")
    customer_id: Optional[str] = Field(
        default=None, description="Linked customer id in the restaurant database"
    )


class UserDiningPreferences(BaseModelNoExtra):
    party_size: int = Field(default=2, description="Preferred number of guests")
    preferred_area_id: Optional[str] = Field(
        default=None, description="Preferred dining area"
    )
    preferred_order_type: OrderType = Field(
        default="dine_in", description="Preferred service mode"
    )
    dietary_preferences: List[str] = Field(
        default_factory=list,
        description="Declared dietary restrictions or preferences",
    )
    favorite_item_ids: List[str] = Field(
        default_factory=list,
        description="Menu item ids marked as favorite by the user",
    )


class UserMenuItemSnapshot(BaseModelNoExtra):
    item_id: str = Field(description="Menu item id")
    category_id: str = Field(description="Category id of the menu item")
    category_name: str = Field(description="Category name of the menu item")
    name: str = Field(description="Display name of the item")
    description: str = Field(description="Short item description")
    base_price: float = Field(description="Visible price of the item")
    available: bool = Field(description="Whether the item can currently be ordered")
    vegetarian: bool = Field(description="Whether the item is vegetarian")
    vegan: bool = Field(description="Whether the item is vegan")
    gluten_free: bool = Field(description="Whether the item is gluten free")
    preparation_time_min: int = Field(description="Estimated preparation time")


class UserModifierOptionSnapshot(BaseModelNoExtra):
    option_id: str = Field(description="Modifier option id")
    name: str = Field(description="Display name of the modifier option")
    price_delta: float = Field(description="Price change produced by the option")
    available: bool = Field(description="Whether the option is available")


class UserModifierGroupSnapshot(BaseModelNoExtra):
    modifier_group_id: str = Field(description="Modifier group id")
    name: str = Field(description="Display name of the modifier group")
    min_selected: int = Field(description="Minimum number of required selections")
    max_selected: int = Field(description="Maximum number of allowed selections")
    options: Dict[str, UserModifierOptionSnapshot] = Field(
        default_factory=dict,
        description="Modifier options indexed by option id",
    )


class CartModifierSelection(BaseModelNoExtra):
    modifier_group_id: str = Field(description="Selected modifier group id")
    option_id: str = Field(description="Selected modifier option id")


class CartItem(BaseModelNoExtra):
    cart_item_id: str = Field(description="Unique identifier inside the user cart")
    menu_item_id: str = Field(description="Menu item id")
    name: str = Field(description="Menu item display name")
    quantity: int = Field(description="Requested quantity")
    base_price: float = Field(description="Snapshot base price")
    modifiers: List[CartModifierSelection] = Field(
        default_factory=list,
        description="Selected modifier options",
    )
    special_instructions: Optional[str] = Field(
        default=None,
        description="Special kitchen instructions for the item",
    )
    estimated_subtotal: float = Field(
        description="Estimated subtotal for this cart line"
    )


class DeliveryContact(BaseModelNoExtra):
    address: Address = Field(description="Delivery destination address")
    contact_name: str = Field(description="Person receiving the order")
    contact_phone: str = Field(description="Phone number for delivery coordination")


class ReservationRequest(BaseModelNoExtra):
    party_size: int = Field(description="Requested number of guests")
    reservation_date: str = Field(description="Reservation date in YYYY-MM-DD format")
    reservation_time: str = Field(description="Reservation time in HH:MM format")
    special_requests: List[str] = Field(
        default_factory=list,
        description="Extra requests attached to the reservation",
    )
    preferred_area_id: Optional[str] = Field(
        default=None, description="Preferred area for the reservation"
    )
    confirmed: bool = Field(
        default=False,
        description="Whether the customer has explicitly confirmed this request",
    )
    processed: bool = Field(
        default=False,
        description="Whether the environment has already created the reservation",
    )
    reservation_id: Optional[str] = Field(
        default=None,
        description="Created reservation id once synchronized with the restaurant",
    )


class OrderRequest(BaseModelNoExtra):
    order_type: OrderType = Field(description="Requested order type")
    items: List[CartItem] = Field(description="Snapshot of the cart at submission time")
    table_id: Optional[str] = Field(
        default=None, description="Requested dine-in table id"
    )
    reservation_id: Optional[str] = Field(
        default=None, description="Linked reservation id when applicable"
    )
    delivery_contact: Optional[DeliveryContact] = Field(
        default=None,
        description="Delivery information for delivery orders",
    )
    special_note: Optional[str] = Field(
        default=None,
        description="Additional note attached to the full order request",
    )
    submitted: bool = Field(
        default=False,
        description="Whether the order should be synchronized with the restaurant",
    )
    processed: bool = Field(
        default=False,
        description="Whether the environment has already created the order",
    )
    order_id: Optional[str] = Field(
        default=None,
        description="Created order id after synchronization",
    )


class PaymentIntent(BaseModelNoExtra):
    order_id: str = Field(description="Order to be paid")
    method_type: PaymentMethodType = Field(description="Requested payment method")
    amount: float = Field(description="Amount the user intends to pay")
    tip: float = Field(default=0.0, description="Optional tip amount")
    metadata: Dict[str, str] = Field(
        default_factory=dict,
        description="Additional payment information such as card brand or last four digits",
    )
    confirmed: bool = Field(
        default=False,
        description="Whether the customer confirmed the payment",
    )
    paid: bool = Field(
        default=False,
        description="Whether the payment was synchronized with the restaurant",
    )


class UserReservationStatusSnapshot(BaseModelNoExtra):
    reservation_id: str = Field(description="Reservation id")
    reservation_date: str = Field(description="Reservation date")
    reservation_time: str = Field(description="Reservation time")
    party_size: int = Field(description="Party size")
    status: str = Field(description="Reservation status")
    assigned_table_ids: List[str] = Field(
        default_factory=list,
        description="Assigned tables for the reservation",
    )


class UserOrderStatusSnapshot(BaseModelNoExtra):
    order_id: str = Field(description="Order id")
    order_type: str = Field(description="Order type")
    status: str = Field(description="Current order status")
    total: float = Field(description="Order total")
    table_id: Optional[str] = Field(default=None, description="Assigned table id")
    created_at: str = Field(description="Order creation timestamp")
    payment_status: str = Field(description="Summary payment status for the order")


class RestaurantUserSurroundings(BaseModelNoExtra):
    currently_in_restaurant: bool = Field(
        default=False,
        description="Whether the customer is currently inside the restaurant",
    )
    seated_table_id: Optional[str] = Field(
        default=None,
        description="Table where the customer is currently seated",
    )
    last_action_note: Optional[str] = Field(
        default=None,
        description="Latest note shown to the user after synchronization",
    )


class RestaurantUserDB(DB):
    identity: UserIdentity = Field(
        default_factory=UserIdentity,
        description="Customer identity within the restaurant experience",
    )
    preferences: UserDiningPreferences = Field(
        default_factory=UserDiningPreferences,
        description="Customer dining preferences",
    )
    visible_menu: Dict[str, UserMenuItemSnapshot] = Field(
        default_factory=dict,
        description="Visible menu items synchronized from the restaurant database",
    )
    visible_modifier_groups: Dict[str, UserModifierGroupSnapshot] = Field(
        default_factory=dict,
        description="Visible modifier groups synchronized from the restaurant database",
    )
    cart: List[CartItem] = Field(
        default_factory=list,
        description="Current cart built by the customer",
    )
    reservation_request: Optional[ReservationRequest] = Field(
        default=None,
        description="Reservation request waiting for synchronization",
    )
    reservation_cancellation_request_id: Optional[str] = Field(
        default=None,
        description="Reservation id the customer wants to cancel",
    )
    order_request: Optional[OrderRequest] = Field(
        default=None,
        description="Order request waiting for synchronization",
    )
    payment_intent: Optional[PaymentIntent] = Field(
        default=None,
        description="Payment request waiting for synchronization",
    )
    tracked_orders: Dict[str, UserOrderStatusSnapshot] = Field(
        default_factory=dict,
        description="Orders visible to the user indexed by order id",
    )
    tracked_reservations: Dict[str, UserReservationStatusSnapshot] = Field(
        default_factory=dict,
        description="Reservations visible to the user indexed by reservation id",
    )
    active_order_id: Optional[str] = Field(
        default=None,
        description="Most relevant order for the current session",
    )
    active_reservation_id: Optional[str] = Field(
        default=None,
        description="Most relevant reservation for the current session",
    )
    surroundings: RestaurantUserSurroundings = Field(
        default_factory=RestaurantUserSurroundings,
        description="Customer surroundings and current in-restaurant state",
    )

    def update_session(self, update_data: Dict[str, Any]) -> None:
        self.__dict__.update(
            update_pydantic_model_with_dict(self, update_data).__dict__
        )

