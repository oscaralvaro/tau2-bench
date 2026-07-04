from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import Field

from tau2.domains.restaurante_joaquin_cachay.utils import (
    RESTAURANTE_JOAQUIN_CACHAY_DB_PATH,
)
from tau2.environment.db import DB
from tau2.utils.pydantic_utils import BaseModelNoExtra

DayOfWeek = Literal[
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]
DiningAreaType = Literal["main_hall", "terrace", "bar", "private_room", "patio"]
TableStatus = Literal["available", "occupied", "reserved", "cleaning", "out_of_service"]
ReservationStatus = Literal["pending", "confirmed", "seated", "completed", "cancelled", "no_show"]
OrderType = Literal["dine_in", "takeout", "delivery"]
OrderStatus = Literal[
    "draft",
    "received",
    "in_preparation",
    "ready",
    "served",
    "completed",
    "cancelled",
]
OrderItemStatus = Literal["pending", "preparing", "ready", "served", "cancelled"]
PaymentStatus = Literal["pending", "authorized", "paid", "partially_refunded", "refunded", "failed"]
PaymentMethodType = Literal["cash", "credit_card", "debit_card", "mobile_wallet", "gift_card"]
EmployeeRole = Literal["manager", "host", "server", "cashier", "cook", "bartender", "delivery_driver"]
EmployeeStatus = Literal["active", "on_break", "off_shift", "inactive"]
IngredientUnit = Literal["g", "kg", "ml", "l", "unit", "oz"]
StockStatus = Literal["in_stock", "low_stock", "out_of_stock"]
MenuItemType = Literal["starter", "main", "dessert", "beverage", "combo", "side"]


class Address(BaseModelNoExtra):
    street: str = Field(description="Street address including number and complement")
    city: str = Field(description="City where the restaurant or customer is located")
    state: str = Field(description="State, region, or province")
    country: str = Field(description="Country name")
    zip_code: str = Field(description="Postal code")


class GeoLocation(BaseModelNoExtra):
    latitude: float = Field(description="Latitude coordinate of the location")
    longitude: float = Field(description="Longitude coordinate of the location")


class BusinessHours(BaseModelNoExtra):
    day: DayOfWeek = Field(description="Day of the week")
    open_time: str = Field(description="Opening time in HH:MM format")
    close_time: str = Field(description="Closing time in HH:MM format")
    is_closed: bool = Field(description="Whether the restaurant is closed on this day")


class DiningArea(BaseModelNoExtra):
    area_id: str = Field(description="Unique identifier for the dining area")
    name: str = Field(description="Display name of the dining area")
    area_type: DiningAreaType = Field(description="Type of dining area")
    smoking_allowed: bool = Field(description="Whether smoking is allowed in this area")
    wheelchair_accessible: bool = Field(description="Whether the area is wheelchair accessible")


class RestaurantTable(BaseModelNoExtra):
    table_id: str = Field(description="Unique identifier for the table")
    table_number: str = Field(description="Human-readable table number")
    area_id: str = Field(description="Dining area where the table is located")
    capacity: int = Field(description="Maximum number of guests that can sit at the table")
    status: TableStatus = Field(description="Current operational status of the table")
    joinable_table_ids: List[str] = Field(
        default_factory=list,
        description="Nearby tables that can be joined with this table for larger parties",
    )


class AllergenInfo(BaseModelNoExtra):
    contains: List[str] = Field(
        default_factory=list,
        description="List of allergens contained in the dish",
    )
    may_contain: List[str] = Field(
        default_factory=list,
        description="List of possible cross-contamination allergens",
    )


class NutritionInfo(BaseModelNoExtra):
    calories: int = Field(description="Estimated calories per serving")
    protein_g: float = Field(description="Protein content in grams")
    carbs_g: float = Field(description="Carbohydrate content in grams")
    fat_g: float = Field(description="Fat content in grams")
    sodium_mg: float = Field(description="Sodium content in milligrams")


class ModifierOption(BaseModelNoExtra):
    option_id: str = Field(description="Unique identifier for the modifier option")
    name: str = Field(description="Display name of the option")
    price_delta: float = Field(description="Additional price applied when this option is selected")
    available: bool = Field(description="Whether the option is currently available")


class ModifierGroup(BaseModelNoExtra):
    modifier_group_id: str = Field(description="Unique identifier for the modifier group")
    name: str = Field(description="Display name of the modifier group")
    min_selected: int = Field(description="Minimum number of options that must be selected")
    max_selected: int = Field(description="Maximum number of options that may be selected")
    options: Dict[str, ModifierOption] = Field(
        default_factory=dict,
        description="Modifier options indexed by option id",
    )


class MenuCategory(BaseModelNoExtra):
    category_id: str = Field(description="Unique identifier for the menu category")
    name: str = Field(description="Display name of the category")
    description: str = Field(description="Short explanation of the category")
    display_order: int = Field(description="Position of the category in the menu")
    active: bool = Field(description="Whether the category is currently visible")


class MenuItem(BaseModelNoExtra):
    item_id: str = Field(description="Unique identifier for the menu item")
    category_id: str = Field(description="Category that contains this menu item")
    name: str = Field(description="Display name of the menu item")
    description: str = Field(description="Detailed description of the dish or drink")
    item_type: MenuItemType = Field(description="Type of menu item")
    base_price: float = Field(description="Base sale price of the menu item")
    available: bool = Field(description="Whether the menu item can currently be ordered")
    preparation_time_min: int = Field(description="Estimated preparation time in minutes")
    spicy_level: Optional[int] = Field(
        default=None,
        description="Optional spicy level from 0 to 5",
    )
    vegetarian: bool = Field(description="Whether the item is vegetarian")
    vegan: bool = Field(description="Whether the item is vegan")
    gluten_free: bool = Field(description="Whether the item is gluten free")
    allergens: AllergenInfo = Field(description="Allergen information for the item")
    nutrition: Optional[NutritionInfo] = Field(
        default=None,
        description="Optional nutritional information for the item",
    )
    modifier_groups: List[str] = Field(
        default_factory=list,
        description="Modifier group ids available for this menu item",
    )
    ingredient_ids: List[str] = Field(
        default_factory=list,
        description="Ingredient ids used to prepare this item",
    )


class Ingredient(BaseModelNoExtra):
    ingredient_id: str = Field(description="Unique identifier for the ingredient")
    name: str = Field(description="Ingredient display name")
    unit: IngredientUnit = Field(description="Measurement unit used for stock tracking")
    current_stock: float = Field(description="Current stock quantity available")
    reorder_level: float = Field(description="Threshold below which the ingredient should be reordered")
    supplier_name: str = Field(description="Main supplier for the ingredient")
    cost_per_unit: float = Field(description="Cost per unit of the ingredient")
    stock_status: StockStatus = Field(description="Current stock state of the ingredient")
    refrigerated: bool = Field(description="Whether the ingredient requires refrigeration")


class CustomerProfile(BaseModelNoExtra):
    customer_id: str = Field(description="Unique identifier for the customer")
    full_name: str = Field(description="Customer full name")
    phone_number: str = Field(description="Primary contact phone number")
    email: Optional[str] = Field(default=None, description="Customer email address")
    loyalty_points: int = Field(description="Current loyalty points balance")
    dietary_preferences: List[str] = Field(
        default_factory=list,
        description="Dietary preferences or restrictions declared by the customer",
    )
    favorite_item_ids: List[str] = Field(
        default_factory=list,
        description="Menu item ids marked as favorite by the customer",
    )
    default_address: Optional[Address] = Field(
        default=None,
        description="Default delivery address for the customer",
    )


class Reservation(BaseModelNoExtra):
    reservation_id: str = Field(description="Unique identifier for the reservation")
    customer_id: str = Field(description="Customer who created the reservation")
    party_size: int = Field(description="Number of guests included in the reservation")
    reservation_date: str = Field(description="Reservation date in YYYY-MM-DD format")
    reservation_time: str = Field(description="Reservation time in HH:MM format")
    status: ReservationStatus = Field(description="Current reservation status")
    assigned_table_ids: List[str] = Field(
        default_factory=list,
        description="Tables assigned to the reservation",
    )
    special_requests: List[str] = Field(
        default_factory=list,
        description="Special notes such as allergies, birthday setup, or seating preferences",
    )
    created_at: str = Field(description="Creation timestamp in ISO 8601 format")


class Employee(BaseModelNoExtra):
    employee_id: str = Field(description="Unique identifier for the employee")
    full_name: str = Field(description="Employee full name")
    role: EmployeeRole = Field(description="Operational role of the employee")
    phone_number: str = Field(description="Employee contact phone number")
    email: Optional[str] = Field(default=None, description="Employee email address")
    status: EmployeeStatus = Field(description="Current work status of the employee")
    shift_start: Optional[str] = Field(
        default=None,
        description="Shift start time in ISO 8601 format when applicable",
    )
    shift_end: Optional[str] = Field(
        default=None,
        description="Shift end time in ISO 8601 format when applicable",
    )


class SelectedModifier(BaseModelNoExtra):
    modifier_group_id: str = Field(description="Modifier group used for this selection")
    option_id: str = Field(description="Selected option id")
    option_name: str = Field(description="Display name of the selected option")
    price_delta: float = Field(description="Price change introduced by this selection")


class OrderItem(BaseModelNoExtra):
    order_item_id: str = Field(description="Unique identifier for the order line")
    menu_item_id: str = Field(description="Menu item ordered")
    name: str = Field(description="Snapshot name of the menu item at purchase time")
    quantity: int = Field(description="Quantity ordered for this menu item")
    unit_price: float = Field(description="Base unit price at purchase time")
    modifiers: List[SelectedModifier] = Field(
        default_factory=list,
        description="Modifier selections applied to the order item",
    )
    special_instructions: Optional[str] = Field(
        default=None,
        description="Free text instructions for the kitchen",
    )
    status: OrderItemStatus = Field(description="Current preparation status of the order item")
    subtotal: float = Field(description="Subtotal for this line including modifiers")


class PaymentBase(BaseModelNoExtra):
    payment_id: str = Field(description="Unique identifier for the payment")
    method_type: PaymentMethodType = Field(description="Type of payment method used")
    amount: float = Field(description="Monetary amount processed by this payment")
    status: PaymentStatus = Field(description="Current status of the payment")
    paid_at: Optional[str] = Field(
        default=None,
        description="Timestamp when the payment was processed in ISO 8601 format",
    )


class CardPayment(PaymentBase):
    method_type: Literal["credit_card", "debit_card"] = Field(
        description="Card payment method type"
    )
    card_brand: str = Field(description="Card brand such as Visa or Mastercard")
    last_four: str = Field(description="Last four digits of the card")


class CashPayment(PaymentBase):
    method_type: Literal["cash"] = Field(description="Cash payment method type")
    change_given: float = Field(description="Amount of change returned to the customer")


class DigitalWalletPayment(PaymentBase):
    method_type: Literal["mobile_wallet"] = Field(
        description="Digital wallet payment method type"
    )
    provider: str = Field(description="Digital wallet provider name")


class GiftCardPayment(PaymentBase):
    method_type: Literal["gift_card"] = Field(description="Gift card payment method type")
    gift_card_id: str = Field(description="Gift card identifier")


Payment = Union[CardPayment, CashPayment, DigitalWalletPayment, GiftCardPayment]


class DeliveryInfo(BaseModelNoExtra):
    address: Address = Field(description="Delivery destination address")
    contact_name: str = Field(description="Name of the person receiving the order")
    contact_phone: str = Field(description="Phone number for delivery coordination")
    driver_id: Optional[str] = Field(
        default=None,
        description="Employee id of the assigned delivery driver",
    )
    delivery_fee: float = Field(description="Delivery fee charged to the customer")
    estimated_arrival_time: Optional[str] = Field(
        default=None,
        description="Estimated arrival time in ISO 8601 format",
    )


class RestaurantOrder(BaseModelNoExtra):
    order_id: str = Field(description="Unique identifier for the order")
    customer_id: Optional[str] = Field(
        default=None,
        description="Customer id when the order is linked to a registered customer",
    )
    order_type: OrderType = Field(description="Whether the order is dine-in, takeout, or delivery")
    status: OrderStatus = Field(description="Current lifecycle status of the order")
    table_id: Optional[str] = Field(
        default=None,
        description="Assigned table id for dine-in orders",
    )
    reservation_id: Optional[str] = Field(
        default=None,
        description="Linked reservation id when applicable",
    )
    server_id: Optional[str] = Field(
        default=None,
        description="Employee id of the responsible server or cashier",
    )
    items: List[OrderItem] = Field(description="Order lines included in the order")
    subtotal: float = Field(description="Subtotal before taxes, service charge, and discounts")
    tax: float = Field(description="Tax amount applied to the order")
    service_charge: float = Field(description="Service charge applied to the order")
    discount: float = Field(description="Total discounts applied to the order")
    total: float = Field(description="Final amount charged to the customer")
    payments: List[Payment] = Field(
        default_factory=list,
        description="Payment records associated with the order",
    )
    delivery_info: Optional[DeliveryInfo] = Field(
        default=None,
        description="Delivery details for delivery orders",
    )
    created_at: str = Field(description="Order creation timestamp in ISO 8601 format")
    closed_at: Optional[str] = Field(
        default=None,
        description="Timestamp when the order was completed or cancelled",
    )


class Review(BaseModelNoExtra):
    review_id: str = Field(description="Unique identifier for the review")
    customer_id: Optional[str] = Field(
        default=None,
        description="Customer who authored the review when known",
    )
    order_id: Optional[str] = Field(
        default=None,
        description="Order associated with the review when applicable",
    )
    rating: int = Field(description="Rating value from 1 to 5")
    comment: Optional[str] = Field(default=None, description="Written customer feedback")
    created_at: str = Field(description="Timestamp when the review was created")


class RestaurantInfo(BaseModelNoExtra):
    restaurant_id: str = Field(description="Unique identifier for the restaurant")
    name: str = Field(description="Restaurant commercial name")
    cuisine_type: str = Field(description="Primary cuisine or food concept")
    phone_number: str = Field(description="Main restaurant phone number")
    email: str = Field(description="Main restaurant email")
    address: Address = Field(description="Physical restaurant address")
    location: Optional[GeoLocation] = Field(
        default=None,
        description="Optional geographic coordinates for the restaurant",
    )
    business_hours: List[BusinessHours] = Field(
        default_factory=list,
        description="Weekly opening hours configuration",
    )
    dine_in_enabled: bool = Field(description="Whether dine-in orders are supported")
    takeout_enabled: bool = Field(description="Whether takeout orders are supported")
    delivery_enabled: bool = Field(description="Whether delivery orders are supported")
    average_ticket: float = Field(description="Average ticket size in the local currency")
    loyalty_program_enabled: bool = Field(description="Whether loyalty points are supported")


class RestauranteJoaquinCachayDB(DB):
    restaurant: RestaurantInfo = Field(description="General restaurant configuration and business profile")
    dining_areas: Dict[str, DiningArea] = Field(
        default_factory=dict,
        description="Dining areas indexed by area id",
    )
    tables: Dict[str, RestaurantTable] = Field(
        default_factory=dict,
        description="Restaurant tables indexed by table id",
    )
    menu_categories: Dict[str, MenuCategory] = Field(
        default_factory=dict,
        description="Menu categories indexed by category id",
    )
    menu_items: Dict[str, MenuItem] = Field(
        default_factory=dict,
        description="Menu items indexed by item id",
    )
    modifier_groups: Dict[str, ModifierGroup] = Field(
        default_factory=dict,
        description="Modifier groups indexed by modifier group id",
    )
    ingredients: Dict[str, Ingredient] = Field(
        default_factory=dict,
        description="Ingredients indexed by ingredient id",
    )
    customers: Dict[str, CustomerProfile] = Field(
        default_factory=dict,
        description="Registered customers indexed by customer id",
    )
    reservations: Dict[str, Reservation] = Field(
        default_factory=dict,
        description="Reservations indexed by reservation id",
    )
    employees: Dict[str, Employee] = Field(
        default_factory=dict,
        description="Employees indexed by employee id",
    )
    orders: Dict[str, RestaurantOrder] = Field(
        default_factory=dict,
        description="Orders indexed by order id",
    )
    reviews: Dict[str, Review] = Field(
        default_factory=dict,
        description="Customer reviews indexed by review id",
    )

    def get_statistics(self) -> dict[str, Any]:
        total_tables = len(self.tables)
        occupied_tables = sum(1 for table in self.tables.values() if table.status == "occupied")
        available_menu_items = sum(1 for item in self.menu_items.values() if item.available)
        active_employees = sum(1 for employee in self.employees.values() if employee.status != "inactive")
        pending_reservations = sum(
            1 for reservation in self.reservations.values() if reservation.status in {"pending", "confirmed"}
        )
        open_orders = sum(
            1 for order in self.orders.values() if order.status not in {"completed", "cancelled"}
        )

        return {
            "restaurant_name": self.restaurant.name,
            "num_dining_areas": len(self.dining_areas),
            "num_tables": total_tables,
            "num_occupied_tables": occupied_tables,
            "num_menu_categories": len(self.menu_categories),
            "num_menu_items": len(self.menu_items),
            "num_available_menu_items": available_menu_items,
            "num_modifier_groups": len(self.modifier_groups),
            "num_ingredients": len(self.ingredients),
            "num_customers": len(self.customers),
            "num_reservations": len(self.reservations),
            "num_pending_reservations": pending_reservations,
            "num_employees": len(self.employees),
            "num_active_employees": active_employees,
            "num_orders": len(self.orders),
            "num_open_orders": open_orders,
            "num_reviews": len(self.reviews),
        }


def get_db():
    return RestauranteJoaquinCachayDB.load(RESTAURANTE_JOAQUIN_CACHAY_DB_PATH)


if __name__ == "__main__":
    db = get_db()
    print(db.get_statistics())

