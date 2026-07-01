"""Generate consistent seed data for the GamerBit Store domain."""

from tau2.domains.lopez.data_model import (
    CategoriaProducto,
    Cliente,
    EspecialidadTecnico,
    EstadoPedido,
    EstadoTicket,
    GamerBitStoreDB,
    Garantia,
    Pedido,
    PedidoItem,
    Producto,
    Tecnico,
    TicketSoporte,
    TipoGarantia,
)
from tau2.domains.lopez.utils import GAMERBIT_STORE_DB_PATH


def build_seed_db() -> GamerBitStoreDB:
    clientes = {
        "c1": Cliente(
            id="c1",
            nombre="Juan Perez",
            correo="juan.perez@gamerbit.pe",
            telefono="999111222",
        ),
        "c2": Cliente(
            id="c2",
            nombre="Maria Lopez",
            correo="maria.lopez@gamerbit.pe",
            telefono="999333444",
        ),
        "c3": Cliente(
            id="c3",
            nombre="Luis Ramos",
            correo="luis.ramos@gamerbit.pe",
            telefono="999555666",
        ),
        "c4": Cliente(
            id="c4",
            nombre="Andrea Castillo",
            correo="andrea.castillo@gamerbit.pe",
            telefono="999777888",
        ),
        "c5": Cliente(
            id="c5",
            nombre="Diego Huaman",
            correo="diego.huaman@gamerbit.pe",
            telefono="999000123",
        ),
    }

    productos = {
        "p1": Producto(
            id="p1",
            nombre="Laptop GamerBit G15",
            categoria=CategoriaProducto.LAPTOP,
            precio=3500.0,
            stock=5,
            garantia_meses=12,
            activo=True,
        ),
        "p2": Producto(
            id="p2",
            nombre="PC Armada Ryzen 7",
            categoria=CategoriaProducto.PC,
            precio=4200.0,
            stock=2,
            garantia_meses=12,
            activo=True,
        ),
        "p3": Producto(
            id="p3",
            nombre='Monitor 24" 144Hz',
            categoria=CategoriaProducto.MONITOR,
            precio=900.0,
            stock=8,
            garantia_meses=6,
            activo=True,
        ),
        "p4": Producto(
            id="p4",
            nombre="Teclado Mecanico RGB",
            categoria=CategoriaProducto.PERIFERICO,
            precio=250.0,
            stock=10,
            garantia_meses=3,
            activo=True,
        ),
        "p5": Producto(
            id="p5",
            nombre="SSD 1TB NVMe",
            categoria=CategoriaProducto.COMPONENTE,
            precio=380.0,
            stock=6,
            garantia_meses=12,
            activo=True,
        ),
        "p6": Producto(
            id="p6",
            nombre="Fuente 750W Gold",
            categoria=CategoriaProducto.COMPONENTE,
            precio=520.0,
            stock=0,
            garantia_meses=12,
            activo=True,
        ),
        "p7": Producto(
            id="p7",
            nombre="Mouse Gamer Pro",
            categoria=CategoriaProducto.PERIFERICO,
            precio=180.0,
            stock=15,
            garantia_meses=3,
            activo=True,
        ),
        "p8": Producto(
            id="p8",
            nombre="Laptop Office 14",
            categoria=CategoriaProducto.LAPTOP,
            precio=2600.0,
            stock=1,
            garantia_meses=12,
            activo=True,
        ),
        "p9": Producto(
            id="p9",
            nombre='Monitor 27" 4K',
            categoria=CategoriaProducto.MONITOR,
            precio=1500.0,
            stock=0,
            garantia_meses=6,
            activo=True,
        ),
        "p10": Producto(
            id="p10",
            nombre="Webcam HD Basic",
            categoria=CategoriaProducto.PERIFERICO,
            precio=120.0,
            stock=4,
            garantia_meses=1,
            activo=False,
        ),
    }

    pedidos = {
        "ped1": Pedido(
            id="ped1",
            cliente_id="c2",
            items=[
                PedidoItem(producto_id="p3", cantidad=1, precio_unitario=900.0),
                PedidoItem(producto_id="p4", cantidad=1, precio_unitario=250.0),
            ],
            total=1150.0,
            estado=EstadoPedido.PENDIENTE,
        ),
        "ped2": Pedido(
            id="ped2",
            cliente_id="c1",
            items=[PedidoItem(producto_id="p1", cantidad=1, precio_unitario=3500.0)],
            total=3500.0,
            estado=EstadoPedido.ENTREGADO,
        ),
        "ped3": Pedido(
            id="ped3",
            cliente_id="c3",
            items=[PedidoItem(producto_id="p5", cantidad=1, precio_unitario=380.0)],
            total=380.0,
            estado=EstadoPedido.CANCELADO,
        ),
        "ped4": Pedido(
            id="ped4",
            cliente_id="c4",
            items=[
                PedidoItem(producto_id="p2", cantidad=1, precio_unitario=4200.0),
                PedidoItem(producto_id="p7", cantidad=1, precio_unitario=180.0),
            ],
            total=4380.0,
            estado=EstadoPedido.CONFIRMADO,
        ),
    }

    tickets = {
        "t1": TicketSoporte(
            id="t1",
            cliente_id="c4",
            producto_id="p2",
            motivo="La PC no enciende",
            estado=EstadoTicket.ABIERTO,
            diagnostico=None,
            solucion=None,
            costo_estimado=None,
            requiere_aprobacion=False,
            aplica_garantia=None,
            listo_para_recojo=False,
        ),
        "t2": TicketSoporte(
            id="t2",
            cliente_id="c1",
            producto_id="p1",
            motivo="La pantalla parpadea de forma intermitente",
            estado=EstadoTicket.EN_DIAGNOSTICO,
            diagnostico="Pendiente de revision tecnica",
            solucion=None,
            costo_estimado=None,
            requiere_aprobacion=False,
            aplica_garantia=None,
            listo_para_recojo=False,
        ),
        "t3": TicketSoporte(
            id="t3",
            cliente_id="c3",
            producto_id="p5",
            motivo="El SSD no es detectado por la BIOS",
            estado=EstadoTicket.ESPERANDO_APROBACION,
            diagnostico="Se requiere reemplazo de la unidad",
            solucion=None,
            costo_estimado=250.0,
            requiere_aprobacion=True,
            aplica_garantia=False,
            listo_para_recojo=False,
        ),
        "t4": TicketSoporte(
            id="t4",
            cliente_id="c2",
            producto_id="p3",
            motivo="Aparecen lineas verticales en la pantalla",
            estado=EstadoTicket.LISTO,
            diagnostico="Falla de panel confirmada",
            solucion="Reemplazo de panel completado",
            costo_estimado=0.0,
            requiere_aprobacion=False,
            aplica_garantia=True,
            listo_para_recojo=True,
        ),
        "t5": TicketSoporte(
            id="t5",
            cliente_id="c1",
            producto_id="p4",
            motivo="Algunas teclas dejaron de responder",
            estado=EstadoTicket.CERRADO,
            diagnostico="Switches desgastados por uso",
            solucion="Se realizo limpieza interna y cambio de switches",
            costo_estimado=80.0,
            requiere_aprobacion=False,
            aplica_garantia=False,
            listo_para_recojo=False,
        ),
    }

    garantias = {
        "g1": Garantia(
            id="g1",
            cliente_id="c1",
            producto_id="p1",
            fecha_compra="2026-01-10",
            vigente=True,
            tipo_garantia=TipoGarantia.TIENDA,
            cobertura="falla_fabrica",
            observaciones="No cubre software, dano fisico ni perdida de datos.",
        ),
        "g2": Garantia(
            id="g2",
            cliente_id="c3",
            producto_id="p5",
            fecha_compra="2024-01-10",
            vigente=False,
            tipo_garantia=TipoGarantia.TIENDA,
            cobertura="falla_fabrica",
            observaciones="Garantia vencida por tiempo de uso.",
        ),
        "g3": Garantia(
            id="g3",
            cliente_id="c4",
            producto_id="p2",
            fecha_compra="2026-02-05",
            vigente=True,
            tipo_garantia=TipoGarantia.FABRICANTE,
            cobertura="solo_hardware",
            observaciones="La validacion final depende del diagnostico tecnico.",
        ),
        "g4": Garantia(
            id="g4",
            cliente_id="c2",
            producto_id="p3",
            fecha_compra="2026-03-01",
            vigente=True,
            tipo_garantia=TipoGarantia.CONSULTAR,
            cobertura="revision_tecnica",
            observaciones="Sujeto a revision tecnica y disponibilidad de reposicion.",
        ),
        "g5": Garantia(
            id="g5",
            cliente_id="c5",
            producto_id="p10",
            fecha_compra="2025-02-15",
            vigente=False,
            tipo_garantia=TipoGarantia.NO_APLICA,
            cobertura="ninguna",
            observaciones="No aplica por dano fisico y producto descontinuado.",
        ),
    }

    tecnicos = {
        "tec1": Tecnico(
            id="tec1",
            nombre="Carlos Medina",
            especialidad=EspecialidadTecnico.HARDWARE,
            disponible=True,
        ),
        "tec2": Tecnico(
            id="tec2",
            nombre="Sofia Vargas",
            especialidad=EspecialidadTecnico.LAPTOPS,
            disponible=True,
        ),
        "tec3": Tecnico(
            id="tec3",
            nombre="Renzo Salazar",
            especialidad=EspecialidadTecnico.PERIFERICOS,
            disponible=False,
        ),
    }

    return GamerBitStoreDB(
        clientes=clientes,
        productos=productos,
        pedidos=pedidos,
        tickets_soporte=tickets,
        garantias=garantias,
        tecnicos=tecnicos,
    )


def main() -> None:
    db = build_seed_db()
    GAMERBIT_STORE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db.dump(GAMERBIT_STORE_DB_PATH, indent=2)


if __name__ == "__main__":
    main()
