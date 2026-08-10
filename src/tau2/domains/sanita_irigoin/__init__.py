from typing import Dict, Literal
from pydantic import BaseModel
from tau2.environment.db import DB


class User(BaseModel):
    user_id: str
    nombre: str
    tipo_cliente: Literal["nuevo", "frecuente"]


class Suelo(BaseModel):
    suelo_id: str
    nombre: str
    ph: float
    nivel_nutrientes: Literal["bajo", "medio", "alto"]


class Cultivo(BaseModel):
    cultivo_id: str
    etapa: Literal["almacigo", "siembra", "crecimiento", "cosecha"]


class Producto(BaseModel):
    producto_id: str
    nombre: str
    tipo: Literal["fertilizante", "herbicida", "plaguicida"]
    composicion: str
    precio: float
    stock: int


class Pedido(BaseModel):
    order_id: str
    user_id: str
    producto_id: str
    cantidad: int
    metodo_pago: Literal["efectivo", "transferencia"]
    estado_pago: Literal["al contado", "credito", "cuotas"]
    estado_entrega: Literal["pendiente", "entregado"]


class Inventario(BaseModel):
    producto_id: str
    stock_actual: int
    stock_minimo: int


class Diagnostico(BaseModel):
    diagnostico_id: str
    suelo_id: str
    cultivo_id: str
    problema: Literal["bajo_nutrientes", "salinidad", "plagas", "maleza"]


class ArrozDB(DB):
    users: Dict[str, User] = {}
    suelos: Dict[str, Suelo] = {}
    cultivos: Dict[str, Cultivo] = {}
    productos: Dict[str, Producto] = {}
    pedidos: Dict[str, Pedido] = {}
    inventario: Dict[str, Inventario] = {}
    diagnosticos: Dict[str, Diagnostico] = {}