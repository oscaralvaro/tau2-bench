from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field
from tau2.environment.db import DB

ProblemaSalud = Literal["Cataratas", "Colelitiasis", "Vicios de Refraccion"]
EstadoInterconsulta = Literal[
    "En Espera",
    "Agendado",
    "Resuelto Externo",
    "Inubicable",
    "Enviada",
]
PrioridadInterconsulta = Literal["Normal", "Alta", "Urgente"]


class Paciente(BaseModel):
    rut: str = Field(description="RUT del paciente")
    nombre: str = Field(description="Nombre completo")
    prevision: str = Field(description="Fonasa o Isapre")
    comuna: str = Field(description="Comuna")
    telefono: Optional[str] = None


class Interconsulta(BaseModel):
    id: str = Field(description="ID de la interconsulta")
    rut_paciente: str = Field(description="RUT asociado")
    problema_salud: str = Field(description="Diagnostico")
    es_ges: bool = Field(default=True)
    dias_espera: int = Field(description="Dias esperando")
    estado: EstadoInterconsulta = Field(default="En Espera")
    prioridad: PrioridadInterconsulta = Field(default="Normal")
    codigo_medico_derivador: Optional[str] = None
    cesfam_origen: Optional[str] = None
    especialidad_destino: Optional[str] = None
    examenes_adjuntos: Optional[List[str]] = None
    notas_clinicas: Optional[str] = None


class CupoAgenda(BaseModel):
    id: str
    hospital: str
    fecha_hora: str
    especialidad: str


class MedicoAPS(BaseModel):
    """Medico de Atencion Primaria de Salud registrado en la red."""
    id: str = Field(description="Codigo del medico")
    nombre: str = Field(description="Nombre completo")
    cesfam: str = Field(description="CESFAM donde trabaja")
    comuna: str = Field(description="Comuna del CESFAM")
    especialidad: str = Field(description="Especialidad del medico")
    telefono: str = Field(description="Telefono de contacto")


class ProtocoloDerivacion(BaseModel):
    """Protocolo de derivacion clinica vigente para una especialidad y condicion."""
    id: str
    especialidad: str
    condicion: str
    nivel_derivacion: str
    criterios_inclusion: List[str]
    examenes_requeridos: List[str]
    contraindicaciones: List[str]
    tiempo_respuesta_garantizado_dias: int
    notas_adicionales: Optional[str] = None


class SaludDB(DB):
    pacientes: Dict[str, Paciente] = Field(default_factory=dict)
    interconsultas: Dict[str, Interconsulta] = Field(default_factory=dict)
    agenda_disponible: Dict[str, CupoAgenda] = Field(default_factory=dict)
    medicos_aps: Dict[str, MedicoAPS] = Field(default_factory=dict)
    protocolos_derivacion: Dict[str, ProtocoloDerivacion] = Field(default_factory=dict)
    sms_verification_codes: Dict[str, str] = Field(default_factory=dict)

    def get_user_by_id(self, user_id: str) -> Optional[Paciente]:
        return self.pacientes.get(user_id)