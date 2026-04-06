from typing import Dict, Literal, Optional

from pydantic import BaseModel, Field
from tau2.environment.db import DB

ProblemaSalud = Literal["Cataratas", "Colelitiasis", "Vicios de Refraccion"]
EstadoInterconsulta = Literal[
    "En Espera",
    "Agendado",
    "Resuelto Externo",
    "Inubicable",
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
    problema_salud: ProblemaSalud = Field(description="Diagnostico")
    es_ges: bool = Field(default=True)
    dias_espera: int = Field(description="Dias esperando")
    estado: EstadoInterconsulta = Field(default="En Espera")
    prioridad: PrioridadInterconsulta = Field(default="Normal")

class CupoAgenda(BaseModel):
    id: str
    hospital: str
    fecha_hora: str
    especialidad: str

class SaludDB(DB):
    pacientes: Dict[str, Paciente] = Field(default_factory=dict)
    interconsultas: Dict[str, Interconsulta] = Field(default_factory=dict)
    agenda_disponible: Dict[str, CupoAgenda] = Field(default_factory=dict)

    def get_user_by_id(self, user_id: str) -> Optional[Paciente]:
        return self.pacientes.get(user_id)
