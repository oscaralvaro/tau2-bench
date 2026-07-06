from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from tau2.domains.lopez.utils import GAMERBIT_STORE_DB_PATH
from tau2.environment.db import DB


class CategoriaProducto(str, Enum):
    LAPTOP = "laptop"
    PC = "pc"
    MONITOR = "monitor"
    PERIFERICO = "periferico"
    COMPONENTE = "componente"


class EstadoPedido(str, Enum):
    PENDIENTE = "pendiente"
    CONFIRMADO = "confirmado"
    CANCELADO = "cancelado"
    ENTREGADO = "entregado"


class EstadoTicket(str, Enum):
    ABIERTO = "abierto"
    EN_DIAGNOSTICO = "en_diagnostico"
    ESPERANDO_APROBACION = "esperando_aprobacion"
    EN_REPARACION = "en_reparacion"
    LISTO = "listo"
    CERRADO = "cerrado"
    RECHAZADO = "rechazado"


class RolCuenta(str, Enum):
    CLIENTE = "cliente"
    EMPLEADO = "empleado"


class TipoGarantia(str, Enum):
    TIENDA = "tienda"
    FABRICANTE = "fabricante"
    CONSULTAR = "consultar"
    NO_APLICA = "no_aplica"


class EspecialidadTecnico(str, Enum):
    HARDWARE = "hardware"
    SOFTWARE = "software"
    LAPTOPS = "laptops"
    PERIFERICOS = "perifericos"


class Cliente(BaseModel):
    id: str = Field(description="Identificador unico del cliente")
    nombre: str = Field(description="Nombre completo del cliente")
    correo: str = Field(description="Correo electronico del cliente")
    telefono: str = Field(description="Telefono del cliente")
    rol: RolCuenta = Field(description="Rol de la cuenta para validacion de identidad")


class Producto(BaseModel):
    id: str = Field(description="Identificador unico del producto")
    nombre: str = Field(description="Nombre comercial del producto")
    categoria: CategoriaProducto = Field(description="Categoria del producto")
    precio: float = Field(description="Precio del producto")
    stock: int = Field(description="Cantidad disponible en stock")
    garantia_meses: int = Field(description="Meses de garantia comercial")
    activo: bool = Field(description="Indica si el producto esta disponible para venta")


class PedidoItem(BaseModel):
    producto_id: str = Field(description="Identificador del producto")
    cantidad: int = Field(description="Cantidad solicitada")
    precio_unitario: float = Field(description="Precio unitario aplicado")


class Pedido(BaseModel):
    id: str = Field(description="Identificador unico del pedido")
    cliente_id: str = Field(description="Cliente asociado al pedido")
    items: list[PedidoItem] = Field(description="Items incluidos en el pedido")
    total: float = Field(description="Total del pedido")
    estado: EstadoPedido = Field(description="Estado actual del pedido")


class TicketSoporte(BaseModel):
    id: str = Field(description="Identificador del ticket de soporte")
    cliente_id: str = Field(description="Cliente asociado al ticket")
    producto_id: str = Field(description="Producto reportado")
    motivo: str = Field(description="Motivo reportado por el cliente")
    estado: EstadoTicket = Field(description="Estado actual del ticket")
    diagnostico: Optional[str] = Field(
        default=None, description="Diagnostico registrado por soporte"
    )
    solucion: Optional[str] = Field(
        default=None, description="Solucion final aplicada al caso"
    )
    costo_estimado: Optional[float] = Field(
        default=None, description="Costo estimado cuando no cubre garantia"
    )
    requiere_aprobacion: bool = Field(
        description="Indica si el cliente debe aprobar la reparacion"
    )
    aplica_garantia: Optional[bool] = Field(
        default=None, description="Indica si el caso califica para garantia"
    )
    listo_para_recojo: bool = Field(
        description="Indica si el equipo ya esta listo para recojo"
    )


class Garantia(BaseModel):
    id: str = Field(description="Identificador de la garantia")
    cliente_id: str = Field(description="Cliente propietario del producto")
    producto_id: str = Field(description="Producto cubierto")
    fecha_compra: str = Field(description="Fecha de compra en formato YYYY-MM-DD")
    vigente: bool = Field(description="Indica si la garantia sigue vigente")
    tipo_garantia: TipoGarantia = Field(description="Tipo de garantia aplicable")
    cobertura: str = Field(description="Cobertura resumida de la garantia")
    observaciones: Optional[str] = Field(
        default=None, description="Condiciones y observaciones relevantes"
    )


class Tecnico(BaseModel):
    id: str = Field(description="Identificador del tecnico")
    nombre: str = Field(description="Nombre del tecnico")
    especialidad: EspecialidadTecnico = Field(description="Especialidad del tecnico")
    disponible: bool = Field(description="Disponibilidad actual del tecnico")


class VerificacionSMS(BaseModel):
    id: str = Field(description="Identificador del desafio de verificacion")
    cliente_id: str = Field(description="Cliente al que se envio el codigo")
    rol_requerido: RolCuenta = Field(description="Rol que se desea validar")
    codigo: str = Field(description="Codigo numerico enviado por SMS")
    enviada_a: str = Field(description="Telefono de destino")
    activa: bool = Field(description="Indica si el desafio sigue vigente")
    verificada: bool = Field(description="Indica si el codigo ya fue validado")
    intentos: int = Field(description="Cantidad de intentos de validacion realizados")


class GamerBitStoreDB(DB):
    clientes: Dict[str, Cliente] = Field(description="Clientes indexados por id")
    productos: Dict[str, Producto] = Field(description="Productos indexados por id")
    pedidos: Dict[str, Pedido] = Field(description="Pedidos indexados por id")
    tickets_soporte: Dict[str, TicketSoporte] = Field(
        description="Tickets de soporte indexados por id"
    )
    garantias: Dict[str, Garantia] = Field(description="Garantias indexadas por id")
    tecnicos: Dict[str, Tecnico] = Field(description="Tecnicos indexados por id")
    verificaciones_sms: Dict[str, VerificacionSMS] = Field(
        description="Desafios SMS indexados por id"
    )

    def get_statistics(self) -> dict[str, Any]:
        return {
            "num_clientes": len(self.clientes),
            "num_productos": len(self.productos),
            "num_pedidos": len(self.pedidos),
            "num_tickets_soporte": len(self.tickets_soporte),
            "num_garantias": len(self.garantias),
            "num_tecnicos": len(self.tecnicos),
            "num_verificaciones_sms": len(self.verificaciones_sms),
        }


def get_db() -> GamerBitStoreDB:
    return GamerBitStoreDB.load(GAMERBIT_STORE_DB_PATH)
