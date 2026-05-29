from tau2.data_model.message import ToolCall
from tau2.domains.lopez.environment import get_environment


def test_buscar_productos_por_categoria_y_presupuesto():
    env = get_environment()
    productos = env.use_tool(
        "buscar_productos", categoria="laptop", presupuesto_max=3000.0
    )
    assert len(productos) == 1
    assert productos[0].id == "p8"
    assert productos[0].activo


def test_consultar_stock_producto_existente():
    env = get_environment()
    stock = env.use_tool("consultar_stock", producto_id="p6")
    assert stock == 0


def test_consultar_producto_existente():
    env = get_environment()
    producto = env.use_tool("consultar_producto", producto_id="p1")
    assert producto.nombre == "Laptop GamerBit G15"
    assert producto.categoria.value == "laptop"


def test_consultar_stock_producto_inexistente():
    env = get_environment()
    response = env.get_response(
        ToolCall(id="1", name="consultar_stock", arguments={"producto_id": "p999"})
    )
    assert response.error


def test_crear_pedido_valido():
    env = get_environment()
    pedido = env.use_tool(
        "crear_pedido",
        cliente_id="c5",
        items=[{"producto_id": "p8", "cantidad": 1}],
    )
    assert pedido.id == "ped5"
    assert pedido.estado.value == "confirmado"
    assert pedido.total == 2600.0
    assert env.tools.db.productos["p8"].stock == 0


def test_crear_pedido_sin_stock_falla():
    env = get_environment()
    response = env.get_response(
        ToolCall(
            id="2",
            name="crear_pedido",
            arguments={
                "cliente_id": "c5",
                "items": [{"producto_id": "p6", "cantidad": 1}],
            },
        )
    )
    assert response.error


def test_crear_pedido_con_producto_inactivo_falla():
    env = get_environment()
    response = env.get_response(
        ToolCall(
            id="3",
            name="crear_pedido",
            arguments={
                "cliente_id": "c5",
                "items": [{"producto_id": "p10", "cantidad": 1}],
            },
        )
    )
    assert response.error


def test_cancelar_pedido_pendiente():
    env = get_environment()
    pedido = env.use_tool("cancelar_pedido", pedido_id="ped1")
    assert pedido.estado.value == "cancelado"


def test_consultar_pedido_existente():
    env = get_environment()
    pedido = env.use_tool("consultar_pedido", pedido_id="ped4")
    assert pedido.cliente_id == "c4"
    assert pedido.estado.value == "confirmado"


def test_cancelar_pedido_entregado_falla():
    env = get_environment()
    response = env.get_response(
        ToolCall(id="4", name="cancelar_pedido", arguments={"pedido_id": "ped2"})
    )
    assert response.error


def test_abrir_ticket_soporte_valido():
    env = get_environment()
    ticket = env.use_tool(
        "abrir_ticket_soporte",
        cliente_id="c5",
        producto_id="p8",
        motivo="Mi laptop no enciende",
    )
    assert ticket.id == "t6"
    assert ticket.estado.value == "abierto"
    assert ticket.motivo == "Mi laptop no enciende"


def test_consultar_ticket_existente():
    env = get_environment()
    ticket = env.use_tool("consultar_ticket", ticket_id="t4")
    assert ticket.estado.value == "listo"
    assert ticket.listo_para_recojo is True


def test_registrar_diagnostico_actualiza_ticket():
    env = get_environment()
    ticket = env.use_tool(
        "registrar_diagnostico",
        ticket_id="t1",
        diagnostico="Falla en la fuente de poder",
        costo_estimado=180.0,
        aplica_garantia=False,
    )
    assert ticket.diagnostico == "Falla en la fuente de poder"
    assert ticket.estado.value == "esperando_aprobacion"
    assert ticket.requiere_aprobacion is True


def test_aprobar_reparacion_requiere_diagnostico():
    env = get_environment()
    response = env.get_response(
        ToolCall(id="5", name="aprobar_reparacion", arguments={"ticket_id": "t1"})
    )
    assert response.error


def test_aprobar_reparacion_valida():
    env = get_environment()
    ticket = env.use_tool("aprobar_reparacion", ticket_id="t3")
    assert ticket.estado.value == "en_reparacion"
    assert ticket.requiere_aprobacion is False


def test_rechazar_reparacion_valida():
    env = get_environment()
    ticket = env.use_tool("rechazar_reparacion", ticket_id="t3")
    assert ticket.estado.value == "rechazado"
    assert ticket.requiere_aprobacion is False


def test_cerrar_ticket_valido():
    env = get_environment()
    ticket = env.use_tool(
        "cerrar_ticket",
        ticket_id="t1",
        solucion="Se reemplazo la fuente de poder y el equipo vuelve a encender",
    )
    assert ticket.estado.value == "cerrado"
    assert ticket.solucion.startswith("Se reemplazo")


def test_verificar_garantia_vigente():
    env = get_environment()
    garantia = env.use_tool("verificar_garantia", cliente_id="c1", producto_id="p1")
    assert garantia.vigente is True
    assert garantia.tipo_garantia.value == "tienda"


def test_verificar_garantia_no_vigente_o_no_aplica():
    env = get_environment()
    garantia = env.use_tool("verificar_garantia", cliente_id="c5", producto_id="p10")
    assert garantia.vigente is False
    assert garantia.tipo_garantia.value == "no_aplica"


def test_enviar_codigo_verificacion_sms():
    env = get_environment()
    verificacion = env.use_tool(
        "enviar_codigo_verificacion_sms", cliente_id="c2", rol_requerido="cliente"
    )
    assert verificacion.id == "sms1"
    assert verificacion.cliente_id == "c2"
    assert verificacion.rol_requerido.value == "cliente"
    assert verificacion.codigo == "000001"
    assert env.user_tools.assert_sms_recibido("c2", "cliente")


def test_validar_codigo_verificacion_sms_valido():
    env = get_environment()
    env.use_tool("enviar_codigo_verificacion_sms", cliente_id="c2", rol_requerido="cliente")
    ok = env.use_tool(
        "validar_codigo_verificacion_sms",
        cliente_id="c2",
        rol_requerido="cliente",
        codigo="000001",
    )
    assert ok is True
    assert env.tools.assert_sms_verificado("c2", "cliente")


def test_validar_codigo_verificacion_sms_incorrecto_falla():
    env = get_environment()
    env.use_tool("enviar_codigo_verificacion_sms", cliente_id="c2", rol_requerido="cliente")
    response = env.get_response(
        ToolCall(
            id="6",
            name="validar_codigo_verificacion_sms",
            arguments={
                "cliente_id": "c2",
                "rol_requerido": "cliente",
                "codigo": "999999",
            },
        )
    )
    assert response.error


def test_validar_codigo_verificacion_sms_rol_incorrecto_falla():
    env = get_environment()
    env.use_tool("enviar_codigo_verificacion_sms", cliente_id="c2", rol_requerido="cliente")
    response = env.get_response(
        ToolCall(
            id="7",
            name="validar_codigo_verificacion_sms",
            arguments={
                "cliente_id": "c2",
                "rol_requerido": "empleado",
                "codigo": "000001",
            },
        )
    )
    assert response.error
