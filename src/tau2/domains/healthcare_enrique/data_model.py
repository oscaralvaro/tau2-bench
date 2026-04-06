from pydantic import BaseModel
from typing import Dict, List, Optional
from tau2.environment.db import DB


# -------------------------
# PACIENTE (Ficha Maestro)
# -------------------------

class Paciente(BaseModel):
    rut: str
    nombre: str
    edad: int
    sexo: str
    prevision: str  # FONASA / ISAPRE

    # Modelo ECICEP
    clasificacion_riesgo: str  # G1, G2, G3
    riesgo_cardiovascular: str  # Bajo, Moderado, Alto, Muy Alto
    estado_pscv: str  # Activo / Inactivo

    cesfam: str
    inscrito: bool


# -------------------------
# PROFESIONAL DE SALUD
# -------------------------

class ProfesionalSalud(BaseModel):
    id_sis: str
    nombre: str
    rol: str  # medico, enfermero, nutricionista, etc.
    certificacion_pa: bool
    sector: str


# -------------------------
# REGISTRO CLINICO (EXAMENES / BIOMETRIA)
# -------------------------

class RegistroClinico(BaseModel):
    id: str
    rut_paciente: str

    tipo: str  # laboratorio, biometria, oftalmologico
    parametro: str  # HbA1c, PA, IMC, etc.

    valor: str
    unidad: str
    fecha: str


# -------------------------
# INTERCONSULTA (SIC)
# -------------------------

class Interconsulta(BaseModel):
    id: str
    rut_paciente: str

    especialidad_destino: str
    criterio_derivacion: str

    estado: str  # borrador, validada, pendiente_examenes, enviada
    prioridad: Optional[str] = None  # C1, C2, C3
    fecha_creacion: str


# -------------------------
# BLOQUE DE AGENDA (CASO 2)
# -------------------------

class BloqueAgenda(BaseModel):
    id: str
    tipo_prestacion: str  # control_integral, ingreso, rescate

    profesionales: List[str]  # IDs de profesionales
    duracion: int  # minutos

    estado_cupo: str  # disponible, reservado, confirmado, inasistencia


# -------------------------
# BASE DE DATOS
# -------------------------

class HealthcareDB(DB):
    pacientes: Dict[str, Paciente] = {}
    profesionales: Dict[str, ProfesionalSalud] = {}
    registros_clinicos: Dict[str, RegistroClinico] = {}
    interconsultas: Dict[str, Interconsulta] = {}
    bloques_agenda: Dict[str, BloqueAgenda] = {}