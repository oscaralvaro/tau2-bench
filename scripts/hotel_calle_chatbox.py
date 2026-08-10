from tau2.domains.hotel_calle.data_model import HotelCalleDB
from tau2.domains.hotel_calle.tools import HotelCalleTools
from tau2.domains.hotel_calle.utils import HOTEL_CALLE_DB_PATH


HELP_TEXT = """
Comandos disponibles:
- ayuda
- hotel
- habitaciones
- disponibilidad <room_type_id> <check_in> <check_out> <guests>
- reservar <guest_name>|<room_type_id>|<check_in>|<check_out>|<guests>|<special_request>
- reservar <guest_name>|<room_type_id>|<check_in>|<check_out>|<guests>|<special_request>|<guest_email>|<guest_phone>
- reserva <reservation_id>
- salir
""".strip()


def print_hotel_info(tools: HotelCalleTools) -> None:
    info = tools.get_hotel_info()
    print(
        f"{info['hotel_name']} en {info['city']}. "
        f"Check-in: {info['check_in_time']}. "
        f"Check-out: {info['check_out_time']}. "
        f"Desayuno incluido: {'si' if info['breakfast_included'] else 'no'}."
    )


def print_room_catalog(tools: HotelCalleTools) -> None:
    for room in tools.get_room_catalog():
        amenities = ", ".join(room.amenities)
        print(
            f"{room.room_type_id}: {room.name} | S/ {room.price_per_night:.2f} por noche | "
            f"max {room.max_guests} huespedes | camas: {room.bed_configuration} | "
            f"disponibles {room.available_rooms} | {amenities}"
        )


def handle_availability(command: str, tools: HotelCalleTools) -> None:
    parts = command.split()
    if len(parts) != 5:
        raise ValueError("Usa: disponibilidad <room_type_id> <check_in> <check_out> <guests>")
    _, room_type_id, check_in, check_out, guests = parts
    result = tools.check_room_availability(
        room_type_id=room_type_id,
        check_in_date=check_in,
        check_out_date=check_out,
        guests=int(guests),
    )
    print(
        f"Habitacion: {result['room_type_name']} | disponible: {result['available']} | "
        f"noches: {result['nights']} | total estimado: S/ {result['estimated_total']:.2f}"
    )


def handle_reservation(command: str, tools: HotelCalleTools) -> None:
    payload = command[len("reservar ") :]
    fields = [item.strip() for item in payload.split("|")]
    if len(fields) not in (6, 8):
        raise ValueError(
            "Usa: reservar <guest_name>|<room_type_id>|<check_in>|<check_out>|<guests>|<special_request> "
            "o agrega |<guest_email>|<guest_phone>"
        )
    guest_email = fields[6] if len(fields) == 8 else ""
    guest_phone = fields[7] if len(fields) == 8 else ""
    reservation = tools.create_reservation(
        guest_name=fields[0],
        room_type_id=fields[1],
        check_in_date=fields[2],
        check_out_date=fields[3],
        guests=int(fields[4]),
        special_request=fields[5],
        guest_email=guest_email,
        guest_phone=guest_phone,
    )
    print(
        f"Reserva creada: {reservation.reservation_id} | cuarto {reservation.room_number} | {reservation.room_type_name} | "
        f"{reservation.check_in_date} a {reservation.check_out_date} | "
        f"total S/ {reservation.total_price:.2f}"
    )


def handle_get_reservation(command: str, tools: HotelCalleTools) -> None:
    parts = command.split()
    if len(parts) != 2:
        raise ValueError("Usa: reserva <reservation_id>")
    reservation = tools.get_reservation(parts[1])
    print(
        f"{reservation.reservation_id}: {reservation.guest_name} | cuarto {reservation.room_number} | {reservation.room_type_name} | "
        f"{reservation.check_in_date} a {reservation.check_out_date} | estado {reservation.status}"
    )


def main() -> None:
    db = HotelCalleDB.load(HOTEL_CALLE_DB_PATH)
    tools = HotelCalleTools(db)

    print("Hotel Calle Chatbox")
    print("Escribe 'ayuda' para ver los comandos.")

    while True:
        command = input("tu> ").strip()
        if not command:
            continue
        try:
            if command == "salir":
                print("Hasta luego.")
                break
            if command == "ayuda":
                print(HELP_TEXT)
            elif command == "hotel":
                print_hotel_info(tools)
            elif command == "habitaciones":
                print_room_catalog(tools)
            elif command.startswith("disponibilidad "):
                handle_availability(command, tools)
            elif command.startswith("reservar "):
                handle_reservation(command, tools)
            elif command.startswith("reserva "):
                handle_get_reservation(command, tools)
            else:
                print("No entendi el comando. Escribe 'ayuda'.")
        except ValueError as exc:
            print(f"Error: {exc}")


if __name__ == "__main__":
    main()
