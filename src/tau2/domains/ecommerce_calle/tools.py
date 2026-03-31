from datetime import datetime, date
from tau2.domains.ecommerce_calle.data_model import EcommerceDB, OrderStatus, Return
from tau2.environment.toolkit import ToolKitBase, ToolType, is_tool


class EcommerceToolKit(ToolKitBase):
    """Tools for an e-commerce customer support domain."""

    db: EcommerceDB

    def __init__(self, db: EcommerceDB) -> None:
        super().__init__(db)

    @is_tool(ToolType.READ)
    def get_user_details(self, user_id: str) -> dict:
        """Obtiene los datos del cliente dado su user_id."""
        user = self.db.users.get(user_id)
        if not user:
            return {"error": f"Usuario {user_id} no encontrado."}
        return user.model_dump()

    @is_tool(ToolType.READ)
    def get_order_details(self, order_id: str) -> dict:
        """Obtiene informacion completa de un pedido dado su order_id."""
        order = self.db.orders.get(order_id)
        if not order:
            return {"error": f"Pedido {order_id} no encontrado."}
        return order.model_dump()

    @is_tool(ToolType.READ)
    def search_orders_by_user(self, user_id: str) -> dict:
        """Lista todos los pedidos de un usuario dado su user_id."""
        if user_id not in self.db.users:
            return {"error": f"Usuario {user_id} no encontrado."}
        orders = [o.model_dump() for o in self.db.orders.values()
                  if o.user_id == user_id]
        return {"orders": orders}

    @is_tool(ToolType.READ)
    def track_shipment(self, order_id: str) -> dict:
        """Devuelve el estado y numero de seguimiento del envio de un pedido."""
        shipment = next(
            (s for s in self.db.shipments.values() if s.order_id == order_id), None
        )
        if not shipment:
            return {"error": f"No hay envio registrado para el pedido {order_id}."}
        return shipment.model_dump()

    @is_tool(ToolType.WRITE)
    def cancel_order(self, order_id: str) -> dict:
        """Cancela un pedido si esta en estado pending_payment o processing."""
        order = self.db.orders.get(order_id)
        if not order:
            return {"error": f"Pedido {order_id} no encontrado."}
        if order.status not in [OrderStatus.pending_payment, OrderStatus.processing]:
            return {"error": "No se puede cancelar: el pedido ya fue enviado o entregado."}
        order.status = OrderStatus.cancelled
        return {"success": True, "message": f"Pedido {order_id} cancelado exitosamente."}

    @is_tool(ToolType.WRITE)
    def update_shipping_address(self, order_id: str, new_address: str) -> dict:
        """Actualiza la direccion de envio si el pedido aun no ha sido enviado."""
        order = self.db.orders.get(order_id)
        if not order:
            return {"error": f"Pedido {order_id} no encontrado."}
        if order.status in [OrderStatus.shipped, OrderStatus.out_for_delivery,
                             OrderStatus.delivered, OrderStatus.cancelled,
                             OrderStatus.returned]:
            return {"error": "No se puede cambiar la direccion: el pedido ya fue enviado."}
        order.shipping_address = new_address
        return {"success": True, "message": f"Direccion actualizada a: {new_address}"}

    @is_tool(ToolType.WRITE)
    def request_return(self, order_id: str, reason: str, user_id: str) -> dict:
        """Solicita una devolucion si el pedido cumple las condiciones de politica."""
        order = self.db.orders.get(order_id)
        if not order:
            return {"error": f"Pedido {order_id} no encontrado."}
        if order.user_id != user_id:
            return {"error": "No tienes permiso para gestionar este pedido."}
        if order.status != OrderStatus.delivered:
            return {"error": "Solo se pueden devolver pedidos entregados."}

        user = self.db.users.get(user_id)
        delivery_date = datetime.strptime(order.date, "%Y-%m-%d").date()
        days_limit = 60 if user and user.customer_type == "premium" else 30
        days_since = (date.today() - delivery_date).days
        if days_since > days_limit:
            return {"error": f"Fuera del plazo de devolucion ({days_limit} dias)."}

        for pid in order.items:
            product = self.db.products.get(pid)
            if product and not product.return_allowed:
                return {"error": f"El producto {product.name} no permite devolucion."}

        return_id = f"RET-{order_id}"
        new_return = Return(
            return_id=return_id, order_id=order_id,
            reason=reason, status="pending", approved=False
        )
        self.db.returns[return_id] = new_return
        return {"success": True, "return_id": return_id, "status": "pending"}

    @is_tool(ToolType.WRITE)
    def request_replacement(self, order_id: str, reason: str) -> dict:
        """Solicita un reemplazo por producto defectuoso o incorrecto."""
        order = self.db.orders.get(order_id)
        if not order:
            return {"error": f"Pedido {order_id} no encontrado."}
        if order.status != OrderStatus.delivered:
            return {"error": "Solo se puede pedir reemplazo de pedidos entregados."}
        return {"success": True,
                "message": f"Reemplazo solicitado para pedido {order_id}. Razon: {reason}"}

    @is_tool(ToolType.WRITE)
    def issue_refund(self, order_id: str) -> dict:
        """Procesa un reembolso si la devolucion fue aprobada."""
        ret = next(
            (r for r in self.db.returns.values() if r.order_id == order_id), None
        )
        if not ret:
            return {"error": "No hay devolucion registrada para este pedido."}
        if not ret.approved:
            return {"error": "La devolucion aun no ha sido aprobada."}
        order = self.db.orders.get(order_id)
        return {"success": True,
                "message": f"Reembolso de S/{order.total} procesado al metodo de pago original."}

    @is_tool(ToolType.WRITE)
    def escalate_to_human(self, order_id: str, reason: str) -> dict:
        """Escala el caso a un agente humano."""
        return {"success": True,
                "message": f"Caso del pedido {order_id} escalado a agente humano. Razon: {reason}"}