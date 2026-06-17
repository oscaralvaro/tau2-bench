from typing import Dict, Literal, Optional

from pydantic import Field

from tau2.environment.db import DB
from tau2.utils.pydantic_utils import BaseModelNoExtra

ProblemaSalud = Literal["Cataratas", "Colelitiasis", "Vicios de Refraccion"]
EstadoInterconsulta = Literal[
    "En Espera",
    "Agendado",
    "Resuelto Externo",
    "Inubicable",
]
PrioridadInterconsulta = Literal["Normal", "Alta", "Urgente"]

DiagnosticoRAG = Literal[
    "Retinopatia Diabetica",
    "UAPO y Teleoftalmologia",
    "Trauma Ocular Complejo",
    "Sospecha de Tumor Ocular",
]
EstadoSolicitud = Literal[
    "Pendiente Revision",
    "Observada",
    "Lista para Derivacion",
    "Derivar a Urgencias",
]


class Usuario(BaseModelNoExtra):
    id: str
    nombre: str
    rol: str


class Paciente(BaseModelNoExtra):
    rut: str = Field(description="RUT del paciente")
    nombre: str = Field(description="Nombre completo")
    prevision: str = Field(description="Fonasa o Isapre")
    comuna: str = Field(description="Comuna")
    telefono: Optional[str] = None


class Interconsulta(BaseModelNoExtra):
    id: str = Field(description="ID de la interconsulta")
    rut_paciente: str = Field(description="RUT asociado")
    problema_salud: ProblemaSalud = Field(description="Diagnostico")
    es_ges: bool = Field(default=True)
    dias_espera: int = Field(description="Dias esperando")
    estado: EstadoInterconsulta = Field(default="En Espera")
    prioridad: PrioridadInterconsulta = Field(default="Normal")


class CupoAgenda(BaseModelNoExtra):
    id: str
    hospital: str
    fecha_hora: str
    especialidad: str


class ProtocoloRAG(BaseModelNoExtra):
    id: str
    diagnostico: DiagnosticoRAG
    examenes_obligatorios: list[str] = Field(default_factory=list)
    examenes_sugeridos: list[str] = Field(default_factory=list)
    signos_alarma: list[str] = Field(default_factory=list)
    ruta_asistencial: str
    plazo_referencia: Optional[str] = None


class SolicitudInterconsulta(BaseModelNoExtra):
    id: str
    rut_paciente: str
    diagnostico_sospecha: DiagnosticoRAG
    examenes_presentados: list[str] = Field(default_factory=list)
    sintomas_alerta: list[str] = Field(default_factory=list)
    estado_revision: EstadoSolicitud = Field(default="Pendiente Revision")
    observaciones: Optional[str] = None


class SaludMendozaDB(DB):
    users: Dict[str, Usuario] = Field(default_factory=dict)
    pacientes: Dict[str, Paciente] = Field(default_factory=dict)
    interconsultas: Dict[str, Interconsulta] = Field(default_factory=dict)
    agenda_disponible: Dict[str, CupoAgenda] = Field(default_factory=dict)
    protocolos_rag: Dict[str, ProtocoloRAG] = Field(default_factory=dict)
    solicitudes_interconsulta: Dict[str, SolicitudInterconsulta] = Field(
        default_factory=dict
    )

    def get_user_by_id(self, user_id: str) -> Optional[Paciente]:
        return self.pacientes.get(user_id)
