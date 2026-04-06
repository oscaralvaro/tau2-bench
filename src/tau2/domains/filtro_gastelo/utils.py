from tau2.utils.utils import DATA_DIR
from tau2.domains.filtro_gastelo.data_model import FiltrosDB, Customer, Filter

FILTRO_DATA_DIR = DATA_DIR / "tau2" / "domains" / "filtro_gastelo"
FILTRO_POLICY_PATH = FILTRO_DATA_DIR / "policy.md"
FILTRO_TASK_SET_PATH = FILTRO_DATA_DIR / "tasks.json"
FILTRO_DB_PATH = FILTRO_DATA_DIR / "db.json"


def generate_db():
    customers = {
        "C-001": Customer(customer_id="C-001", name="Francesco Gastelo", phone="950123456", past_orders=45),
        "C-002": Customer(customer_id="C-002", name="Luis Ramos", phone="940888777", past_orders=25),
        "C-003": Customer(customer_id="C-003", name="Maria Abad", phone="920111222", past_orders=8),
        "C-004": Customer(customer_id="C-004", name="Jorge Nizama", phone="960333444", past_orders=0),
        "C-005": Customer(customer_id="C-005", name="Ana Castillo", phone="910555666", past_orders=15),
    }

    inventory = {
        # Filtros con stock (Regla 1 - Entrega Inmediata)
        "JD-101": Filter(item_id="JD-101", brand="John Deere", name="Filtro Aceite 5075E", type="Aceite", price=185.5, stock=12),
        "CAT-201": Filter(item_id="CAT-201", brand="Caterpillar", name="Filtro Aire Primario", type="Aire", price=320.0, stock=8),
        "FG-301": Filter(item_id="FG-301", brand="Fleetguard", name="Filtro Combustible", type="Combustible", price=145.0, stock=20),
        "DON-401": Filter(item_id="DON-401", brand="Donaldson", name="Filtro Hidráulico", type="Hidráulico", price=295.0, stock=6),
        "KOM-601": Filter(item_id="KOM-601", brand="Komatsu", name="Filtro Aceite PC200", type="Aceite", price=275.0, stock=10),
        "CASE-501": Filter(item_id="CASE-501", brand="Case IH", name="Filtro Aceite Magnum", type="Aceite", price=210.0, stock=12),
        "FG-302": Filter(item_id="FG-302", brand="Fleetguard", name="Separador de Agua", type="Combustible", price=195.0, stock=10),
        "DON-402": Filter(item_id="DON-402", brand="Donaldson", name="Filtro Aire Secundario", type="Aire", price=130.0, stock=15),
        "JD-102": Filter(item_id="JD-102", brand="John Deere", name="Filtro Aire Cabina", type="Aire", price=140.0, stock=8),
        "CAT-202": Filter(item_id="CAT-202", brand="Caterpillar", name="Filtro Combustible 320D", type="Combustible", price=220.0, stock=7),

        # Filtros agotados con equivalente (Regla 7)
        "JD-999": Filter(item_id="JD-999", brand="John Deere", name="Filtro Especial Agotado", type="Aceite", price=290.0, stock=0, equivalent_id="DON-999"),
        "DON-999": Filter(item_id="DON-999", brand="Donaldson", name="Reemplazo Donaldson", type="Aceite", price=265.0, stock=5, equivalent_id="JD-999"),
        "CAT-888": Filter(item_id="CAT-888", brand="Caterpillar", name="Filtro Hidr. Pesado", type="Hidráulico", price=530.0, stock=0, equivalent_id="FG-888"),
        "FG-888": Filter(item_id="FG-888", brand="Fleetguard", name="Reemplazo Fleetguard", type="Hidráulico", price=495.0, stock=4, equivalent_id="CAT-888"),

        # Filtros agotados sin equivalente (Regla 2 - Pedido a Proveedor)
        "JD-000": Filter(item_id="JD-000", brand="John Deere", name="Filtro Cosechadora S700", type="Aceite", price=650.0, stock=0),
        "CAT-000": Filter(item_id="CAT-000", brand="Caterpillar", name="Filtro Respiradero", type="Aire", price=95.0, stock=0),
        "KOM-000": Filter(item_id="KOM-000", brand="Komatsu", name="Filtro Transmisión", type="Hidráulico", price=380.0, stock=0),
        "CASE-000": Filter(item_id="CASE-000", brand="Case IH", name="Filtro Especial Raro", type="Hidráulico", price=410.0, stock=0),
        "FG-000": Filter(item_id="FG-000", brand="Fleetguard", name="Filtro AdBlue", type="Químico", price=245.0, stock=0),
        "DON-000": Filter(item_id="DON-000", brand="Donaldson", name="Filtro Especial Minería", type="Aire", price=950.0, stock=0),
    }

    # Creamos el objeto DB
    db = FiltrosDB(customers=customers, inventory=inventory, provider_orders={})

    # Creamos la carpeta si no existe
    FILTRO_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Generamos el db.json
    db.dump(FILTRO_DB_PATH)
    print(f"✅ db.json generado en: {FILTRO_DB_PATH}")


if __name__ == "__main__":
    generate_db()