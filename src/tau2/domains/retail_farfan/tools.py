from typing import List
from tau2.environment.toolkit import ToolKitBase
from .data_model import Order, Return, Payment


class RetailTools(ToolKitBase):

    def __init__(self, db):
        self.db = db

    # =========================
    # USER
    # =========================
    def get_user_details(self, user_id: str):
        if user_id not in self.db.users:
            raise Exception("Usuario no existe")
        return self.db.users[user_id]

    # =========================
    # PRODUCTOS
    # =========================
    def search_products(self, keyword: str):
        return [
            p for p in self.db.products.values() if keyword.lower() in p.nombre.lower()
        ]

    # =========================
    # PEDIDOS
    # =========================
    def create_order(self, user_id: str, product_ids: List[str]):
        user = self.get_user_details(user_id)

        if user.estado != "activo":
            raise Exception("Usuario bloqueado")

        total = 0

        for pid in product_ids:
            product = self.db.products.get(pid)

            if not product:
                raise Exception(f"Producto {pid} no existe")

            if product.stock <= 0:
                raise Exception(f"Producto {pid} sin stock")

            total += product.precio
            product.stock -= 1

        order_id = f"ORD{len(self.db.orders)+1}"

        order = Order(
            order_id=order_id,
            user_id=user_id,
            productos=product_ids,
            total=total,
            estado="pendiente",
        )

        self.db.orders[order_id] = order
        return order

    def cancel_order(self, order_id: str):
        order = self.db.orders.get(order_id)

        if not order:
            raise Exception("Pedido no existe")

        if order.estado not in ["pendiente", "enviado"]:
            raise Exception("No se puede cancelar este pedido")

        order.estado = "cancelado"
        return order

    def track_order(self, order_id: str):
        if order_id not in self.db.orders:
            raise Exception("Pedido no existe")

        return self.db.orders[order_id]

    # =========================
    # DEVOLUCIONES
    # =========================
    def request_return(self, order_id: str, motivo: str):

        order = self.track_order(order_id)

        if order.estado != "entregado":
            raise Exception("No elegible para devolución")

        # Evitar duplicados
        for r in self.db.returns.values():
            if r.order_id == order_id:
                raise Exception("Ya existe una devolución para este pedido")

        return_id = f"RET{len(self.db.returns)+1}"

        new_return = Return(
            return_id=return_id, order_id=order_id, motivo=motivo, estado="solicitada"
        )

        self.db.returns[return_id] = new_return
        return new_return

    # =========================
    # PAGOS
    # =========================
    def process_payment(self, order_id: str, metodo: str):

        # Validar existencia
        if order_id not in self.db.orders:
            raise Exception("Pedido no existe")

        # Evitar pagos duplicados
        for p in self.db.payments.values():
            if p.order_id == order_id:
                raise Exception("Este pedido ya fue pagado")

        payment_id = f"PAY{len(self.db.payments)+1}"

        payment = Payment(
            payment_id=payment_id,
            order_id=order_id,
            metodo_pago=metodo,
            estado="pagado",
        )

        self.db.payments[payment_id] = payment
        return payment
