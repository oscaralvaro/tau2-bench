from tau2.environment.toolkit import ToolKitBase
from tau2.domains.sanita_irigoin.data_model import ArrozDB


class ArrozToolKit(ToolKitBase):
    db: ArrozDB

    def get_user_details(self, user_id: str) -> dict:
        """
        Obtiene la información de un cliente dado su user_id.
        Retorna nombre y tipo de cliente (nuevo/frecuente).
        Retorna error si el usuario no existe.
        """
        user = self.db.users.get(user_id)
        if not user:
            return {"error": f"Usuario '{user_id}' no encontrado."}
        return user.model_dump()

    def get_producto_details(self, producto_id: str) -> dict:
        """
        Devuelve información completa de un producto dado su producto_id:
        nombre, tipo, composición, precio y stock actual.
        Retorna error si el producto no existe.
        """
        producto = self.db.productos.get(producto_id)
        if not producto:
            return {"error": f"Producto '{producto_id}' no encontrado."}
        return producto.model_dump()

    def check_stock(self, producto_id: str) -> dict:
        """
        Verifica si un producto tiene stock disponible.
        Retorna el stock actual y si está disponible (True/False).
        Retorna error si el producto no existe.
        """
        producto = self.db.productos.get(producto_id)
        if not producto:
            return {"error": f"Producto '{producto_id}' no encontrado."}
        disponible = producto.stock > 0
        return {
            "producto_id": producto_id,
            "stock_actual": producto.stock,
            "disponible": disponible,
        }

    def get_soil_details(self, suelo_id: str) -> dict:
        """
        Obtiene las características de un suelo dado su suelo_id:
        nombre, pH y nivel de nutrientes.
        Retorna error si el suelo no existe.
        """
        suelo = self.db.suelos.get(suelo_id)
        if not suelo:
            return {"error": f"Suelo '{suelo_id}' no encontrado."}
        return suelo.model_dump()

    def get_crop_details(self, cultivo_id: str) -> dict:
        """
        Obtiene la información de un cultivo dado su cultivo_id:
        etapa actual del arroz (almacigo, siembra, crecimiento, cosecha).
        Retorna error si el cultivo no existe.
        """
        cultivo = self.db.cultivos.get(cultivo_id)
        if not cultivo:
            return {"error": f"Cultivo '{cultivo_id}' no encontrado."}
        return cultivo.model_dump()

    def recommend_fertilizer(self, diagnostico_id: str, presupuesto: float) -> dict:
        """
        Recomienda un fertilizante adecuado basado en el diagnóstico del suelo
        y el presupuesto del cliente. Solo recomienda productos con stock
        disponible y que entren en el presupuesto.
        Retorna error si no hay recomendación posible.
        """
        diagnostico = self.db.diagnosticos.get(diagnostico_id)
        if not diagnostico:
            return {"error": f"Diagnóstico '{diagnostico_id}' no encontrado."}

        suelo = self.db.suelos.get(diagnostico.suelo_id)
        if not suelo:
            return {"error": "Suelo asociado al diagnóstico no encontrado."}

        candidatos = [
            p for p in self.db.productos.values()
            if p.tipo == "fertilizante" and p.stock > 0 and p.precio <= presupuesto
        ]

        if not candidatos:
            return {"error": "No hay fertilizantes disponibles dentro del presupuesto indicado."}

        recomendado = candidatos[0]
        return {
            "recomendacion": recomendado.model_dump(),
            "razon": (
                f"Producto adecuado para suelo {suelo.nombre} "
                f"con nivel de nutrientes {suelo.nivel_nutrientes}."
            ),
        }

    def suggest_alternative(self, producto_id: str) -> dict:
        """
        Sugiere un producto alternativo del mismo tipo cuando el producto
        solicitado no tiene stock disponible.
        Retorna error si no hay alternativas disponibles.
        """
        producto = self.db.productos.get(producto_id)
        if not producto:
            return {"error": f"Producto '{producto_id}' no encontrado."}

        alternativas = [
            p for pid, p in self.db.productos.items()
            if p.tipo == producto.tipo and pid != producto_id and p.stock > 0
        ]

        if not alternativas:
            return {"error": f"No hay alternativas disponibles para el tipo '{producto.tipo}'."}

        return {"alternativa": alternativas[0].model_dump()}

    def validate_budget(self, producto_id: str, presupuesto: float) -> dict:
        """
        Verifica si el precio de un producto entra dentro del presupuesto
        del cliente. Retorna si es viable y cuánto costaría.
        Retorna error si el producto no existe.
        """
        producto = self.db.productos.get(producto_id)
        if not producto:
            return {"error": f"Producto '{producto_id}' no encontrado."}

        viable = producto.precio <= presupuesto
        return {
            "producto_id": producto_id,
            "precio": producto.precio,
            "presupuesto": presupuesto,
            "viable": viable,
        }

    def create_order(
        self,
        user_id: str,
        producto_id: str,
        cantidad: int,
        metodo_pago: str,
        estado_pago: str,
    ) -> dict:
        """
        Crea un pedido para un cliente si hay stock suficiente.
        Reglas:
        - Clientes nuevos solo pueden pagar 'al contado'.
        - Clientes frecuentes pueden acceder a 'credito' o 'cuotas'.
        - Solo se crea el pedido si hay stock suficiente.
        - Descuenta el stock tras confirmar el pedido.
        Retorna el pedido creado o un error si no se puede procesar.
        """
        user = self.db.users.get(user_id)
        if not user:
            return {"error": f"Usuario '{user_id}' no encontrado."}

        producto = self.db.productos.get(producto_id)
        if not producto:
            return {"error": f"Producto '{producto_id}' no encontrado."}

        if estado_pago in ("credito", "cuotas") and user.tipo_cliente == "nuevo":
            return {
                "error": "Los clientes nuevos solo pueden pagar al contado. "
                "El crédito está disponible solo para clientes frecuentes."
            }

        if producto.stock < cantidad:
            return {"error": f"Stock insuficiente. Stock disponible: {producto.stock} unidades."}

        if metodo_pago not in ("efectivo", "transferencia"):
            return {"error": "Método de pago inválido. Use 'efectivo' o 'transferencia'."}

        if estado_pago not in ("al contado", "credito", "cuotas"):
            return {"error": "Estado de pago inválido. Use 'al contado', 'credito' o 'cuotas'."}

        order_id = f"ORD-{len(self.db.pedidos) + 1:03d}"
        nuevo_pedido = {
            "order_id": order_id,
            "user_id": user_id,
            "producto_id": producto_id,
            "cantidad": cantidad,
            "metodo_pago": metodo_pago,
            "estado_pago": estado_pago,
            "estado_entrega": "pendiente",
        }

        from tau2.domains.sanita_irigoin.data_model import Pedido
        self.db.pedidos[order_id] = Pedido(**nuevo_pedido)
        self.db.productos[producto_id].stock -= cantidad

        return {"pedido_creado": nuevo_pedido}

    def get_order_details(self, order_id: str) -> dict:
        """
        Retorna los detalles de un pedido dado su order_id.
        Retorna error si el pedido no existe.
        """
        pedido = self.db.pedidos.get(order_id)
        if not pedido:
            return {"error": f"Pedido '{order_id}' no encontrado."}
        return pedido.model_dump()

    def escalate_to_human(self, motivo: str) -> dict:
        """
        Escala la conversación a un vendedor humano cuando el agente
        no puede resolver la solicitud. Usar cuando el cliente solicita
        atención humana, la consulta es muy técnica, o hay un problema
        con un pedido ya entregado.
        Retorna confirmación del escalamiento.
        """
        return {
            "escalado": True,
            "mensaje": (
                f"Su consulta ha sido escalada a un vendedor humano. "
                f"Motivo: {motivo}. En breve será atendido."
            ),
        }