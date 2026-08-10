import pytest
from tau2.domains.cable_calderon.data_model import (
    CableCalderonDB, Cliente, ContactoAutorizado,
    Plan, Servicio, OrdenInstalacion, Reclamo
)
from tau2.domains.cable_calderon.tools import CableCalderonToolKit


@pytest.fixture
def db():
    """Base de datos de prueba con datos mínimos."""
    return CableCalderonDB(
        clientes={
            "C001": Cliente(
                cliente_id="C001",
                nombre_titular="Maria Fernanda Torres Vega",
                telefono="987654321",
                email="mftorres@gmail.com",
                direccion="Av. Los Pinos 123, Piura",
                tiene_deuda=False,
                monto_deuda=0.0,
                contactos_autorizados=[
                    ContactoAutorizado(nombre="Carlos Torres", telefono="912345678")
                ]
            ),
            "C002": Cliente(
                cliente_id="C002",
                nombre_titular="Roberto Silva Paredes",
                telefono="976543210",
                email="rsilva@hotmail.com",
                direccion="Jr. Tacna 456, Piura",
                tiene_deuda=True,
                monto_deuda=85.50,
                contactos_autorizados=[]
            ),
            "C003": Cliente(
                cliente_id="C003",
                nombre_titular="Ana Lucia Ramirez Diaz",
                telefono="965432109",
                email="anaramirez@gmail.com",
                direccion="Calle Lima 789, Piura",
                tiene_deuda=False,
                monto_deuda=0.0,
                contactos_autorizados=[]
            ),
        },
        planes={
            "P001": Plan(plan_id="P001", nombre="Internet Básico", tipo="internet", velocidad_mbps=50, canales=None, precio_mensual=59.90, nivel=1),
            "P002": Plan(plan_id="P002", nombre="Internet Pro", tipo="internet", velocidad_mbps=100, canales=None, precio_mensual=89.90, nivel=2),
            "P003": Plan(plan_id="P003", nombre="Internet Premium", tipo="internet", velocidad_mbps=200, canales=None, precio_mensual=129.90, nivel=3),
            "P004": Plan(plan_id="P004", nombre="Cable Básico", tipo="cable", velocidad_mbps=None, canales=60, precio_mensual=49.90, nivel=1),
        },
        servicios={
            "S001": Servicio(servicio_id="S001", cliente_id="C001", plan_id="P001", estado="activo", fecha_inicio="2025-01-15", fecha_vencimiento="2026-04-15"),
            "S002": Servicio(servicio_id="S002", cliente_id="C002", plan_id="P001", estado="suspendido", fecha_inicio="2024-08-01", fecha_vencimiento="2026-03-01"),
            "S003": Servicio(servicio_id="S003", cliente_id="C003", plan_id="P002", estado="activo", fecha_inicio="2025-03-10", fecha_vencimiento="2026-04-10"),
        },
        ordenes={
            "O001": OrdenInstalacion(orden_id="O001", cliente_id="C001", tipo="mantenimiento", fecha_programada="2026-04-05", hora_programada="10:00", tecnico_asignado="Juan Perez", estado="confirmada"),
            "O002": OrdenInstalacion(orden_id="O002", cliente_id="C003", tipo="instalacion_nueva", fecha_programada="2026-04-02", hora_programada="14:00", tecnico_asignado=None, estado="pendiente"),
            "O003": OrdenInstalacion(orden_id="O003", cliente_id="C001", tipo="instalacion_nueva", fecha_programada="2026-03-31", hora_programada="09:00", tecnico_asignado="Mario Rios", estado="confirmada"),
        },
        reclamos={
            "R001": Reclamo(reclamo_id="R001", cliente_id="C001", tipo="señal", descripcion="Intermitencia en la señal", estado="en_proceso", fecha_creacion="2026-03-25", fecha_resolucion=None),
            "R002": Reclamo(reclamo_id="R002", cliente_id="C003", tipo="facturacion", descripcion="Cobro duplicado", estado="abierto", fecha_creacion="2026-03-28", fecha_resolucion=None),
        }
    )


@pytest.fixture
def toolkit(db):
    return CableCalderonToolKit(db=db)


# ─── get_client_details ───────────────────────────────────────────────────────

def test_get_client_details_exitoso(toolkit):
    result = toolkit.get_client_details("C001")
    assert result["cliente_id"] == "C001"
    assert result["nombre_titular"] == "Maria Fernanda Torres Vega"
    assert result["tiene_deuda"] == False

def test_get_client_details_no_existe(toolkit):
    result = toolkit.get_client_details("C999")
    assert "error" in result


# ─── get_service_details ──────────────────────────────────────────────────────

def test_get_service_details_exitoso(toolkit):
    result = toolkit.get_service_details("C001")
    assert result["cliente_id"] == "C001"
    assert result["estado"] == "activo"
    assert "plan_nombre" in result

def test_get_service_details_no_existe(toolkit):
    result = toolkit.get_service_details("C999")
    assert "error" in result


# ─── list_available_plans ─────────────────────────────────────────────────────

def test_list_available_plans_sin_filtro(toolkit):
    result = toolkit.list_available_plans()
    assert "planes" in result
    assert len(result["planes"]) == 4

def test_list_available_plans_filtro_internet(toolkit):
    result = toolkit.list_available_plans(tipo="internet")
    assert "planes" in result
    assert all(p["tipo"] == "internet" for p in result["planes"])

def test_list_available_plans_filtro_invalido(toolkit):
    result = toolkit.list_available_plans(tipo="satelital")
    assert "error" in result


# ─── get_order_details ────────────────────────────────────────────────────────

def test_get_order_details_exitoso(toolkit):
    result = toolkit.get_order_details("O001")
    assert result["orden_id"] == "O001"
    assert result["estado"] == "confirmada"

def test_get_order_details_no_existe(toolkit):
    result = toolkit.get_order_details("O999")
    assert "error" in result


# ─── schedule_installation ───────────────────────────────────────────────────

def test_schedule_installation_exitoso(toolkit):
    result = toolkit.schedule_installation("C001", "mantenimiento", "2026-04-20", "10:00")
    assert "orden" in result
    assert result["orden"]["cliente_id"] == "C001"
    assert result["orden"]["estado"] == "pendiente"

def test_schedule_installation_cliente_con_deuda(toolkit):
    result = toolkit.schedule_installation("C002", "instalacion_nueva", "2026-04-20", "10:00")
    assert "error" in result
    assert "deuda" in result["error"].lower()

def test_schedule_installation_cliente_no_existe(toolkit):
    result = toolkit.schedule_installation("C999", "instalacion_nueva", "2026-04-20", "10:00")
    assert "error" in result


# ─── reschedule_installation ─────────────────────────────────────────────────

def test_reschedule_installation_exitoso(toolkit):
    result = toolkit.reschedule_installation("O002", "2026-04-10", "09:00")
    assert "orden" in result
    assert result["orden"]["fecha_programada"] == "2026-04-10"

def test_reschedule_installation_menos_48h(toolkit):
    # O003 está para 2026-03-31, menos de 48h desde 2026-03-30
    result = toolkit.reschedule_installation("O003", "2026-04-05", "10:00")
    assert "error" in result
    assert "48" in result["error"]

def test_reschedule_installation_no_existe(toolkit):
    result = toolkit.reschedule_installation("O999", "2026-04-10", "09:00")
    assert "error" in result


# ─── cancel_installation ─────────────────────────────────────────────────────

def test_cancel_installation_exitoso(toolkit):
    result = toolkit.cancel_installation("O002")
    assert "orden" in result
    assert result["orden"]["estado"] == "cancelada"

def test_cancel_installation_tecnico_menos_24h(toolkit):
    # O003 tiene técnico asignado y es para mañana 2026-03-31
    result = toolkit.cancel_installation("O003")
    assert "error" in result
    assert "técnico" in result["error"].lower() or "24" in result["error"]

def test_cancel_installation_no_existe(toolkit):
    result = toolkit.cancel_installation("O999")
    assert "error" in result


# ─── upgrade_plan ─────────────────────────────────────────────────────────────

def test_upgrade_plan_exitoso(toolkit):
    result = toolkit.upgrade_plan("C003", "P003")
    assert "plan_nuevo" in result
    assert result["plan_nuevo"] == "Internet Premium"

def test_upgrade_plan_downgrade_rechazado(toolkit):
    # C003 tiene P002 (nivel 2), intenta bajar a P001 (nivel 1)
    result = toolkit.upgrade_plan("C003", "P001")
    assert "error" in result
    assert "downgrade" in result["error"].lower()

def test_upgrade_plan_servicio_suspendido(toolkit):
    # C002 tiene servicio suspendido
    result = toolkit.upgrade_plan("C002", "P002")
    assert "error" in result

def test_upgrade_plan_cliente_no_existe(toolkit):
    result = toolkit.upgrade_plan("C999", "P002")
    assert "error" in result


# ─── create_complaint ─────────────────────────────────────────────────────────

def test_create_complaint_exitoso(toolkit):
    result = toolkit.create_complaint("C001", "facturacion", "Cobro incorrecto en abril")
    assert "reclamo" in result
    assert result["reclamo"]["tipo"] == "facturacion"
    assert result["reclamo"]["estado"] == "abierto"

def test_create_complaint_tipo_senal_mensaje_72h(toolkit):
    result = toolkit.create_complaint("C001", "señal", "Internet lento")
    assert "72" in result["mensaje"]

def test_create_complaint_tipo_invalido(toolkit):
    result = toolkit.create_complaint("C001", "queja_general", "No me gusta el servicio")
    assert "error" in result

def test_create_complaint_cliente_no_existe(toolkit):
    result = toolkit.create_complaint("C999", "señal", "Sin internet")
    assert "error" in result


# ─── get_complaint_status ─────────────────────────────────────────────────────

def test_get_complaint_status_exitoso(toolkit):
    result = toolkit.get_complaint_status("R001")
    assert result["reclamo_id"] == "R001"
    assert result["estado"] == "en_proceso"

def test_get_complaint_status_no_existe(toolkit):
    result = toolkit.get_complaint_status("R999")
    assert "error" in result