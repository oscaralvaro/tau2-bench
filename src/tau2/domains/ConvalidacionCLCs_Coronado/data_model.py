from typing import Any, Dict, List, Literal, TypeAlias

from pydantic import BaseModel, Field

from tau2.domains.ConvalidacionCLCs_Coronado.utils import CONVALIDACION_DB_PATH
from tau2.environment.db import DB

ProgramaAcademico: TypeAlias = Literal["IIS", "IME", "IC", "ARQ"]
EstadoSolicitud: TypeAlias = Literal["APPROVED", "DENIED", "IN PROCESS"]


class Estudiante(BaseModel):
    carnet: str = Field(description="Numero de carnet del estudiante")
    nombre_completo: str = Field(description="Nombre completo del estudiante")
    programa: ProgramaAcademico = Field(description="Programa academico")
    clcs_validados: List[int] = Field(
        description="Lista de CLCs ya validados",
        default_factory=list,
    )


class HorasCertificado(BaseModel):
    carnet: str = Field(description="Numero de carnet del estudiante")
    actividad: str = Field(description="Nombre de la actividad")
    horas_pdf: int = Field(description="Horas registradas en el certificado PDF")


class PagoDerechoAcademico(BaseModel):
    carnet: str = Field(description="Numero de carnet del estudiante")
    actividad: str = Field(description="Nombre de la actividad")
    pagado: bool = Field(description="Estado del pago academico")


class Solicitud(BaseModel):
    request_id: str = Field(description="Identificador unico de la solicitud")
    carnet: str = Field(description="Numero de carnet del estudiante")
    nombre_completo: str = Field(description="Nombre completo del estudiante")
    programa: ProgramaAcademico = Field(description="Programa academico")
    actividad: str = Field(description="Nombre de la actividad")
    evaluado_con_nota: bool = Field(description="Indica si la actividad fue evaluada")
    clc: int = Field(description="CLC solicitado")
    archivo: str = Field(description="Nombre del archivo PDF")
    horas_declaradas: int = Field(description="Horas declaradas por el estudiante")
    status: EstadoSolicitud = Field(description="Estado de la solicitud")


class ConvalidacionCLCDB(DB):
    """Base de datos para el dominio de convalidacion de CLCs."""

    estudiantes: List[Estudiante] = Field(description="Lista de estudiantes")
    congresos_preaprobados: Dict[str, List[str]] = Field(
        description="Congresos preaprobados por programa"
    )
    bienales_arquitectura: List[str] = Field(
        description="Bienales preaprobadas para Arquitectura"
    )
    horas_certificados: List[HorasCertificado] = Field(
        description="Horas registradas en certificados PDF por actividad",
        default_factory=list,
    )
    pagos_derecho_academico: List[PagoDerechoAcademico] = Field(
        description="Pagos de derecho academico registrados"
    )
    solicitudes: List[Solicitud] = Field(
        description="Solicitudes de convalidacion",
        default_factory=list,
    )

    def get_statistics(self) -> dict[str, Any]:
        """Obtiene estadisticas simples de la base del dominio."""
        return {
            "num_estudiantes": len(self.estudiantes),
            "num_pagos": len(self.pagos_derecho_academico),
            "num_solicitudes": len(self.solicitudes),
        }


def get_db() -> ConvalidacionCLCDB:
    return ConvalidacionCLCDB.load(CONVALIDACION_DB_PATH)


if __name__ == "__main__":
    db = get_db()
    print(db.get_statistics())
