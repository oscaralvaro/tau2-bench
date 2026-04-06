from tau2.domains.ecommerce_calle.data_model import EcommerceDB
from tau2.domains.ecommerce_calle.user_data_model import UserProfile, UserOrderSummary
from tau2.environment.toolkit import ToolKitBase, ToolType, is_tool


class EcommerceUserToolKit(ToolKitBase):
    """Herramientas disponibles para el usuario simulado durante la conversacion."""

    db: EcommerceDB

    def __init__(self, db: EcommerceDB) -> None:
        super().__init__(db)

    @is_tool(ToolType.READ)
    def get_my_profile(self, user_id: str) -> dict:
        """Obtiene el perfil del usuario y su historial de pedidos."""
        user = self.db.users.get(user_id)
        if not user:
            return {"error": f"Usuario {user_id} no encontrado."}

        orders = [
            UserOrderSummary(
                order_id=o.order_id,
                date=o.date,
                status=o.status,
                total=o.total,
                items=o.items,
            )
            for o in self.db.orders.values()
            if o.user_id == user_id
        ]

        profile = UserProfile(
            user_id=user.user_id,
            name=user.name,
            email=user.email,
            customer_type=user.customer_type,
            orders=orders,
        )
        return profile.model_dump()

    @is_tool(ToolType.READ)
    def get_my_order_status(self, order_id: str, user_id: str) -> dict:
        """Permite al usuario verificar el estado de uno de sus pedidos."""
        order = self.db.orders.get(order_id)
        if not order:
            return {"error": f"Pedido {order_id} no encontrado."}
        if order.user_id != user_id:
            return {"error": "Este pedido no pertenece a tu cuenta."}
        return {
            "order_id": order.order_id,
            "status": order.status,
            "total": order.total,
            "date": order.date,
        }

    @is_tool(ToolType.READ)
    def get_my_return_status(self, order_id: str) -> dict:
        """Permite al usuario verificar si tiene una devolucion activa para un pedido."""
        ret = next(
            (r for r in self.db.returns.values() if r.order_id == order_id), None
        )
        if not ret:
            return {"error": f"No hay devolucion registrada para el pedido {order_id}."}
        return {
            "return_id": ret.return_id,
            "order_id": ret.order_id,
            "status": ret.status,
            "approved": ret.approved,
        }