from pathlib import Path
from typing import Optional

from tau2.data_model.tasks import Task
from tau2.domains.restaurante_joaquin_cachay.data_model import (
    Address,
    RestaurantInfo,
    RestauranteJoaquinCachayDB,
)
from tau2.domains.restaurante_joaquin_cachay.tools import (
    RestauranteJoaquinCachayTools,
)
from tau2.domains.restaurante_joaquin_cachay.user_data_model import (
    RestaurantUserDB,
    UserMenuItemSnapshot,
    UserModifierGroupSnapshot,
    UserModifierOptionSnapshot,
    UserOrderStatusSnapshot,
    UserReservationStatusSnapshot,
)
from tau2.domains.restaurante_joaquin_cachay.user_tools import (
    RestauranteJoaquinCachayUserTools,
)
from tau2.domains.restaurante_joaquin_cachay.utils import (
    RESTAURANTE_JOAQUIN_CACHAY_DB_PATH,
    RESTAURANTE_JOAQUIN_CACHAY_POLICY_PATH,
    RESTAURANTE_JOAQUIN_CACHAY_POLICY_SOLO_PATH,
    RESTAURANTE_JOAQUIN_CACHAY_TASK_SET_PATH,
    RESTAURANTE_JOAQUIN_CACHAY_USER_DB_PATH,
)
from tau2.environment.environment import Environment
from tau2.utils import load_file


class RestauranteJoaquinCachayEnvironment(Environment):
    tools: RestauranteJoaquinCachayTools
    user_tools: RestauranteJoaquinCachayUserTools

    def __init__(
        self,
        domain_name: str,
        policy: str,
        tools: RestauranteJoaquinCachayTools,
        user_tools: RestauranteJoaquinCachayUserTools,
        solo_mode: bool = False,
    ):
        super().__init__(domain_name, policy, tools, user_tools, solo_mode=solo_mode)

    def _sync_visible_menu(self) -> None:
        self.user_tools.db.visible_menu = {}
        for item_id, item in self.tools.db.menu_items.items():
            category_name = (
                self.tools.db.menu_categories[item.category_id].name
                if item.category_id in self.tools.db.menu_categories
                else item.category_id
            )
            self.user_tools.db.visible_menu[item_id] = UserMenuItemSnapshot(
                item_id=item.item_id,
                category_id=item.category_id,
                category_name=category_name,
                name=item.name,
                description=item.description,
                base_price=item.base_price,
                available=item.available,
                vegetarian=item.vegetarian,
                vegan=item.vegan,
                gluten_free=item.gluten_free,
                preparation_time_min=item.preparation_time_min,
            )

        self.user_tools.db.visible_modifier_groups = {}
        for group_id, group in self.tools.db.modifier_groups.items():
            self.user_tools.db.visible_modifier_groups[group_id] = (
                UserModifierGroupSnapshot(
                    modifier_group_id=group.modifier_group_id,
                    name=group.name,
                    min_selected=group.min_selected,
                    max_selected=group.max_selected,
                    options={
                        option_id: UserModifierOptionSnapshot(
                            option_id=option.option_id,
                            name=option.name,
                            price_delta=option.price_delta,
                            available=option.available,
                        )
                        for option_id, option in group.options.items()
                    },
                )
            )

    def _ensure_customer_identity(self) -> None:
        identity = self.user_tools.db.identity
        if identity.customer_id is not None:
            return
        if not identity.name or not identity.phone_number:
            return
        customer = self.tools.create_customer_profile(
            full_name=identity.name,
            phone_number=identity.phone_number,
            email=identity.email,
            dietary_preferences=self.user_tools.db.preferences.dietary_preferences,
        )
        identity.customer_id = customer.customer_id

    def _sync_reservation_request(self) -> None:
        user_db = self.user_tools.db
        if (
            user_db.reservation_request is not None
            and user_db.reservation_request.confirmed
            and not user_db.reservation_request.processed
        ):
            self._ensure_customer_identity()
            if user_db.identity.customer_id is None:
                raise ValueError(
                    "The customer must have name and phone number before creating a reservation"
                )
            reservation = self.tools.create_reservation(
                customer_id=user_db.identity.customer_id,
                party_size=user_db.reservation_request.party_size,
                reservation_date=user_db.reservation_request.reservation_date,
                reservation_time=user_db.reservation_request.reservation_time,
                special_requests=user_db.reservation_request.special_requests,
                preferred_area_id=user_db.reservation_request.preferred_area_id,
            )
            user_db.reservation_request.reservation_id = reservation.reservation_id
            user_db.reservation_request.processed = True
            user_db.active_reservation_id = reservation.reservation_id
            user_db.surroundings.last_action_note = (
                f"Reservation {reservation.reservation_id} created."
            )

        if user_db.reservation_cancellation_request_id is not None:
            reservation_id = user_db.reservation_cancellation_request_id
            if reservation_id in self.tools.db.reservations:
                self.tools.cancel_reservation(reservation_id)
                user_db.surroundings.last_action_note = (
                    f"Reservation {reservation_id} cancelled."
                )
            user_db.reservation_cancellation_request_id = None

    def _sync_order_request(self) -> None:
        user_db = self.user_tools.db
        if user_db.order_request is None:
            return
        if not user_db.order_request.submitted or user_db.order_request.processed:
            return

        self._ensure_customer_identity()
        delivery_info = None
        if user_db.order_request.delivery_contact is not None:
            delivery_info = {
                "address": user_db.order_request.delivery_contact.address,
                "contact_name": user_db.order_request.delivery_contact.contact_name,
                "contact_phone": user_db.order_request.delivery_contact.contact_phone,
                "delivery_fee": 7.5,
            }

        order = self.tools.create_order(
            order_type=user_db.order_request.order_type,
            items=[
                {
                    "menu_item_id": item.menu_item_id,
                    "quantity": item.quantity,
                    "modifiers": [
                        {
                            "modifier_group_id": modifier.modifier_group_id,
                            "option_id": modifier.option_id,
                        }
                        for modifier in item.modifiers
                    ],
                    "special_instructions": item.special_instructions,
                }
                for item in user_db.order_request.items
            ],
            customer_id=user_db.identity.customer_id,
            table_id=user_db.order_request.table_id
            or user_db.surroundings.seated_table_id,
            reservation_id=user_db.order_request.reservation_id,
            delivery_info=delivery_info,
        )
        user_db.order_request.order_id = order.order_id
        user_db.order_request.processed = True
        user_db.active_order_id = order.order_id
        user_db.cart = []
        user_db.surroundings.last_action_note = f"Order {order.order_id} created."

    def _sync_payment_intent(self) -> None:
        payment_intent = self.user_tools.db.payment_intent
        if payment_intent is None or not payment_intent.confirmed or payment_intent.paid:
            return
        payment_payload = {
            "method_type": payment_intent.method_type,
            "amount": round(payment_intent.amount + payment_intent.tip, 2),
            "status": "paid",
        }
        if payment_intent.method_type in {"credit_card", "debit_card"}:
            payment_payload["card_brand"] = payment_intent.metadata.get(
                "card_brand", "visa"
            )
            payment_payload["last_four"] = payment_intent.metadata.get(
                "last_four", "1111"
            )
        elif payment_intent.method_type == "mobile_wallet":
            payment_payload["provider"] = payment_intent.metadata.get(
                "provider", "wallet"
            )
        elif payment_intent.method_type == "gift_card":
            payment_payload["gift_card_id"] = payment_intent.metadata.get(
                "gift_card_id", "gift-card"
            )
        elif payment_intent.method_type == "cash":
            payment_payload["change_given"] = payment_intent.metadata.get(
                "change_given", 0.0
            )
        self.tools.record_payment(payment_intent.order_id, payment_payload)
        payment_intent.paid = True
        self.user_tools.db.surroundings.last_action_note = (
            f"Payment registered for order {payment_intent.order_id}."
        )

    def _sync_tracked_state(self) -> None:
        user_db = self.user_tools.db
        customer_id = user_db.identity.customer_id
        user_db.tracked_reservations = {}
        for reservation in self.tools.db.reservations.values():
            if customer_id is None or reservation.customer_id != customer_id:
                continue
            user_db.tracked_reservations[reservation.reservation_id] = (
                UserReservationStatusSnapshot(
                    reservation_id=reservation.reservation_id,
                    reservation_date=reservation.reservation_date,
                    reservation_time=reservation.reservation_time,
                    party_size=reservation.party_size,
                    status=reservation.status,
                    assigned_table_ids=reservation.assigned_table_ids,
                )
            )

        user_db.tracked_orders = {}
        for order in self.tools.db.orders.values():
            if customer_id is None or order.customer_id != customer_id:
                continue
            payment_status = "unpaid"
            if len(order.payments) > 0:
                payment_status = order.payments[-1].status
            user_db.tracked_orders[order.order_id] = UserOrderStatusSnapshot(
                order_id=order.order_id,
                order_type=order.order_type,
                status=order.status,
                total=order.total,
                table_id=order.table_id,
                created_at=order.created_at,
                payment_status=payment_status,
            )

        if (
            user_db.active_reservation_id is not None
            and user_db.active_reservation_id in user_db.tracked_reservations
        ):
            reservation = user_db.tracked_reservations[user_db.active_reservation_id]
            if reservation.status == "seated" and reservation.assigned_table_ids:
                user_db.surroundings.currently_in_restaurant = True
                user_db.surroundings.seated_table_id = reservation.assigned_table_ids[0]
        if (
            user_db.active_order_id is not None
            and user_db.active_order_id in user_db.tracked_orders
        ):
            order = user_db.tracked_orders[user_db.active_order_id]
            if order.table_id is not None:
                user_db.surroundings.seated_table_id = order.table_id

    def sync_tools(self):
        self._sync_visible_menu()
        self._ensure_customer_identity()
        self._sync_reservation_request()
        self._sync_order_request()
        self._sync_payment_intent()
        self._sync_tracked_state()


def _load_text_or_default(path: Path, default_text: str) -> str:
    if path.exists():
        return load_file(path)
    return default_text


def _load_tasks_if_available(path: Path) -> list[Task]:
    if not path.exists():
        return []
    tasks = load_file(path)
    if isinstance(tasks, dict) and "tasks" in tasks:
        tasks = tasks["tasks"]
    return [Task.model_validate(task) for task in tasks]


def _default_db() -> RestauranteJoaquinCachayDB:
    return RestauranteJoaquinCachayDB(
        restaurant=RestaurantInfo(
            restaurant_id="rest-001",
            name="Restaurante Joaquin Cachay",
            cuisine_type="Peruvian Fusion",
            phone_number="+51-999-999-999",
            email="reservas@restaurantejoaquincachay.com",
            address=Address(
                street="Av. Principal 123",
                city="Lima",
                state="Lima",
                country="Peru",
                zip_code="15001",
            ),
            location=None,
            business_hours=[],
            dine_in_enabled=True,
            takeout_enabled=True,
            delivery_enabled=True,
            average_ticket=45.0,
            loyalty_program_enabled=True,
        )
    )


def get_environment(
    db: Optional[RestauranteJoaquinCachayDB] = None,
    user_db: Optional[RestaurantUserDB] = None,
    solo_mode: bool = False,
) -> RestauranteJoaquinCachayEnvironment:
    if db is None:
        db = (
            RestauranteJoaquinCachayDB.load(RESTAURANTE_JOAQUIN_CACHAY_DB_PATH)
            if RESTAURANTE_JOAQUIN_CACHAY_DB_PATH.exists()
            else _default_db()
        )
    if user_db is None:
        user_db = (
            RestaurantUserDB.load(RESTAURANTE_JOAQUIN_CACHAY_USER_DB_PATH)
            if RESTAURANTE_JOAQUIN_CACHAY_USER_DB_PATH.exists()
            else RestaurantUserDB()
        )
    tools = RestauranteJoaquinCachayTools(db)
    user_tools = RestauranteJoaquinCachayUserTools(user_db)
    policy_path = (
        RESTAURANTE_JOAQUIN_CACHAY_POLICY_SOLO_PATH
        if solo_mode
        else RESTAURANTE_JOAQUIN_CACHAY_POLICY_PATH
    )
    policy = _load_text_or_default(
        policy_path,
        "You are the restaurant assistant. Help customers with menu questions, reservations, orders, and payments while keeping the restaurant database accurate.",
    )
    env = RestauranteJoaquinCachayEnvironment(
        domain_name="restaurante_joaquin_cachay",
        policy=policy,
        tools=tools,
        user_tools=user_tools,
        solo_mode=solo_mode,
    )
    return env


def get_tasks(task_split_name: Optional[str] = "base") -> list[Task]:
    tasks = _load_tasks_if_available(RESTAURANTE_JOAQUIN_CACHAY_TASK_SET_PATH)
    if task_split_name is None or len(tasks) == 0:
        return tasks
    task_splits = get_tasks_split()
    if len(task_splits.get("base", [])) == 0 and task_split_name == "base":
        return tasks
    if task_split_name not in task_splits:
        raise ValueError(
            f"Invalid task split name: {task_split_name}. Valid splits are: {task_splits.keys()}"
        )
    return [task for task in tasks if task.id in task_splits[task_split_name]]


def get_tasks_split() -> dict[str, list[str]]:
    split_file = (
        Path(RESTAURANTE_JOAQUIN_CACHAY_TASK_SET_PATH).parent
        / f"split_{Path(RESTAURANTE_JOAQUIN_CACHAY_TASK_SET_PATH).stem}.json"
    )
    if not split_file.exists():
        return {"base": []}
    return load_file(split_file)


