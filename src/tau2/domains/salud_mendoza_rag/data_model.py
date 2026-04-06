from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field
from tau2.environment.db import DB

# Tipos fijos para validación estricta
EstadoSolicitud = Literal["Borrador", "Validada", "Rechazada por Protocolo"]
DiagnosticoRCR = Literal["Glaucoma", "Cataratas", "Colelitiasis", "Vicios de Refraccion"]

class Examen(BaseModel):
    nombre: str
    obligatorio: bool = True

class ProtocoloRAG(BaseModel):
    id: str
    diagnostico: DiagnosticoRCR
    especialidad: str
    examenes_requeridos: List[Examen]
    link_referencia: str

class SolicitudInterconsulta(BaseModel):
    id: str
    rut_paciente: str
    diagnostico_sospecha: DiagnosticoRCR
    examenes_adjuntos: List[str] = Field(default_factory=list)
    estado: EstadoSolicitud = "Borrador"

class SaludMendozaRAGDB(DB):
    protocolos: Dict[str, ProtocoloRAG] = Field(default_factory=dict)
    solicitudes: Dict[str, SolicitudInterconsulta] = Field(default_factory=dict)

    def get_user_by_id(self, user_id: str) -> Optional[dict]:
        # El usuario aquí es el Médico de APS
        return {"id": user_id, "rol": "Medico_APS"}
