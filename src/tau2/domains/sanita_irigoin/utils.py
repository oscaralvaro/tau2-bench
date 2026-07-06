from pathlib import Path

DOMAIN_DIR = Path(__file__).parent
DATA_DIR = Path(__file__).parents[4] / "data" / "tau2" / "domains" / "sanita_irigoin"

DB_PATH = DATA_DIR / "db.json"
POLICY_PATH = DATA_DIR / "policy.md"
TASKS_PATH = DATA_DIR / "tasks.json"
SPLIT_TASKS_PATH = DATA_DIR / "split_tasks.json"


if __name__ == "__main__":
    from tau2.domains.sanita_irigoin.data_model import (
        ArrozDB, User, Suelo, Cultivo, Producto,
        Pedido, Inventario, Diagnostico
    )

    db = ArrozDB()

    db.users = {
        "U001": User(user_id="U001", nombre="Carlos Ramirez", tipo_cliente="frecuente"),
        "U002": User(user_id="U002", nombre="Maria Lopez",    tipo_cliente="nuevo"),
        "U003": User(user_id="U003", nombre="Jose Flores",    tipo_cliente="frecuente"),
        "U004": User(user_id="U004", nombre="Ana Torres",     tipo_cliente="nuevo"),
        "U005": User(user_id="U005", nombre="Luis Mendoza",   tipo_cliente="frecuente"),
    }

    db.suelos = {
        "S001": Suelo(suelo_id="S001", nombre="aluvial-arcilloso",        ph=6.5, nivel_nutrientes="medio"),
        "S002": Suelo(suelo_id="S002", nombre="salitroso",                ph=8.2, nivel_nutrientes="bajo"),
        "S003": Suelo(suelo_id="S003", nombre="aluvial-franco-arcilloso", ph=6.8, nivel_nutrientes="alto"),
    }

    db.cultivos = {
        "C001": Cultivo(cultivo_id="C001", etapa="siembra"),
        "C002": Cultivo(cultivo_id="C002", etapa="crecimiento"),
        "C003": Cultivo(cultivo_id="C003", etapa="almacigo"),
        "C004": Cultivo(cultivo_id="C004", etapa="cosecha"),
    }

    db.productos = {
        "P001": Producto(producto_id="P001", nombre="Urea 46%",          tipo="fertilizante", composicion="N 46%",           precio=85.0,  stock=50),
        "P002": Producto(producto_id="P002", nombre="NPK 20-20-20",      tipo="fertilizante", composicion="N20 P20 K20",      precio=120.0, stock=30),
        "P003": Producto(producto_id="P003", nombre="Sulfato de Amonio", tipo="fertilizante", composicion="N 21% S 24%",      precio=70.0,  stock=0),
        "P004": Producto(producto_id="P004", nombre="Gramoxone",          tipo="herbicida",    composicion="Paraquat 20%",     precio=55.0,  stock=20),
        "P005": Producto(producto_id="P005", nombre="Cipermetrina",       tipo="plaguicida",   composicion="Cipermetrina 25%", precio=45.0,  stock=15),
        "P006": Producto(producto_id="P006", nombre="NPK 15-15-15",      tipo="fertilizante", composicion="N15 P15 K15",      precio=95.0,  stock=25),
        "P007": Producto(producto_id="P007", nombre="Glifosato",          tipo="herbicida",    composicion="Glifosato 48%",    precio=40.0,  stock=0),
        "P008": Producto(producto_id="P008", nombre="Clorpirifos",        tipo="plaguicida",   composicion="Clorpirifos 48%",  precio=60.0,  stock=10),
    }

    db.inventario = {
        "P001": Inventario(producto_id="P001", stock_actual=50, stock_minimo=10),
        "P002": Inventario(producto_id="P002", stock_actual=30, stock_minimo=5),
        "P003": Inventario(producto_id="P003", stock_actual=0,  stock_minimo=10),
        "P004": Inventario(producto_id="P004", stock_actual=20, stock_minimo=5),
        "P005": Inventario(producto_id="P005", stock_actual=15, stock_minimo=5),
        "P006": Inventario(producto_id="P006", stock_actual=25, stock_minimo=5),
        "P007": Inventario(producto_id="P007", stock_actual=0,  stock_minimo=5),
        "P008": Inventario(producto_id="P008", stock_actual=10, stock_minimo=3),
    }

    db.diagnosticos = {
        "D001": Diagnostico(diagnostico_id="D001", suelo_id="S001", cultivo_id="C001", problema="bajo_nutrientes"),
        "D002": Diagnostico(diagnostico_id="D002", suelo_id="S002", cultivo_id="C002", problema="salinidad"),
        "D003": Diagnostico(diagnostico_id="D003", suelo_id="S003", cultivo_id="C003", problema="plagas"),
        "D004": Diagnostico(diagnostico_id="D004", suelo_id="S001", cultivo_id="C004", problema="maleza"),
    }

    db.pedidos = {
        "ORD-001": Pedido(
            order_id="ORD-001", user_id="U001", producto_id="P001",
            cantidad=5, metodo_pago="transferencia",
            estado_pago="credito", estado_entrega="entregado"
        ),
        "ORD-002": Pedido(
            order_id="ORD-002", user_id="U002", producto_id="P004",
            cantidad=2, metodo_pago="efectivo",
            estado_pago="al contado", estado_entrega="pendiente"
        ),
    }

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    db.dump(DB_PATH)
    print(f"✅ db.json generado en: {DB_PATH}")