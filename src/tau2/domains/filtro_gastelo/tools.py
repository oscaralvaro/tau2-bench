from tau2.domains.filtro_gastelo.data_model import FiltrosDB, Customer, Filter
from tau2.environment.toolkit import ToolKitBase, ToolType, is_tool 
from typing import Optional

class FiltrosTools(ToolKitBase):
    "Herramientas simples para el pedido de filtros"
     
    db:FiltrosDB
    def __init__(self, db: FiltrosDB)-> None:
        super().__init__(db)
    
    def _find_filter_by_id(self, item_id: str) -> Filter:
        for filter in self.db.inventory.values():
            if filter.item_id.lower() == item_id.lower():
                return filter
        raise ValueError(f"Filtro '{item_id}' no encontrado")
    
    @is_tool(ToolType.READ)
    def search_filter_catalog(
        self,
        brand: Optional[str] = None,
        filter_type: Optional[str] = None
        ) -> dict:
        """
        Busca filtros en el catálogo por marca y/o tipo.
        Usa este tool cuando el cliente quiera ver opciones disponibles.
        Parámetros:
        - brand: Marca del filtro (John Deere, Caterpillar, Fleetguard, Donaldson, Case IH, Komatsu)
        - filter_type: Tipo de filtro (Aceite, Aire, Hidráulico, Combustible)
        Retorna lista de filtros con su ID, nombre, precio y stock.
        """
        results = []
        for f in self.db.inventory.values():
            match_brand = (brand is None) or (f.brand.lower() == brand.lower())
            match_type = (filter_type is None) or (f.type.lower() == filter_type.lower())
            if match_brand and match_type:
                results.append({
                    "item_id": f.item_id,
                    "brand": f.brand,
                    "name": f.name,
                    "type": f.type,
                    "price": f.price,
                    "stock": f.stock
                })
        if not results:
            return {"error": "No se encontraron filtros con esos criterios."}
        return {"filters": results}


    @is_tool(ToolType.READ)
    def get_filter_status(self, item_id: str) -> dict:
        """
        Consulta el estado completo de un filtro específico por su ID.
        Úsalo SIEMPRE antes de prometer una entrega o buscar equivalentes.
        Retorna precio, stock, disponibilidad y si tiene un equivalente registrado.
        Parámetros:
        - item_id: ID único del filtro (ejemplo: JD-101, CAT-201)
        """
        if item_id.upper().startswith("CAR"):
            return {"error": "No aceptamos pedidos de filtros de autos"}
        try:
            f = self._find_filter_by_id(item_id)
        except ValueError:
            return {"error": f"No se encontró ningún filtro con ID '{item_id}'."}
        availability = "Entrega Inmediata" if f.stock > 0 else "Sin stock"
        return {
            "item_id": f.item_id,
            "brand": f.brand,
            "name": f.name,
            "type": f.type,
            "price_soles": f.price,
            "stock": f.stock,
            "availability": availability,
            "equivalent_id": f.equivalent_id
        }


    @is_tool(ToolType.READ)
    def get_equivalent_filter(self, item_id: str) -> dict:
        """
        Busca un filtro equivalente con stock disponible cuando el filtro
        solicitado está agotado. Solo retorna equivalentes marcados
        explícitamente en el sistema (campo equivalent_id).
        Úsalo SOLO si get_filter_status retornó stock=0.
        Parámetros:
        - item_id: ID del filtro agotado para el que se busca equivalente
        """
        try:
            original = self._find_filter_by_id(item_id)
        except ValueError:
            return {"error": f"No se encontró el filtro '{item_id}'."}

        if original.equivalent_id is None:
            return {"equivalent": None, "message": "Este filtro no tiene equivalente registrado en el sistema."}
        
        try:
            equivalent = self._find_filter_by_id(original.equivalent_id)
        except ValueError:
            return {"equivalent": None, "message": "El equivalente registrado no existe en el sistema."}
        if equivalent.stock == 0:
            return {"equivalent": None, "message": f"El equivalente {equivalent.brand} también está agotado."}
        return {
            "equivalent": {
                "item_id": equivalent.item_id,
                "brand": equivalent.brand,
                "name": equivalent.name,
                "price_soles": equivalent.price,
                "stock": equivalent.stock,
                "availability": "Entrega Inmediata"
            }
        }
    @is_tool(ToolType.READ)
    def get_customer_details(self, customer_id: str) -> dict:
        """
        Obtiene la información de un cliente registrado por su ID.
        También retorna el descuento aplicable según sus compras pasadas:
        - 20 o más compras: 5% de descuento
        - 40 o más compras: 10% de descuento
        Parámetros:
        - customer_id: ID del cliente (ejemplo: C-001, C-002)
        """
        customer = self.db.customers.get(customer_id)
        if not customer:
            return {"error": f"No se encontró ningún cliente con ID '{customer_id}'."}
        discount = 0
        if customer.past_orders >= 40:
            discount = 10
        elif customer.past_orders >= 10:
            discount = 5
        return {
            "customer_id": customer.customer_id,
            "name": customer.name,
            "phone": customer.phone,
            "past_orders": customer.past_orders,
            "discount_percentage": discount
        }
    
    @is_tool(ToolType.WRITE)
    def register_provider_order(
        self,
        customer_name: str,
        customer_phone: str,
        item_id: str,
        quantity: int
    ) -> dict:
        """

        Registra un pedido a proveedor cuando el filtro no tiene stock
        ni equivalente disponible. El tiempo de entrega es de 3 a 5 días hábiles.
        Úsalo SOLO si el cliente aceptó esperar y proporcionó sus datos.
        Parámetros:
        - customer_name: Nombre completo del cliente
        - customer_phone: Número de celular del cliente
        - item_id: ID del filtro a pedir al proveedor
        - quantity: Cantidad de unidades solicitadas
        """
        if item_id not in self.db.inventory:
            return {"error": f"El filtro '{item_id}' no existe en el catálogo."}
        if quantity <= 0:
            return {"error": "La cantidad debe ser mayor a 0."}
        filter_info = self.db.inventory[item_id]
        order_id = f"ORD-{len(self.db.provider_orders) + 1:03d}"
        order = {
            "order_id": order_id,
            "customer_name": customer_name,
            "customer_phone": customer_phone,
            "item_id": item_id,
            "item_name": filter_info.name,
            "brand": filter_info.brand,
            "quantity": quantity,
            "estimated_days": "3 a 5 días hábiles",
            "status": "Pendiente"
        }
        
        self.db.provider_orders[order_id] = order
        
        return {
            "success": True,
            "order_id": order_id,
            "message": f"Pedido registrado. El filtro {filter_info.brand} - {filter_info.name} llegará en 3 a 5 días hábiles.",
            "order": order
        }


    @is_tool(ToolType.WRITE)
    def escalate_to_human(self, reason: str) -> dict:
        """
        Transfiere la conversación a un agente humano cuando la solicitud
        está fuera de las capacidades del agente.
        Úsalo cuando:
        - El cliente pide descuentos no autorizados
        - El cliente pregunta por repuestos de motor internos
        - Existe una queja sobre un pedido previo que no puedes resolver
        Parámetros:
        - reason: Motivo del escalamiento
        """
        return {
            "escalated": True,
            "message": "Tu solicitud ha sido transferida a un agente humano. En breve se comunicarán contigo.",
            "reason": reason
        }