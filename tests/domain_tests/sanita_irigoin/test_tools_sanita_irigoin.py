import pytest
from tau2.domains.sanita_irigoin.data_model import (
    ArrozDB, User, Suelo, Cultivo, Producto, Pedido, Inventario, Diagnostico
)
from tau2.domains.sanita_irigoin.tools import ArrozToolKit


@pytest.fixture
def db():
    database = ArrozDB()
    database.users = {
        "U001": User(user_id="U001", nombre="Carlos Ramirez", tipo_cliente="frecuente"),
        "U002": User(user_id="U002", nombre="Maria Lopez",    tipo_cliente="nuevo"),
    }
    database.suelos = {
        "S001": Suelo(suelo_id="S001", nombre="aluvial-arcilloso", ph=6.5, nivel_nutrientes="medio"),
    }
    database.cultivos = {
        "C001": Cultivo(cultivo_id="C001", etapa="siembra"),
    }
    database.productos = {
        "P001": Producto(producto_id="P001", nombre="Urea 46%",     tipo="fertilizante", composicion="N 46%",        precio=85.0,  stock=50),
        "P002": Producto(producto_id="P002", nombre="NPK 20-20-20", tipo="fertilizante", composicion="N20 P20 K20",  precio=120.0, stock=0),
        "P003": Producto(producto_id="P003", nombre="Gramoxone",     tipo="herbicida",    composicion="Paraquat 20%", precio=55.0,  stock=10),
    }
    database.pedidos = {
        "ORD-001": Pedido(
            order_id="ORD-001", user_id="U001", producto_id="P001",
            cantidad=5, metodo_pago="transferencia",
            estado_pago="credito", estado_entrega="entregado"
        ),
    }
    database.diagnosticos = {
        "D001": Diagnostico(diagnostico_id="D001", suelo_id="S001", cultivo_id="C001", problema="bajo_nutrientes"),
    }
    return database


@pytest.fixture
def toolkit(db):
    return ArrozToolKit(db=db)


def test_get_user_details_existente(toolkit):
    r = toolkit.get_user_details("U001")
    assert r["user_id"] == "U001"
    assert r["tipo_cliente"] == "frecuente"

def test_get_user_details_no_existe(toolkit):
    assert "error" in toolkit.get_user_details("U999")

def test_get_producto_details_existente(toolkit):
    r = toolkit.get_producto_details("P001")
    assert r["nombre"] == "Urea 46%"

def test_get_producto_details_no_existe(toolkit):
    assert "error" in toolkit.get_producto_details("P999")

def test_check_stock_disponible(toolkit):
    assert toolkit.check_stock("P001")["disponible"] is True

def test_check_stock_sin_stock(toolkit):
    assert toolkit.check_stock("P002")["disponible"] is False

def test_check_stock_no_existe(toolkit):
    assert "error" in toolkit.check_stock("P999")

def test_get_soil_details_existente(toolkit):
    assert toolkit.get_soil_details("S001")["suelo_id"] == "S001"

def test_get_soil_details_no_existe(toolkit):
    assert "error" in toolkit.get_soil_details("S999")

def test_get_crop_details_existente(toolkit):
    assert toolkit.get_crop_details("C001")["etapa"] == "siembra"

def test_get_crop_details_no_existe(toolkit):
    assert "error" in toolkit.get_crop_details("C999")

def test_recommend_fertilizer_exitoso(toolkit):
    r = toolkit.recommend_fertilizer("D001", presupuesto=100.0)
    assert "recomendacion" in r
    assert r["recomendacion"]["precio"] <= 100.0

def test_recommend_fertilizer_presupuesto_insuficiente(toolkit):
    assert "error" in toolkit.recommend_fertilizer("D001", presupuesto=5.0)

def test_recommend_fertilizer_no_existe(toolkit):
    assert "error" in toolkit.recommend_fertilizer("D999", presupuesto=100.0)

def test_suggest_alternative_exitoso(toolkit):
    r = toolkit.suggest_alternative("P002")
    assert "alternativa" in r
    assert r["alternativa"]["stock"] > 0

def test_suggest_alternative_no_existe(toolkit):
    assert "error" in toolkit.suggest_alternative("P999")

def test_validate_budget_viable(toolkit):
    assert toolkit.validate_budget("P001", presupuesto=100.0)["viable"] is True

def test_validate_budget_no_viable(toolkit):
    assert toolkit.validate_budget("P001", presupuesto=50.0)["viable"] is False

def test_validate_budget_no_existe(toolkit):
    assert "error" in toolkit.validate_budget("P999", presupuesto=100.0)

def test_create_order_exitoso_contado(toolkit):
    assert "pedido_creado" in toolkit.create_order("U002", "P001", 2, "efectivo", "al contado")

def test_create_order_frecuente_credito(toolkit):
    assert "pedido_creado" in toolkit.create_order("U001", "P001", 2, "transferencia", "credito")

def test_create_order_nuevo_credito_rechazado(toolkit):
    assert "error" in toolkit.create_order("U002", "P001", 2, "transferencia", "credito")

def test_create_order_sin_stock(toolkit):
    assert "error" in toolkit.create_order("U001", "P002", 1, "efectivo", "al contado")

def test_create_order_cantidad_excede_stock(toolkit):
    assert "error" in toolkit.create_order("U001", "P001", 9999, "efectivo", "al contado")

def test_create_order_usuario_no_existe(toolkit):
    assert "error" in toolkit.create_order("U999", "P001", 1, "efectivo", "al contado")

def test_create_order_descuenta_stock(toolkit):
    stock_antes = toolkit.db.productos["P001"].stock
    toolkit.create_order("U001", "P001", 3, "efectivo", "al contado")
    assert toolkit.db.productos["P001"].stock == stock_antes - 3

def test_get_order_details_existente(toolkit):
    assert toolkit.get_order_details("ORD-001")["order_id"] == "ORD-001"

def test_get_order_details_no_existe(toolkit):
    assert "error" in toolkit.get_order_details("ORD-999")

def test_escalate_to_human(toolkit):
    r = toolkit.escalate_to_human("Cliente solicita atención humana")
    assert r["escalado"] is True