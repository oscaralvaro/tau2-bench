from __future__ import annotations
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from tau2.environment.db import DB
from tau2.domains.cable_calderon.utils import CABLE_CALDERON_DB_PATH


class ContactoAutorizado(BaseModel):
    """Persona autorizada para realizar cambios en la cuenta"""
    nombre: str = Field(description="Nombre completo del contacto autorizado")
    telefono: str = Field(description="Teléfono del contacto autorizado")


class Cliente(BaseModel):
    """Cliente de CableHogar"""
    cliente_id: str = Field(description="Identificador único del cliente")
    nombre_titular: str = Field(description="Nombre completo del titular del contrato")
    telefono: str = Field(description="Teléfono de contacto")
    email: str = Field(description="Correo electrónico")
    direccion: str = Field(description="Dirección de instalación")
    tiene_deuda: bool = Field(description="Si el cliente tiene deuda pendiente")
    monto_deuda: float = Field(description="Monto de deuda pendiente en soles")
    contactos_autorizados: List[ContactoAutorizado] = Field(
        default=[], description="Lista de personas autorizadas para hacer cambios"
    )


class Plan(BaseModel):
    """Plan de servicio disponible"""
    plan_id: str = Field(description="Identificador único del plan")
    nombre: str = Field(description="Nombre del plan")
    tipo: str = Field(description="Tipo: cable, internet o combo")
    velocidad_mbps: Optional[int] = Field(default=None, description="Velocidad en Mbps (solo internet/combo)")
    canales: Optional[int] = Field(default=None, description="Número de canales (solo cable/combo)")
    precio_mensual: float = Field(description="Precio mensual en soles")
    nivel: int = Field(description="Nivel del plan: 1=básico, 2=intermedio, 3=premium")


class Servicio(BaseModel):
    """Servicio activo de un cliente"""
    servicio_id: str = Field(description="Identificador único del servicio")
    cliente_id: str = Field(description="ID del cliente")
    plan_id: str = Field(description="ID del plan contratado")
    estado: str = Field(description="Estado: activo, suspendido, cancelado")
    fecha_inicio: str = Field(description="Fecha de inicio del servicio (YYYY-MM-DD)")
    fecha_vencimiento: str = Field(description="Fecha de vencimiento del ciclo actual (YYYY-MM-DD)")


class OrdenInstalacion(BaseModel):
    """Orden de instalación o visita técnica"""
    orden_id: str = Field(description="Identificador único de la orden")
    cliente_id: str = Field(description="ID del cliente")
    tipo: str = Field(description="Tipo: instalacion_nueva, mantenimiento, retiro")
    fecha_programada: str = Field(description="Fecha programada (YYYY-MM-DD)")
    hora_programada: str = Field(description="Hora programada (HH:MM)")
    tecnico_asignado: Optional[str] = Field(default=None, description="Nombre del técnico asignado")
    estado: str = Field(description="Estado: pendiente, confirmada, en_curso, completada, cancelada")


class Reclamo(BaseModel):
    """Reclamo o ticket de soporte"""
    reclamo_id: str = Field(description="Identificador único del reclamo")
    cliente_id: str = Field(description="ID del cliente")
    tipo: str = Field(description="Tipo: señal, facturacion, instalacion, otro")
    descripcion: str = Field(description="Descripción del problema")
    estado: str = Field(description="Estado: abierto, en_proceso, resuelto, cerrado")
    fecha_creacion: str = Field(description="Fecha de creación (YYYY-MM-DD)")
    fecha_resolucion: Optional[str] = Field(default=None, description="Fecha de resolución (YYYY-MM-DD)")


class CableCalderonDB(DB):
    """Base de datos del dominio CableHogar"""
    clientes: Dict[str, Cliente] = Field(default={}, description="Clientes indexados por cliente_id")
    planes: Dict[str, Plan] = Field(default={}, description="Planes indexados por plan_id")
    servicios: Dict[str, Servicio] = Field(default={}, description="Servicios indexados por servicio_id")
    ordenes: Dict[str, OrdenInstalacion] = Field(default={}, description="Órdenes indexadas por orden_id")
    reclamos: Dict[str, Reclamo] = Field(default={}, description="Reclamos indexados por reclamo_id")

    @classmethod
    def load(cls) -> "CableCalderonDB":
        return cls.model_validate_json(open(CABLE_CALDERON_DB_PATH).read())