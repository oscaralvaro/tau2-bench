from tau2.domains.sanita_irigoin.data_model import ArrozDB
from tau2.environment.toolkit import RAGToolKit, ToolType, is_tool


class ArrozToolKit(RAGToolKit):
    """Herramientas para el dominio de insumos agricolas para arroz."""
    db: ArrozDB

    def __init__(self, db: ArrozDB, policy_index=None, retrieval_k: int = 3) -> None:
        super().__init__(db, policy_index=policy_index, retrieval_k=retrieval_k)

    @is_tool(ToolType.READ)
    def get_user_details(self, user_id: str) -> dict:
        """
        Obtiene la informacion de un cliente dado su user_id.
        Retorna nombre y tipo de cliente (nuevo/frecuente).
        Retorna error si el usuario no existe.
        """
        user = self.db.users.get(user_id)
        if not user:
            return {"error": f"Usuario '{user_id}' no encontrado."}
        return user.model_dump()

    @is_tool(ToolType.READ)
    def get_producto_details(self, producto_id: str) -> dict:
        """
        Devuelve informacion completa de un producto usando su producto_id exacto.

        Argumentos:
        - producto_id: codigo interno del producto, por ejemplo "P001", "P002",
          "P003". No usar el nombre comercial como "Urea 46%" o "NPK 20-20-20".

        Uso correcto:
        - get_producto_details(producto_id="P001") para consultar Urea 46%.
        - get_producto_details(producto_id="P002") para consultar NPK 20-20-20.

        Uso incorrecto:
        - get_producto_details(producto_id="Urea 46%")
        - get_producto_details(producto_id="NPK 20-20-20")

        Retorna nombre, tipo, composicion, precio y stock actual.
        Retorna error si el producto_id no existe.
        """
        producto = self.db.productos.get(producto_id)
        if not producto:
            return {"error": f"Producto '{producto_id}' no encontrado."}
        return producto.model_dump()

    @is_tool(ToolType.READ)
    def check_stock(self, producto_id: str) -> dict:
        """
        Verifica si un producto tiene stock disponible usando su producto_id exacto.

        Argumentos:
        - producto_id: codigo interno del producto, por ejemplo "P001", "P002",
          "P003". No usar nombres de producto en este argumento.

        Uso correcto:
        - check_stock(producto_id="P001") para verificar stock de Urea 46%.
        - check_stock(producto_id="P002") para verificar stock de NPK 20-20-20.

        Uso incorrecto:
        - check_stock(producto_id="Urea 46%")
        - check_stock(producto_id="NPK 20-20-20")

        En un cambio de opinion del cliente, volver a llamar check_stock con el
        producto_id final antes de crear el pedido. Por ejemplo, si primero queria
        P001 y luego cambia a NPK 20-20-20, usar check_stock(producto_id="P002").

        Retorna el stock actual y si esta disponible (True/False).
        Retorna error si el producto_id no existe.
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

    @is_tool(ToolType.READ)
    def get_soil_details(self, suelo_id: str) -> dict:
        """
        Obtiene las caracteristicas de un suelo dado su suelo_id:
        nombre, pH y nivel de nutrientes.
        Retorna error si el suelo no existe.
        """
        suelo = self.db.suelos.get(suelo_id)
        if not suelo:
            return {"error": f"Suelo '{suelo_id}' no encontrado."}
        return suelo.model_dump()

    @is_tool(ToolType.READ)
    def get_crop_details(self, cultivo_id: str) -> dict:
        """
        Obtiene la informacion de un cultivo dado su cultivo_id:
        etapa actual del arroz (almacigo, siembra, crecimiento, cosecha).
        Retorna error si el cultivo no existe.
        """
        cultivo = self.db.cultivos.get(cultivo_id)
        if not cultivo:
            return {"error": f"Cultivo '{cultivo_id}' no encontrado."}
        return cultivo.model_dump()

    @is_tool(ToolType.READ)
    def recommend_fertilizer(self, diagnostico_id: str, presupuesto: float) -> dict:
        """
        Recomienda un fertilizante adecuado basado en el diagnostico del suelo
        y el presupuesto del cliente. Solo recomienda productos con stock
        disponible y que entren en el presupuesto.
        Retorna error si no hay recomendacion posible.
        """
        diagnostico = self.db.diagnosticos.get(diagnostico_id)
        if not diagnostico:
            return {"error": f"Diagnostico '{diagnostico_id}' no encontrado."}

        suelo = self.db.suelos.get(diagnostico.suelo_id)
        if not suelo:
            return {"error": "Suelo asociado al diagnostico no encontrado."}

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

    @is_tool(ToolType.READ)
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

    @is_tool(ToolType.READ)
    def validate_budget(self, producto_id: str, presupuesto: float) -> dict:
        """
        Verifica si el precio de un producto entra dentro del presupuesto
        del cliente. Retorna si es viable y cuanto costaria.
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

    @is_tool(ToolType.WRITE)
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
                "El credito esta disponible solo para clientes frecuentes."
            }

        if producto.stock < cantidad:
            return {"error": f"Stock insuficiente. Stock disponible: {producto.stock} unidades."}

        if metodo_pago not in ("efectivo", "transferencia"):
            return {"error": "Metodo de pago invalido. Use 'efectivo' o 'transferencia'."}

        if estado_pago not in ("al contado", "credito", "cuotas"):
            return {"error": "Estado de pago invalido. Use 'al contado', 'credito' o 'cuotas'."}

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

    @is_tool(ToolType.READ)
    def get_order_details(self, order_id: str) -> dict:
        """
        Retorna los detalles de un pedido dado su order_id.
        Retorna error si el pedido no existe.
        """
        pedido = self.db.pedidos.get(order_id)
        if not pedido:
            return {"error": f"Pedido '{order_id}' no encontrado."}
        return pedido.model_dump()

    @is_tool(ToolType.WRITE)
    def escalate_to_human(self, motivo: str) -> dict:
        """
        Escala la conversacion a un vendedor humano cuando el agente
        no puede resolver la solicitud. Usar cuando el cliente solicita
        atencion humana, la consulta es muy tecnica, o hay un problema
        con un pedido ya entregado.
        Retorna confirmacion del escalamiento.
        """
        return {
            "escalado": True,
            "mensaje": (
                f"Su consulta ha sido escalada a un vendedor humano. "
                f"Motivo: {motivo}. En breve sera atendido."
            ),
        }

    @is_tool(ToolType.WRITE)
    def send_sms_code(self, user_id: str) -> dict:
        """
        Envia un codigo de verificacion SMS al usuario para autenticar
        operaciones sensibles. Debe llamarse antes de ejecutar acciones
        que requieran verificacion de identidad.
        Retorna el codigo enviado (en simulacion se expone para pruebas).
        El codigo es determinístico basado en el user_id para verificación.
        """
        import hashlib
        user = self.db.users.get(user_id)
        if not user:
            return {"error": f"Usuario '{user_id}' no encontrado."}

        # Generar código determinístico basado en hash del user_id
        hash_obj = hashlib.sha256(user_id.encode())
        hash_hex = hash_obj.hexdigest()
        codigo = str(int(hash_hex[:6], 16) % 1000000).zfill(6)
        
        from tau2.domains.sanita_irigoin.user_tools import _sms_codes
        _sms_codes[user_id] = codigo

        return {
            "mensaje": f"Codigo SMS enviado al usuario {user_id}.",
            "codigo_enviado": codigo,
        }

    @is_tool(ToolType.WRITE)
    def verify_sms_code(self, user_id: str, codigo: str, rol: str = "user") -> dict:
        """
        Verifica el codigo SMS proporcionado por el usuario.
        Tambien valida el rol del usuario (user, employee, admin).
        Roles validos: 'user', 'employee', 'admin'.
        Retorna exito si el codigo es correcto y el rol es valido,
        error si el codigo es incorrecto o el rol no coincide.
        """
        from tau2.domains.sanita_irigoin.user_tools import _sms_codes

        roles_validos = ["user", "employee", "admin"]
        if rol not in roles_validos:
            return {"error": f"Rol '{rol}' no valido. Roles permitidos: {roles_validos}"}

        codigo_esperado = _sms_codes.get(user_id)
        if not codigo_esperado:
            return {"error": "No se ha enviado ningun codigo SMS a este usuario."}

        if codigo != codigo_esperado:
            return {"error": "Codigo SMS incorrecto. Verifique e intente nuevamente."}

        user = self.db.users.get(user_id)
        return {
            "verificado": True,
            "user_id": user_id,
            "rol": rol,
            "nombre": user.nombre if user else "Desconocido",
            "mensaje": "Identidad verificada correctamente.",
        }
