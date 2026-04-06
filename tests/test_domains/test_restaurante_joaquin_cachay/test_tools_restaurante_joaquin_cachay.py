import pytest

from tau2.domains.restaurante_joaquin_cachay.data_model import (
    RestauranteJoaquinCachayDB,
)
from tau2.domains.restaurante_joaquin_cachay.environment import get_environment
from tau2.domains.restaurante_joaquin_cachay.tools import (
    RestauranteJoaquinCachayTools,
)
from tau2.domains.restaurante_joaquin_cachay.user_data_model import RestaurantUserDB
from tau2.domains.restaurante_joaquin_cachay.user_data_model import (
    UserOrderStatusSnapshot,
)
from tau2.domains.restaurante_joaquin_cachay.user_tools import (
    RestauranteJoaquinCachayUserTools,
)
from tau2.domains.restaurante_joaquin_cachay.utils import (
    RESTAURANTE_JOAQUIN_CACHAY_DB_PATH,
)


@pytest.fixture
def assistant_tools() -> RestauranteJoaquinCachayTools:
    db = RestauranteJoaquinCachayDB.load(RESTAURANTE_JOAQUIN_CACHAY_DB_PATH)
    return RestauranteJoaquinCachayTools(db)


@pytest.fixture
def user_tools() -> RestauranteJoaquinCachayUserTools:
    db = RestauranteJoaquinCachayDB.load(RESTAURANTE_JOAQUIN_CACHAY_DB_PATH)
    user_db = RestaurantUserDB()
    env = get_environment(db=db, user_db=user_db)
    return env.user_tools


def test_get_restaurant_info_returns_profile(
    assistant_tools: RestauranteJoaquinCachayTools,
) -> None:
    info = assistant_tools.get_restaurant_info()

    assert info.name == "Restaurante Joaquin Cachay"
    assert info.delivery_enabled is True


def test_get_menu_returns_only_available_items(
    assistant_tools: RestauranteJoaquinCachayTools,
) -> None:
    menu = assistant_tools.get_menu()

    assert len(menu) > 0
    assert all(item.available for item in menu)
    assert all(item.item_id != "MAIN-003" for item in menu)


def test_get_menu_item_details_returns_expected_item(
    assistant_tools: RestauranteJoaquinCachayTools,
) -> None:
    item = assistant_tools.get_menu_item_details("MAIN-001")

    assert item.name == "Lomo Saltado"
    assert item.base_price == 42.0


def test_get_menu_item_details_raises_for_missing_item(
    assistant_tools: RestauranteJoaquinCachayTools,
) -> None:
    with pytest.raises(ValueError, match="not found"):
        assistant_tools.get_menu_item_details("MISSING")


def test_get_available_tables_filters_by_party_size(
    assistant_tools: RestauranteJoaquinCachayTools,
) -> None:
    tables = assistant_tools.get_available_tables(party_size=4)

    assert len(tables) > 0
    assert all(table.capacity >= 4 for table in tables)
    assert all(table.status == "available" for table in tables)


def test_create_customer_profile_creates_new_customer(
    assistant_tools: RestauranteJoaquinCachayTools,
) -> None:
    customer = assistant_tools.create_customer_profile(
        full_name="Lucia Mendoza",
        phone_number="+51-955-123-123",
        email="lucia.mendoza@example.com",
    )

    assert customer.customer_id == "CUST-007"
    assert assistant_tools.db.customers["CUST-007"].full_name == "Lucia Mendoza"


def test_create_customer_profile_reuses_existing_phone(
    assistant_tools: RestauranteJoaquinCachayTools,
) -> None:
    customer = assistant_tools.create_customer_profile(
        full_name="Diego Ruiz",
        phone_number="+51-944-222-222",
        email="nuevo.correo@example.com",
    )

    assert customer.customer_id == "CUST-002"
    assert assistant_tools.db.customers["CUST-002"].email == "nuevo.correo@example.com"


def test_create_reservation_assigns_table_when_available(
    assistant_tools: RestauranteJoaquinCachayTools,
) -> None:
    reservation = assistant_tools.create_reservation(
        customer_id="CUST-001",
        party_size=2,
        reservation_date="2026-04-07",
        reservation_time="20:00",
        special_requests=["quiet table"],
        preferred_area_id="AREA-001",
    )

    assert reservation.status == "confirmed"
    assert len(reservation.assigned_table_ids) == 1


def test_create_reservation_becomes_pending_for_large_party(
    assistant_tools: RestauranteJoaquinCachayTools,
) -> None:
    reservation = assistant_tools.create_reservation(
        customer_id="CUST-001",
        party_size=10,
        reservation_date="2026-04-07",
        reservation_time="21:00",
    )

    assert reservation.status == "pending"
    assert reservation.assigned_table_ids == []


def test_cancel_reservation_updates_status(
    assistant_tools: RestauranteJoaquinCachayTools,
) -> None:
    reservation = assistant_tools.cancel_reservation("RES-001")

    assert reservation.status == "cancelled"


def test_create_order_requires_items(
    assistant_tools: RestauranteJoaquinCachayTools,
) -> None:
    with pytest.raises(ValueError, match="At least one item"):
        assistant_tools.create_order(order_type="takeout", items=[], customer_id="CUST-001")


def test_create_order_raises_for_unavailable_item(
    assistant_tools: RestauranteJoaquinCachayTools,
) -> None:
    with pytest.raises(ValueError, match="unavailable"):
        assistant_tools.create_order(
            order_type="takeout",
            customer_id="CUST-001",
            items=[{"menu_item_id": "MAIN-003", "quantity": 1}],
        )


def test_create_delivery_order_returns_new_order(
    assistant_tools: RestauranteJoaquinCachayTools,
) -> None:
    order = assistant_tools.create_order(
        order_type="delivery",
        customer_id="CUST-002",
        items=[
            {"menu_item_id": "MAIN-001", "quantity": 1},
            {
                "menu_item_id": "BEV-001",
                "quantity": 1,
                "modifiers": [
                    {"modifier_group_id": "DRINK-001", "option_id": "DRINK-LARGE"}
                ],
            },
        ],
        delivery_info={
            "address": {
                "street": "Av. Los Olivos 456",
                "city": "Lima",
                "state": "Lima",
                "country": "Peru",
                "zip_code": "15023",
            },
            "contact_name": "Diego Ruiz",
            "contact_phone": "+51-944-222-222",
        },
    )

    assert order.order_id == "ORD-009"
    assert order.order_type == "delivery"
    assert order.total > 0


def test_update_order_item_status_updates_order(
    assistant_tools: RestauranteJoaquinCachayTools,
) -> None:
    order = assistant_tools.update_order_item_status(
        order_id="ORD-006",
        order_item_id="ORD-006-ITEM-01",
        status="ready",
    )

    assert order.items[0].status == "ready"


def test_record_payment_appends_payment(
    assistant_tools: RestauranteJoaquinCachayTools,
) -> None:
    order = assistant_tools.record_payment(
        order_id="ORD-002",
        payment={
            "method_type": "mobile_wallet",
            "amount": 61.78,
            "status": "paid",
            "provider": "Yape",
        },
    )

    assert len(order.payments) == 1
    assert order.payments[0].method_type == "mobile_wallet"


def test_close_order_marks_completed(
    assistant_tools: RestauranteJoaquinCachayTools,
) -> None:
    order = assistant_tools.close_order("ORD-002")

    assert order.status == "completed"
    assert order.closed_at is not None


def test_cancel_order_marks_lines_cancelled(
    assistant_tools: RestauranteJoaquinCachayTools,
) -> None:
    order = assistant_tools.cancel_order("ORD-004")

    assert order.status == "cancelled"
    assert all(item.status == "cancelled" for item in order.items)


def test_update_table_status_changes_table(
    assistant_tools: RestauranteJoaquinCachayTools,
) -> None:
    table = assistant_tools.update_table_status("TBL-006", "cleaning")

    assert table.status == "cleaning"


def test_submit_review_creates_review(
    assistant_tools: RestauranteJoaquinCachayTools,
) -> None:
    review = assistant_tools.submit_review(
        rating=5,
        comment="Muy buen servicio.",
        customer_id="CUST-001",
        order_id="ORD-001",
    )

    assert review.review_id == "REV-003"
    assert review.rating == 5


def test_calculate_rejects_invalid_expression(
    assistant_tools: RestauranteJoaquinCachayTools,
) -> None:
    with pytest.raises(ValueError, match="Invalid characters"):
        assistant_tools.calculate("2 + os.system('rm -rf /')")


def test_user_tools_view_profile_returns_identity(
    user_tools: RestauranteJoaquinCachayUserTools,
) -> None:
    profile = user_tools.view_profile()

    assert "identity" in profile
    assert "preferences" in profile


def test_user_tools_update_profile_updates_identity(
    user_tools: RestauranteJoaquinCachayUserTools,
) -> None:
    identity = user_tools.update_profile(
        name="Lucia Mendoza",
        phone_number="+51-955-123-123",
        email="lucia.mendoza@example.com",
    )

    assert identity["name"] == "Lucia Mendoza"
    assert identity["phone_number"] == "+51-955-123-123"


def test_user_tools_browse_menu_returns_visible_items(
    user_tools: RestauranteJoaquinCachayUserTools,
) -> None:
    items = user_tools.browse_menu()

    assert len(items) > 0
    assert all(item.available for item in items)


def test_user_tools_add_and_remove_item_from_cart(
    user_tools: RestauranteJoaquinCachayUserTools,
) -> None:
    cart_item = user_tools.add_item_to_cart("MAIN-001", quantity=2)

    assert cart_item.cart_item_id == "CART-001"
    assert len(user_tools.view_cart()) == 1

    cart = user_tools.remove_item_from_cart("CART-001")

    assert cart == []


def test_user_tools_clear_cart_empties_cart(
    user_tools: RestauranteJoaquinCachayUserTools,
) -> None:
    user_tools.add_item_to_cart("ENT-001", quantity=1)
    message = user_tools.clear_cart()

    assert message == "Cart cleared."
    assert user_tools.view_cart() == []


def test_user_tools_request_and_confirm_reservation(
    user_tools: RestauranteJoaquinCachayUserTools,
) -> None:
    request = user_tools.request_reservation(
        reservation_date="2026-04-03",
        reservation_time="20:00",
        party_size=4,
    )
    confirmed = user_tools.confirm_reservation_request()

    assert request.party_size == 4
    assert confirmed.confirmed is True


def test_user_tools_submit_order_requires_non_empty_cart(
    user_tools: RestauranteJoaquinCachayUserTools,
) -> None:
    with pytest.raises(ValueError, match="cart is empty"):
        user_tools.submit_order(order_type="takeout")


def test_user_tools_submit_order_creates_order_request(
    user_tools: RestauranteJoaquinCachayUserTools,
) -> None:
    user_tools.add_item_to_cart("ENT-001", quantity=1)
    order_request = user_tools.submit_order(order_type="takeout")

    assert order_request.order_type == "takeout"
    assert order_request.submitted is True


def test_user_tools_request_and_confirm_payment(
    user_tools: RestauranteJoaquinCachayUserTools,
) -> None:
    user_tools.db.active_order_id = "ORD-002"
    user_tools.db.tracked_orders["ORD-002"] = UserOrderStatusSnapshot(
        order_id="ORD-002",
        order_type="delivery",
        status="ready",
        total=61.78,
        table_id=None,
        created_at="2026-03-31T19:20:00",
        payment_status="unpaid",
    )

    intent = user_tools.request_payment(
        method_type="mobile_wallet",
        metadata={"provider": "Yape"},
    )
    confirmed = user_tools.confirm_payment()

    assert intent.order_id == "ORD-002"
    assert confirmed.confirmed is True


def test_user_tools_set_presence_updates_surroundings(
    user_tools: RestauranteJoaquinCachayUserTools,
) -> None:
    surroundings = user_tools.set_presence(True, seated_table_id="TBL-004")

    assert surroundings["currently_in_restaurant"] is True
    assert surroundings["seated_table_id"] == "TBL-004"
