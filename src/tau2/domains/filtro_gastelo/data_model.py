from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field
from pathlib import Path
from tau2.environment.db import DB
filtro_DB_PATH = Path(__file__).parent / "filtros.json" 

OrderStatus = Literal['Confirmed']

class Customer(BaseModel):
    customer_id: str = Field(description="ID único del cliente (ejemplo: C-001)")
    name: str = Field(description="Nombre completo del cliente")
    phone: str = Field(description="Número de celular del cliente")
    past_orders: int=Field(description='Número de compras pasadas')

class Filter(BaseModel):
    item_id: str = Field(description="ID único del filtro (ejemplo: JD-101)")
    brand: str = Field(description="Marca del filtro (John Deere, Caterpillar, Fleetguard, Donaldson, Case IH, Komatsu)")
    name: str = Field(description="Nombre descriptivo del filtro")
    type: str = Field(description="Tipo de filtro (Aceite, Aire, Hidráulico, Combustible)")
    price: float = Field(description="Precio en soles (S/.)")
    stock: int = Field(description="Unidades disponibles en almacén")
    equivalent_id: Optional[str] = Field(default=None, description="ID del filtro compatible que puede reemplazarlo")

class FiltrosDB(DB):
    customers: Dict[str, Customer] = Field(description="Diccionario de clientes indexado por customer_id")
    inventory: Dict[str, Filter] = Field(description="Diccionario de filtros indexado por item_id")
    provider_orders: Dict[str, dict] = Field(default={}, description="Pedidos registrados a proveedor")
    def get_statistics(self) -> dict[str, Any]:
        return {
            "num_filters": len(self.inventory),
            "num_customers": len(self.customers),
            "num_provider_orders": len(self.provider_orders)
            }
def get_db(path: Path = filtro_DB_PATH):
    return FiltrosDB.load(path)