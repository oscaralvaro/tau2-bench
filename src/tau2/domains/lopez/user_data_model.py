from pydantic import BaseModel, Field

from tau2.environment.db import DB


class SMSInboxMessage(BaseModel):
    id: str = Field(description="Identificador del mensaje SMS")
    cliente_id: str = Field(description="Cliente al que pertenece el SMS")
    telefono: str = Field(description="Telefono de destino")
    rol_requerido: str = Field(description="Rol que el agente desea validar")
    codigo: str = Field(description="Codigo numerico recibido")
    leido: bool = Field(description="Indica si el usuario ya reviso el SMS")


class LopezUserDB(DB):
    cliente_actual_id: str | None = Field(
        default=None, description="Cliente activo del usuario simulado"
    )
    sms_inbox: list[SMSInboxMessage] = Field(
        default_factory=list, description="Bandeja de SMS del usuario"
    )
