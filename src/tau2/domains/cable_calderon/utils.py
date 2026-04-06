from pathlib import Path
import os

# Detecta la ruta correcta usando TAU2_DATA_DIR o la ruta relativa al repo
_THIS_FILE = Path(__file__).resolve()
_REPO_ROOT = _THIS_FILE.parents[4]  # src/tau2/domains/cable_calderon -> repo root

if "TAU2_DATA_DIR" in os.environ:
    CABLE_CALDERON_DATA_DIR = Path(os.environ["TAU2_DATA_DIR"]) / "domains" / "cable_calderon"
else:
    CABLE_CALDERON_DATA_DIR = _REPO_ROOT / "data" / "tau2" / "domains" / "cable_calderon"

CABLE_CALDERON_DB_PATH = CABLE_CALDERON_DATA_DIR / "db.json"
CABLE_CALDERON_TASKS_PATH = CABLE_CALDERON_DATA_DIR / "tasks.json"
CABLE_CALDERON_SPLIT_TASKS_PATH = CABLE_CALDERON_DATA_DIR / "split_tasks.json"
CABLE_CALDERON_POLICY_PATH = _THIS_FILE.parent / "policy.md"

if __name__ == "__main__":
    """
    Ejecuta este script para generar db.json automáticamente:
    python src/tau2/domains/cable_calderon/utils.py
    """
    from tau2.domains.cable_calderon.data_model import (
        CableCalderonDB, Cliente, ContactoAutorizado,
        Plan, Servicio, OrdenInstalacion, Reclamo
    )

    db = CableCalderonDB(
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
                contactos_autorizados=[
                    ContactoAutorizado(nombre="Pedro Ramirez", telefono="923456789")
                ]
            ),
            "C004": Cliente(
                cliente_id="C004",
                nombre_titular="Luis Alberto Mendoza Cruz",
                telefono="954321098",
                email="lmendoza@gmail.com",
                direccion="Av. Grau 321, Piura",
                tiene_deuda=False,
                monto_deuda=0.0,
                contactos_autorizados=[]
            ),
            "C005": Cliente(
                cliente_id="C005",
                nombre_titular="Carmen Rosa Huanca Flores",
                telefono="943210987",
                email="chuanca@yahoo.com",
                direccion="Av. Sanchez Cerro 654, Piura",
                tiene_deuda=True,
                monto_deuda=120.00,
                contactos_autorizados=[
                    ContactoAutorizado(nombre="Jose Huanca", telefono="934567890")
                ]
            ),
        },
        users={
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
                contactos_autorizados=[
                    ContactoAutorizado(nombre="Pedro Ramirez", telefono="923456789")
                ]
            ),
            "C004": Cliente(
                cliente_id="C004",
                nombre_titular="Luis Alberto Mendoza Cruz",
                telefono="954321098",
                email="lmendoza@gmail.com",
                direccion="Av. Grau 321, Piura",
                tiene_deuda=False,
                monto_deuda=0.0,
                contactos_autorizados=[]
            ),
            "C005": Cliente(
                cliente_id="C005",
                nombre_titular="Carmen Rosa Huanca Flores",
                telefono="943210987",
                email="chuanca@yahoo.com",
                direccion="Av. Sanchez Cerro 654, Piura",
                tiene_deuda=True,
                monto_deuda=120.00,
                contactos_autorizados=[
                    ContactoAutorizado(nombre="Jose Huanca", telefono="934567890")
                ]
            ),
        },
        planes={
            "P001": Plan(
                plan_id="P001",
                nombre="Internet Básico",
                tipo="internet",
                velocidad_mbps=50,
                canales=None,
                precio_mensual=59.90,
                nivel=1
            ),
            "P002": Plan(
                plan_id="P002",
                nombre="Internet Pro",
                tipo="internet",
                velocidad_mbps=100,
                canales=None,
                precio_mensual=89.90,
                nivel=2
            ),
            "P003": Plan(
                plan_id="P003",
                nombre="Internet Premium",
                tipo="internet",
                velocidad_mbps=200,
                canales=None,
                precio_mensual=129.90,
                nivel=3
            ),
            "P004": Plan(
                plan_id="P004",
                nombre="Cable Básico",
                tipo="cable",
                velocidad_mbps=None,
                canales=60,
                precio_mensual=49.90,
                nivel=1
            ),
            "P005": Plan(
                plan_id="P005",
                nombre="Cable Plus",
                tipo="cable",
                velocidad_mbps=None,
                canales=120,
                precio_mensual=79.90,
                nivel=2
            ),
            "P006": Plan(
                plan_id="P006",
                nombre="Combo Básico",
                tipo="combo",
                velocidad_mbps=50,
                canales=60,
                precio_mensual=99.90,
                nivel=1
            ),
            "P007": Plan(
                plan_id="P007",
                nombre="Combo Premium",
                tipo="combo",
                velocidad_mbps=100,
                canales=120,
                precio_mensual=149.90,
                nivel=2
            ),
        },
        servicios={
            "S001": Servicio(
                servicio_id="S001",
                cliente_id="C001",
                plan_id="P006",
                estado="activo",
                fecha_inicio="2025-01-15",
                fecha_vencimiento="2026-04-15"
            ),
            "S002": Servicio(
                servicio_id="S002",
                cliente_id="C002",
                plan_id="P001",
                estado="suspendido",
                fecha_inicio="2024-08-01",
                fecha_vencimiento="2026-03-01"
            ),
            "S003": Servicio(
                servicio_id="S003",
                cliente_id="C003",
                plan_id="P002",
                estado="activo",
                fecha_inicio="2025-03-10",
                fecha_vencimiento="2026-04-10"
            ),
            "S004": Servicio(
                servicio_id="S004",
                cliente_id="C004",
                plan_id="P004",
                estado="activo",
                fecha_inicio="2025-06-20",
                fecha_vencimiento="2026-04-20"
            ),
            "S005": Servicio(
                servicio_id="S005",
                cliente_id="C005",
                plan_id="P007",
                estado="suspendido",
                fecha_inicio="2024-11-05",
                fecha_vencimiento="2026-02-05"
            ),
        },
        ordenes={
            "O001": OrdenInstalacion(
                orden_id="O001",
                cliente_id="C001",
                tipo="mantenimiento",
                fecha_programada="2026-04-05",
                hora_programada="10:00",
                tecnico_asignado="Juan Perez",
                estado="confirmada"
            ),
            "O002": OrdenInstalacion(
                orden_id="O002",
                cliente_id="C003",
                tipo="instalacion_nueva",
                fecha_programada="2026-04-02",
                hora_programada="14:00",
                tecnico_asignado=None,
                estado="pendiente"
            ),
            "O003": OrdenInstalacion(
                orden_id="O003",
                cliente_id="C004",
                tipo="instalacion_nueva",
                fecha_programada="2026-03-31",
                hora_programada="09:00",
                tecnico_asignado="Mario Rios",
                estado="confirmada"
            ),
            "O004": OrdenInstalacion(
                orden_id="O004",
                cliente_id="C002",
                tipo="retiro",
                fecha_programada="2026-04-10",
                hora_programada="11:00",
                tecnico_asignado=None,
                estado="pendiente"
            ),
            "O005": OrdenInstalacion(
                orden_id="O005",
                cliente_id="C005",
                tipo="instalacion_nueva",
                fecha_programada="2026-04-15",
                hora_programada="15:00",
                tecnico_asignado=None,
                estado="pendiente"
            ),
            "O006": OrdenInstalacion(
                orden_id="O006",
                cliente_id="C001",
                tipo="instalacion_nueva",
                fecha_programada="2026-03-31",
                hora_programada="08:00",
                tecnico_asignado="Luis Campos",
                estado="en_curso"
            ),
            "O007": OrdenInstalacion(
                orden_id="O007",
                cliente_id="C003",
                tipo="mantenimiento",
                fecha_programada="2026-04-20",
                hora_programada="10:00",
                tecnico_asignado=None,
                estado="pendiente"
            ),
            "O008": OrdenInstalacion(
                orden_id="O008",
                cliente_id="C004",
                tipo="mantenimiento",
                fecha_programada="2026-04-08",
                hora_programada="16:00",
                tecnico_asignado=None,
                estado="pendiente"
            ),
            "O009": OrdenInstalacion(
                orden_id="O009",
                cliente_id="C002",
                tipo="instalacion_nueva",
                fecha_programada="2026-04-01",
                hora_programada="09:00",
                tecnico_asignado="Carlos Vega",
                estado="confirmada"
            ),
            "O010": OrdenInstalacion(
                orden_id="O010",
                cliente_id="C005",
                tipo="mantenimiento",
                fecha_programada="2026-03-20",
                hora_programada="11:00",
                tecnico_asignado="Mario Rios",
                estado="completada"
            ),
        },
        reclamos={
            "R001": Reclamo(
                reclamo_id="R001",
                cliente_id="C001",
                tipo="señal",
                descripcion="Intermitencia en la señal de internet",
                estado="en_proceso",
                fecha_creacion="2026-03-25",
                fecha_resolucion=None
            ),
            "R002": Reclamo(
                reclamo_id="R002",
                cliente_id="C003",
                tipo="facturacion",
                descripcion="Cobro duplicado en el mes de marzo",
                estado="abierto",
                fecha_creacion="2026-03-28",
                fecha_resolucion=None
            ),
            "R003": Reclamo(
                reclamo_id="R003",
                cliente_id="C004",
                tipo="instalacion",
                descripcion="Técnico no se presentó en la fecha acordada",
                estado="resuelto",
                fecha_creacion="2026-03-15",
                fecha_resolucion="2026-03-20"
            ),
            "R004": Reclamo(
                reclamo_id="R004",
                cliente_id="C002",
                tipo="señal",
                descripcion="Sin señal de cable desde hace 3 días",
                estado="abierto",
                fecha_creacion="2026-03-29",
                fecha_resolucion=None
            ),
            "R005": Reclamo(
                reclamo_id="R005",
                cliente_id="C004",
                tipo="otro",
                descripcion="Solicitud de información sobre planes disponibles",
                estado="cerrado",
                fecha_creacion="2026-03-10",
                fecha_resolucion="2026-03-11"
            ),
            "R006": Reclamo(
                reclamo_id="R006",
                cliente_id="C005",
                tipo="facturacion",
                descripcion="Cobro de servicio suspendido",
                estado="en_proceso",
                fecha_creacion="2026-03-27",
                fecha_resolucion=None
            ),
            "R007": Reclamo(
                reclamo_id="R007",
                cliente_id="C001",
                tipo="instalacion",
                descripcion="Cable mal instalado, genera interferencia",
                estado="resuelto",
                fecha_creacion="2026-03-01",
                fecha_resolucion="2026-03-05"
            ),
            "R008": Reclamo(
                reclamo_id="R008",
                cliente_id="C003",
                tipo="señal",
                descripcion="Velocidad de internet muy lenta en horas pico",
                estado="en_proceso",
                fecha_creacion="2026-03-26",
                fecha_resolucion=None
            ),
            "R009": Reclamo(
                reclamo_id="R009",
                cliente_id="C004",
                tipo="facturacion",
                descripcion="No reconoce el cobro de instalación",
                estado="abierto",
                fecha_creacion="2026-03-30",
                fecha_resolucion=None
            ),
            "R010": Reclamo(
                reclamo_id="R010",
                cliente_id="C002",
                tipo="otro",
                descripcion="Solicitud de reconexión del servicio",
                estado="cerrado",
                fecha_creacion="2026-03-20",
                fecha_resolucion="2026-03-22"
            ),
        }
    )

    CABLE_CALDERON_DATA_DIR.mkdir(parents=True, exist_ok=True)
    db.dump(CABLE_CALDERON_DB_PATH)
    print(f"db.json generado en: {CABLE_CALDERON_DB_PATH}")