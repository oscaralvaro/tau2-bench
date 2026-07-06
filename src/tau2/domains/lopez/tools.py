from tau2.domains.lopez.data_model import (
    Cliente,
    EstadoPedido,
    EstadoTicket,
    GamerBitStoreDB,
    Garantia,
    Pedido,
    PedidoItem,
    Producto,
    RolCuenta,
    TicketSoporte,
    TipoGarantia,
    VerificacionSMS,
)
from tau2.environment.toolkit import ToolKitBase, ToolType, is_tool


class GamerBitStoreTools(ToolKitBase):
    """Tools for GamerBit Store sales, support, and warranty workflows."""

    db: GamerBitStoreDB

    def __init__(self, db: GamerBitStoreDB) -> None:
        super().__init__(db)

    def _get_cliente(self, cliente_id: str) -> Cliente:
        if cliente_id not in self.db.clientes:
            raise ValueError(f"Cliente '{cliente_id}' no existe")
        return self.db.clientes[cliente_id]

    def _get_producto(self, producto_id: str) -> Producto:
        if producto_id not in self.db.productos:
            raise ValueError(f"Producto '{producto_id}' no existe")
        return self.db.productos[producto_id]

    def _get_pedido(self, pedido_id: str) -> Pedido:
        if pedido_id not in self.db.pedidos:
            raise ValueError(f"Pedido '{pedido_id}' no existe")
        return self.db.pedidos[pedido_id]

    def _get_ticket(self, ticket_id: str) -> TicketSoporte:
        if ticket_id not in self.db.tickets_soporte:
            raise ValueError(f"Ticket '{ticket_id}' no existe")
        return self.db.tickets_soporte[ticket_id]

    def _get_garantia(self, cliente_id: str, producto_id: str) -> Garantia:
        for garantia in self.db.garantias.values():
            if garantia.cliente_id == cliente_id and garantia.producto_id == producto_id:
                return garantia
        raise ValueError(
            f"No existe garantia para cliente '{cliente_id}' y producto '{producto_id}'"
        )

    def _next_pedido_id(self) -> str:
        return f"ped{len(self.db.pedidos) + 1}"

    def _next_ticket_id(self) -> str:
        return f"t{len(self.db.tickets_soporte) + 1}"

    def _next_verificacion_sms_id(self) -> str:
        return f"sms{len(self.db.verificaciones_sms) + 1}"

    @is_tool(ToolType.READ)
    def buscar_productos(
        self, categoria: str | None = None, presupuesto_max: float | None = None
    ) -> list[Producto]:
        """
        Buscar productos activos por categoria y presupuesto.

        Args:
            categoria: Categoria opcional, por ejemplo 'laptop' o 'monitor'.
            presupuesto_max: Presupuesto maximo opcional.

        Returns:
            Lista de productos activos que cumplen los filtros.
        """
        productos = [producto for producto in self.db.productos.values() if producto.activo]
        if categoria is not None:
            productos = [
                producto
                for producto in productos
                if producto.categoria.value == categoria
            ]
        if presupuesto_max is not None:
            productos = [
                producto for producto in productos if producto.precio <= presupuesto_max
            ]
        return productos

    @is_tool(ToolType.READ)
    def consultar_producto(self, producto_id: str) -> Producto:
        """
        Consultar el detalle de un producto.

        Args:
            producto_id: Identificador del producto, como 'p1'.

        Returns:
            El producto solicitado.
        """
        return self._get_producto(producto_id)

    @is_tool(ToolType.READ)
    def consultar_stock(self, producto_id: str) -> int:
        """
        Consultar el stock disponible de un producto.

        Args:
            producto_id: Identificador del producto.

        Returns:
            Cantidad disponible en stock.
        """
        return self._get_producto(producto_id).stock

    @is_tool(ToolType.WRITE)
    def crear_pedido(self, cliente_id: str, items: list[dict]) -> Pedido:
        """
        Crear un pedido para un cliente si todos los productos existen, estan activos y tienen stock.

        Args:
            cliente_id: Identificador del cliente, como 'c1'.
            items: Lista de items con `producto_id` y `cantidad`.

        Returns:
            El pedido creado.

        Raises:
            ValueError: Si el cliente no existe, los items son invalidos, hay productos inactivos o stock insuficiente.
        """
        self._get_cliente(cliente_id)
        if len(items) == 0:
            raise ValueError("El pedido debe incluir al menos un item")

        pedido_items: list[PedidoItem] = []
        total = 0.0
        productos_actualizados: list[tuple[Producto, int]] = []
        for item in items:
            producto = self._get_producto(item["producto_id"])
            cantidad = int(item["cantidad"])
            if cantidad <= 0:
                raise ValueError("La cantidad debe ser mayor a cero")
            if not producto.activo:
                raise ValueError(f"El producto '{producto.id}' no esta activo")
            if producto.stock < cantidad:
                raise ValueError(f"Stock insuficiente para '{producto.id}'")
            productos_actualizados.append((producto, cantidad))
            pedido_items.append(
                PedidoItem(
                    producto_id=producto.id,
                    cantidad=cantidad,
                    precio_unitario=producto.precio,
                )
            )
            total += producto.precio * cantidad

        for producto, cantidad in productos_actualizados:
            producto.stock -= cantidad

        pedido = Pedido(
            id=self._next_pedido_id(),
            cliente_id=cliente_id,
            items=pedido_items,
            total=round(total, 2),
            estado=EstadoPedido.CONFIRMADO,
        )
        self.db.pedidos[pedido.id] = pedido
        return pedido

    @is_tool(ToolType.READ)
    def consultar_pedido(self, pedido_id: str) -> Pedido:
        """
        Consultar el estado y detalle de un pedido.

        Args:
            pedido_id: Identificador del pedido, como 'ped1'.

        Returns:
            El pedido solicitado.
        """
        return self._get_pedido(pedido_id)

    @is_tool(ToolType.WRITE)
    def cancelar_pedido(self, pedido_id: str) -> Pedido:
        """
        Cancelar un pedido que aun no fue entregado.

        Args:
            pedido_id: Identificador del pedido.

        Returns:
            El pedido actualizado.

        Raises:
            ValueError: Si el pedido ya fue entregado o ya estaba cancelado.
        """
        pedido = self._get_pedido(pedido_id)
        if pedido.estado == EstadoPedido.ENTREGADO:
            raise ValueError("No se puede cancelar un pedido entregado")
        if pedido.estado == EstadoPedido.CANCELADO:
            raise ValueError("El pedido ya fue cancelado")
        pedido.estado = EstadoPedido.CANCELADO
        return pedido

    @is_tool(ToolType.WRITE)
    def abrir_ticket_soporte(
        self, cliente_id: str, producto_id: str, motivo: str
    ) -> TicketSoporte:
        """
        Abrir un ticket de soporte tecnico.

        Args:
            cliente_id: Identificador del cliente.
            producto_id: Identificador del producto reportado.
            motivo: Descripcion breve de la falla.

        Returns:
            El ticket creado.

        Raises:
            ValueError: Si el cliente o el producto no existen, o el motivo esta vacio.
        """
        self._get_cliente(cliente_id)
        self._get_producto(producto_id)
        if not motivo.strip():
            raise ValueError("El motivo no debe estar vacio")

        ticket = TicketSoporte(
            id=self._next_ticket_id(),
            cliente_id=cliente_id,
            producto_id=producto_id,
            motivo=motivo,
            estado=EstadoTicket.ABIERTO,
            diagnostico=None,
            solucion=None,
            costo_estimado=None,
            requiere_aprobacion=False,
            aplica_garantia=None,
            listo_para_recojo=False,
        )
        self.db.tickets_soporte[ticket.id] = ticket
        return ticket

    @is_tool(ToolType.READ)
    def consultar_ticket(self, ticket_id: str) -> TicketSoporte:
        """
        Consultar el estado y detalle de un ticket de soporte.

        Args:
            ticket_id: Identificador del ticket, como 't1'.

        Returns:
            El ticket solicitado.
        """
        return self._get_ticket(ticket_id)

    @is_tool(ToolType.WRITE)
    def registrar_diagnostico(
        self,
        ticket_id: str,
        diagnostico: str,
        costo_estimado: float,
        aplica_garantia: bool,
    ) -> TicketSoporte:
        """
        Registrar el diagnostico tecnico de un ticket.

        Args:
            ticket_id: Identificador del ticket.
            diagnostico: Resultado del diagnostico.
            costo_estimado: Costo estimado si no aplica garantia.
            aplica_garantia: Indica si el caso califica para garantia.

        Returns:
            El ticket actualizado.
        """
        ticket = self._get_ticket(ticket_id)
        if ticket.estado in {EstadoTicket.CERRADO, EstadoTicket.RECHAZADO}:
            raise ValueError("No se puede diagnosticar un ticket cerrado o rechazado")
        ticket.diagnostico = diagnostico
        ticket.aplica_garantia = aplica_garantia
        ticket.costo_estimado = 0.0 if aplica_garantia else round(costo_estimado, 2)
        ticket.requiere_aprobacion = not aplica_garantia
        ticket.estado = (
            EstadoTicket.EN_REPARACION
            if aplica_garantia
            else EstadoTicket.ESPERANDO_APROBACION
        )
        return ticket

    @is_tool(ToolType.WRITE)
    def aprobar_reparacion(self, ticket_id: str) -> TicketSoporte:
        """
        Aprobar una reparacion pendiente de autorizacion del cliente.

        Args:
            ticket_id: Identificador del ticket.

        Returns:
            El ticket actualizado.
        """
        ticket = self._get_ticket(ticket_id)
        if ticket.diagnostico is None:
            raise ValueError("No se puede aprobar sin diagnostico previo")
        if ticket.estado != EstadoTicket.ESPERANDO_APROBACION:
            raise ValueError("El ticket no esta esperando aprobacion")
        ticket.estado = EstadoTicket.EN_REPARACION
        ticket.requiere_aprobacion = False
        return ticket

    @is_tool(ToolType.WRITE)
    def rechazar_reparacion(self, ticket_id: str) -> TicketSoporte:
        """
        Rechazar una reparacion luego del diagnostico.

        Args:
            ticket_id: Identificador del ticket.

        Returns:
            El ticket actualizado.
        """
        ticket = self._get_ticket(ticket_id)
        if ticket.diagnostico is None:
            raise ValueError("No se puede rechazar sin diagnostico previo")
        ticket.estado = EstadoTicket.RECHAZADO
        ticket.requiere_aprobacion = False
        return ticket

    @is_tool(ToolType.WRITE)
    def cerrar_ticket(self, ticket_id: str, solucion: str) -> TicketSoporte:
        """
        Cerrar un ticket con una solucion final.

        Args:
            ticket_id: Identificador del ticket.
            solucion: Solucion final aplicada.

        Returns:
            El ticket actualizado.
        """
        ticket = self._get_ticket(ticket_id)
        if not solucion.strip():
            raise ValueError("La solucion no debe estar vacia")
        ticket.solucion = solucion
        ticket.estado = EstadoTicket.CERRADO
        ticket.listo_para_recojo = False
        return ticket

    @is_tool(ToolType.READ)
    def verificar_garantia(self, cliente_id: str, producto_id: str) -> Garantia:
        """
        Consultar el estado de garantia de un producto para un cliente.

        Args:
            cliente_id: Identificador del cliente.
            producto_id: Identificador del producto.

        Returns:
            La garantia registrada para el cliente y el producto.
        """
        self._get_cliente(cliente_id)
        self._get_producto(producto_id)
        return self._get_garantia(cliente_id, producto_id)

    @is_tool(ToolType.WRITE)
    def enviar_codigo_verificacion_sms(
        self, cliente_id: str, rol_requerido: str
    ) -> VerificacionSMS:
        """
        Enviar un codigo SMS de verificacion al telefono del cliente.

        Args:
            cliente_id: Identificador del cliente.
            rol_requerido: Rol que se desea validar, por ejemplo 'cliente' o 'empleado'.

        Returns:
            Desafio de verificacion creado.
        """
        cliente = self._get_cliente(cliente_id)
        rol = RolCuenta(rol_requerido)
        codigo = f"{len(self.db.verificaciones_sms) + 1:06d}"
        verificacion = VerificacionSMS(
            id=self._next_verificacion_sms_id(),
            cliente_id=cliente_id,
            rol_requerido=rol,
            codigo=codigo,
            enviada_a=cliente.telefono,
            activa=True,
            verificada=False,
            intentos=0,
        )
        self.db.verificaciones_sms[verificacion.id] = verificacion
        return verificacion

    @is_tool(ToolType.WRITE)
    def validar_codigo_verificacion_sms(
        self, cliente_id: str, rol_requerido: str, codigo: str
    ) -> bool:
        """
        Validar un codigo SMS previamente enviado al cliente.

        Args:
            cliente_id: Identificador del cliente.
            rol_requerido: Rol que se desea validar.
            codigo: Codigo numerico recibido por el cliente.

        Returns:
            True si el codigo es valido para el cliente y el rol.
        """
        cliente = self._get_cliente(cliente_id)
        rol = RolCuenta(rol_requerido)
        if cliente.rol != rol:
            raise ValueError(
                f"El cliente '{cliente_id}' no tiene el rol requerido '{rol.value}'"
            )
        verificaciones = [
            sms
            for sms in self.db.verificaciones_sms.values()
            if sms.cliente_id == cliente_id and sms.activa
        ]
        if not verificaciones:
            raise ValueError("No existe un codigo SMS activo para este cliente")
        verificacion = verificaciones[-1]
        verificacion.intentos += 1
        if verificacion.rol_requerido != rol:
            raise ValueError("El rol solicitado no coincide con el desafio enviado")
        if verificacion.codigo != codigo:
            raise ValueError("Codigo SMS incorrecto")
        verificacion.verificada = True
        verificacion.activa = False
        return True

    def assert_pedido_estado(self, pedido_id: str, expected_estado: str) -> bool:
        pedido = self.db.pedidos.get(pedido_id)
        if pedido is None:
            return False
        return pedido.estado.value == expected_estado

    def assert_pedido_cliente_y_total(
        self, pedido_id: str, cliente_id: str, total: float
    ) -> bool:
        pedido = self.db.pedidos.get(pedido_id)
        if pedido is None:
            return False
        return pedido.cliente_id == cliente_id and abs(pedido.total - total) < 1e-6

    def assert_ticket_estado(self, ticket_id: str, expected_estado: str) -> bool:
        ticket = self.db.tickets_soporte.get(ticket_id)
        if ticket is None:
            return False
        return ticket.estado.value == expected_estado

    def assert_ticket_motivo(self, ticket_id: str, expected_motivo: str) -> bool:
        ticket = self.db.tickets_soporte.get(ticket_id)
        if ticket is None:
            return False
        return ticket.motivo == expected_motivo

    def assert_no_pedido_for_cliente_producto(
        self, cliente_id: str, producto_id: str
    ) -> bool:
        for pedido in self.db.pedidos.values():
            if pedido.cliente_id != cliente_id:
                continue
            for item in pedido.items:
                if item.producto_id == producto_id:
                    return False
        return True

    def assert_garantia_no_aplica(self, cliente_id: str, producto_id: str) -> bool:
        garantia = self._get_garantia(cliente_id, producto_id)
        return (not garantia.vigente) or garantia.tipo_garantia == TipoGarantia.NO_APLICA

    def assert_sms_verificado(self, cliente_id: str, rol_requerido: str) -> bool:
        rol = RolCuenta(rol_requerido)
        return any(
            sms.cliente_id == cliente_id
            and sms.rol_requerido == rol
            and sms.verificada
            for sms in self.db.verificaciones_sms.values()
        )

    def assert_sms_no_verificado(self, cliente_id: str, rol_requerido: str) -> bool:
        rol = RolCuenta(rol_requerido)
        return not any(
            sms.cliente_id == cliente_id
            and sms.rol_requerido == rol
            and sms.verificada
            for sms in self.db.verificaciones_sms.values()
        )
