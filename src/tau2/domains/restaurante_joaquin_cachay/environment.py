import hashlib
import json
from pathlib import Path
from typing import Optional

from tau2.data_model.message import (
    AssistantMessage,
    Message,
    ToolCall,
    ToolMessage,
    UserMessage,
)
from tau2.data_model.tasks import InitializationData, Task
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
    UserSMSMessage,
)
from tau2.domains.restaurante_joaquin_cachay.user_tools import (
    RestauranteJoaquinCachayUserTools,
)
from tau2.domains.restaurante_joaquin_cachay.utils import (
    RESTAURANTE_JOAQUIN_CACHAY_DB_PATH,
    RESTAURANTE_JOAQUIN_CACHAY_POLICY_PATH,
    RESTAURANTE_JOAQUIN_CACHAY_POLICY_RAG_PATH,
    RESTAURANTE_JOAQUIN_CACHAY_POLICY_SOLO_PATH,
    RESTAURANTE_JOAQUIN_CACHAY_TASK_SET_PATH,
    RESTAURANTE_JOAQUIN_CACHAY_USER_DB_PATH,
)
from tau2.environment.environment import Environment
from tau2.environment.rag import (
    THINK_INSTRUCTION,
    ChromaPolicyIndex,
    _make_gemini_embed_fn,
    get_chunks,
)
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

    def _sync_sms_state(self) -> None:
        messages: list[UserSMSMessage] = []
        for challenge in self.tools._sms_challenges.values():
            messages.append(
                UserSMSMessage(
                    message_id=challenge.challenge_id,
                    phone_number=challenge.phone_number,
                    role=challenge.role,
                    purpose=challenge.purpose,
                    reference_id=challenge.reference_id,
                    code=challenge.code,
                    sent_at=challenge.sent_at,
                    consumed=challenge.status == "verified",
                )
            )
        self.user_tools.db.sms_inbox = sorted(messages, key=lambda message: message.message_id)

    def sync_tools(self):
        self._sync_visible_menu()
        self._ensure_customer_identity()
        self._sync_reservation_request()
        self._sync_order_request()
        self._sync_payment_intent()
        self._sync_tracked_state()
        self._sync_sms_state()

    def _iter_tool_action_pairs(
        self, message_history: list[Message]
    ) -> list[tuple[ToolCall, ToolMessage]]:
        actions: list[tuple[ToolCall, ToolMessage]] = []
        messages = list(message_history)
        idx = 0
        while idx < len(messages):
            message = messages[idx]
            if isinstance(message, (AssistantMessage, UserMessage)) and message.is_tool_call():
                for tool_call in message.tool_calls:
                    idx += 1
                    if idx >= len(messages) or not isinstance(messages[idx], ToolMessage):
                        return actions
                    tool_message = messages[idx]
                    if tool_call.id == tool_message.id:
                        actions.append((tool_call, tool_message))
            idx += 1
        return actions

    def _align_policy_replay_context(self, message_history: list[Message]) -> None:
        if not isinstance(self.tools, RestauranteJoaquinCachayTools):
            return
        if not self.tools._policy_text:
            return

        policy_digest = hashlib.sha1(
            self.tools._policy_text.encode("utf-8")
        ).hexdigest()
        cache_dir = (
            self.tools._policy_result_cache_path.parent
            if self.tools._policy_result_cache_path is not None
            else _POLICY_CACHE_DIR
        )

        for tool_call, tool_message in self._iter_tool_action_pairs(message_history):
            if tool_call.name != "retrieve_policy":
                continue
            query = tool_call.arguments.get("query")
            if not isinstance(query, str):
                continue
            replay_context = self.tools.find_policy_replay_context(
                query=query.strip(),
                expected_content=tool_message.content,
                cache_dir=cache_dir,
                policy_digest=policy_digest,
            )
            if replay_context is None:
                continue
            policy_cache_key, retrieval_k, cache_path = replay_context
            self.tools.configure_policy_replay_context(
                policy_cache_key=policy_cache_key,
                retrieval_k=retrieval_k,
                policy_result_cache_path=cache_path,
            )
            return

    def set_state(
        self,
        initialization_data: Optional[InitializationData],
        initialization_actions,
        message_history: list[Message],
    ):
        self._align_policy_replay_context(message_history)
        super().set_state(
            initialization_data=initialization_data,
            initialization_actions=initialization_actions,
            message_history=message_history,
        )


def _load_text_or_default(path: Path, default_text: str) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8")
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


_POLICY_INDEX_CACHE: dict[tuple[str, str], ChromaPolicyIndex] = {}
_POLICY_CACHE_DIR = Path(RESTAURANTE_JOAQUIN_CACHAY_POLICY_PATH).parent / "cache"


def _make_policy_cache_key(policy_text: str, chunking_strategy: str) -> str:
    digest = hashlib.sha1(policy_text.encode("utf-8")).hexdigest()
    return f"{chunking_strategy}:{digest}"


def _get_policy_chunk_cache_path(policy_text: str, chunking_strategy: str) -> Path:
    digest = hashlib.sha1(policy_text.encode("utf-8")).hexdigest()
    return _POLICY_CACHE_DIR / f"policy_chunks_{chunking_strategy}_{digest}.json"


def _get_policy_result_cache_path(policy_text: str, chunking_strategy: str) -> Path:
    digest = hashlib.sha1(policy_text.encode("utf-8")).hexdigest()
    return _POLICY_CACHE_DIR / f"policy_results_{chunking_strategy}_{digest}.json"


def _make_persisted_embed_fn(policy_text: str, chunking_strategy: str):
    chunks = get_chunks(policy_text, chunking_strategy)
    cache_path = _get_policy_chunk_cache_path(policy_text, chunking_strategy)
    base_embed_fn = _make_gemini_embed_fn()
    cached_embeddings: Optional[list[list[float]]] = None

    def embed_fn(texts: list[str]) -> list[list[float]]:
        nonlocal cached_embeddings

        if texts == chunks:
            if cached_embeddings is None and cache_path.exists():
                try:
                    payload = json.loads(cache_path.read_text(encoding="utf-8"))
                    if payload.get("chunks") == chunks:
                        embeddings = payload.get("embeddings")
                        if isinstance(embeddings, list) and len(embeddings) == len(chunks):
                            cached_embeddings = embeddings
                except (OSError, json.JSONDecodeError):
                    cached_embeddings = None

            if cached_embeddings is not None:
                return cached_embeddings

            embeddings = base_embed_fn(texts)
            try:
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                cache_path.write_text(
                    json.dumps(
                        {
                            "strategy": chunking_strategy,
                            "policy_hash": hashlib.sha1(
                                policy_text.encode("utf-8")
                            ).hexdigest(),
                            "chunks": chunks,
                            "embeddings": embeddings,
                        }
                    ),
                    encoding="utf-8",
                )
            except OSError:
                pass
            cached_embeddings = embeddings
            return embeddings

        return base_embed_fn(texts)

    return embed_fn


def _get_cached_policy_index(
    policy_text: str,
    chunking_strategy: str,
) -> ChromaPolicyIndex:
    cache_key = (chunking_strategy, hashlib.sha1(policy_text.encode("utf-8")).hexdigest())
    policy_index = _POLICY_INDEX_CACHE.get(cache_key)
    if policy_index is None:
        policy_index = ChromaPolicyIndex(
            policy_text,
            strategy=chunking_strategy,
            _embed_fn=_make_persisted_embed_fn(policy_text, chunking_strategy),
        )
        _POLICY_INDEX_CACHE[cache_key] = policy_index
    return policy_index


def get_environment(
    db: Optional[RestauranteJoaquinCachayDB] = None,
    user_db: Optional[RestaurantUserDB] = None,
    solo_mode: bool = False,
    chunking_strategy: str = "headers",
    retrieval_k: int = 3,
    use_think: bool = False,
    use_rag: bool = False,
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
    policy_source_path = (
        RESTAURANTE_JOAQUIN_CACHAY_POLICY_SOLO_PATH
        if solo_mode
        else RESTAURANTE_JOAQUIN_CACHAY_POLICY_PATH
    )
    full_policy = _load_text_or_default(
        policy_source_path,
        "You are the restaurant assistant. Help customers with menu questions, reservations, orders, and payments while keeping the restaurant database accurate.",
    )
    policy_cache_key = _make_policy_cache_key(full_policy, chunking_strategy)
    policy_result_cache_path = _get_policy_result_cache_path(
        full_policy,
        chunking_strategy,
    )
    policy = full_policy
    if use_rag:
        policy_index = _get_cached_policy_index(
            full_policy,
            chunking_strategy=chunking_strategy,
        )
        tools = RestauranteJoaquinCachayTools(
            db,
            policy_index=policy_index,
            policy_text=full_policy,
            policy_cache_key=policy_cache_key,
            chunking_strategy=chunking_strategy,
            retrieval_k=retrieval_k,
            expose_policy_tools=True,
            expose_think_tool=use_think,
            policy_result_cache_path=str(policy_result_cache_path),
        )
        if not solo_mode:
            policy = _load_text_or_default(
                RESTAURANTE_JOAQUIN_CACHAY_POLICY_RAG_PATH,
                full_policy,
            )
        if use_think:
            policy = policy + THINK_INSTRUCTION
    else:
        tools = RestauranteJoaquinCachayTools(
            db,
            policy_text=full_policy,
            policy_cache_key=policy_cache_key,
            chunking_strategy=chunking_strategy,
            expose_policy_tools=False,
            expose_think_tool=False,
            policy_result_cache_path=str(policy_result_cache_path),
        )
    user_tools = RestauranteJoaquinCachayUserTools(user_db)
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


