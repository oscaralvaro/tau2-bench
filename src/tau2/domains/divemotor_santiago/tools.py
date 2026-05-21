from tau2.environment.toolkit import ToolKitBase, is_tool, ToolType
from .data_model import CodigoSMS, Cotizacion, Pedido


class DivemotorTools(ToolKitBase):
    def _codigo_para_cliente(self, cliente_id: str) -> str:
        return f"{sum(ord(c) for c in cliente_id) + 482000}"

    def _identidad_verificada(self, cliente_id: str, rol_requerido: str = "user") -> bool:
        codigo = self.db.codigos_sms.get(cliente_id)
        return (
            codigo is not None
            and codigo.verificado
            and codigo.rol_requerido == rol_requerido
        )

    @is_tool(ToolType.READ)
    def get_cliente(self, cliente_id: str):
        return self.db.users.get(cliente_id)

    @is_tool(ToolType.READ)
    def buscar_vehiculos(self, tipo: str):
        return [v for v in self.db.vehiculos.values() if tipo.lower() in v.tipo.lower()]

    @is_tool(ToolType.WRITE)
    def enviar_codigo_sms(self, cliente_id: str, rol_requerido: str = "user"):
        cliente = self.db.users.get(cliente_id)

        if not cliente:
            return "Error: cliente no existe"

        if cliente.rol != rol_requerido:
            return "Error: rol no autorizado"

        codigo = self._codigo_para_cliente(cliente_id)
        self.db.codigos_sms[cliente_id] = CodigoSMS(
            cliente_id=cliente_id,
            codigo=codigo,
            rol_requerido=rol_requerido,
            verificado=False,
        )
        return {
            "cliente_id": cliente_id,
            "rol_requerido": rol_requerido,
            "estado": "codigo_enviado",
        }

    @is_tool(ToolType.WRITE)
    def verificar_codigo_sms(
        self, cliente_id: str, codigo: str, rol_requerido: str = "user"
    ):
        registro = self.db.codigos_sms.get(cliente_id)

        if not registro:
            return "Error: codigo no enviado"

        if registro.rol_requerido != rol_requerido:
            return "Error: rol no coincide"

        if registro.codigo != codigo:
            registro.verificado = False
            return "Error: codigo incorrecto"

        registro.verificado = True
        return {
            "cliente_id": cliente_id,
            "rol_requerido": rol_requerido,
            "estado": "verificado",
        }

    def identidad_verificada(self, cliente_id: str, rol_requerido: str = "user") -> bool:
        return self._identidad_verificada(cliente_id, rol_requerido)

    @is_tool(ToolType.WRITE)
    def crear_cotizacion(self, cliente_id: str, vehiculo_id: str):
        cliente = self.db.users.get(cliente_id)
        vehiculo = self.db.vehiculos.get(vehiculo_id)

        if not cliente or not vehiculo:
            return "Error: cliente o vehiculo no existe"

        if cliente.presupuesto < vehiculo.precio:
            return "Error: presupuesto insuficiente"

        if vehiculo.stock <= 0:
            return "Error: sin stock"

        cot_id = f"cot_{len(self.db.cotizaciones)+1}"

        cot = Cotizacion(
            id=cot_id,
            cliente_id=cliente_id,
            vehiculo_id=vehiculo_id,
            precio_final=vehiculo.precio,
            estado="pendiente",
        )

        self.db.cotizaciones[cot_id] = cot
        return cot

    @is_tool(ToolType.WRITE)
    def aprobar_cotizacion(self, cotizacion_id: str):
        cot = self.db.cotizaciones.get(cotizacion_id)

        if not cot:
            return "Error: no existe"

        if not self._identidad_verificada(cot.cliente_id):
            return "Error: identidad no verificada"

        cot.estado = "aprobada"
        return cot

    @is_tool(ToolType.WRITE)
    def crear_pedido(self, cotizacion_id: str):
        cot = self.db.cotizaciones.get(cotizacion_id)

        if not cot:
            return "Error: cotizacion no existe"

        if cot.estado != "aprobada":
            return "Error: cotizacion no aprobada"

        if not self._identidad_verificada(cot.cliente_id):
            return "Error: identidad no verificada"

        vehiculo = self.db.vehiculos.get(cot.vehiculo_id)

        if vehiculo.stock <= 0:
            return "Error: sin stock"

        vehiculo.stock -= 1

        ped_id = f"ped_{len(self.db.pedidos)+1}"

        ped = Pedido(
            id=ped_id,
            cotizacion_id=cotizacion_id,
            estado="confirmado",
        )

        self.db.pedidos[ped_id] = ped
        return ped

    @is_tool(ToolType.WRITE)
    def cancelar_pedido(self, pedido_id: str):
        ped = self.db.pedidos.get(pedido_id)

        if not ped:
            return "Error: pedido no existe"

        cot = self.db.cotizaciones.get(ped.cotizacion_id)
        if cot and not self._identidad_verificada(cot.cliente_id):
            return "Error: identidad no verificada"

        ped.estado = "cancelado"
        return ped
