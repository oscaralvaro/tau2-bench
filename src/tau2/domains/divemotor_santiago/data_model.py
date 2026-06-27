from pydantic import BaseModel
from typing import Dict
from tau2.environment.db import DB


class Cliente(BaseModel):
    id: str
    nombre: str
    tipo: str  # empresa / persona
    presupuesto: float
    rol: str = "user"


class Vehiculo(BaseModel):
    id: str
    nombre: str
    tipo: str  # camion / bus / auto
    precio: float
    stock: int


class Cotizacion(BaseModel):
    id: str
    cliente_id: str
    vehiculo_id: str
    precio_final: float
    estado: str  # pendiente / aprobada / rechazada


class Pedido(BaseModel):
    id: str
    cotizacion_id: str
    estado: str  # confirmado / cancelado


class CodigoSMS(BaseModel):
    cliente_id: str
    codigo: str
    rol_requerido: str
    verificado: bool = False


class DivemotorDB(DB):
    users: Dict[str, Cliente]
    clientes: Dict[str, Cliente]
    vehiculos: Dict[str, Vehiculo]
    cotizaciones: Dict[str, Cotizacion]
    pedidos: Dict[str, Pedido]
    codigos_sms: Dict[str, CodigoSMS] = {}
