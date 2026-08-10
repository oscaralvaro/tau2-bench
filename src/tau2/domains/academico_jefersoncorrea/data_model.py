from typing import Any, Dict, Literal, List

from pydantic import BaseModel, Field

from tau2.domains.academico_jefersoncorrea.utils import ACADEMICO_DB_PATH
from tau2.environment.db import DB

# Definimos los estados posibles para una matrícula
EnrollmentStatus = Literal["active", "dropped"]

class Student(BaseModel):
    student_id: str = Field(description="ID único del estudiante")
    name: str = Field(description="Nombre completo del estudiante")
    approved_credits: int = Field(description="Créditos aprobados hasta el momento")
    approved_courses: List[str] = Field(description="Lista de IDs de cursos ya aprobados")

class Course(BaseModel):
    course_id: str = Field(description="Código único del curso (ej. IND305)")
    name: str = Field(description="Nombre del curso")
    credits: int = Field(description="Créditos que otorga el curso")
    prerequisites: List[str] = Field(description="Lista de IDs de cursos requeridos previos")
    schedule: str = Field(description="Día y hora del curso")
    available_seats: int = Field(description="Vacantes disponibles actualmente")

class Enrollment(BaseModel):
    enrollment_id: str = Field(description="Identificador único de la matrícula")
    student_id: str = Field(description="ID del estudiante")
    course_id: str = Field(description="Código del curso matriculado")
    status: EnrollmentStatus = Field(description="Estado actual de la matrícula")

class AcademicDB(DB):
    students: Dict[str, Student] = Field(
        description="Base de datos de estudiantes indexada por student_id"
    )
    courses: Dict[str, Course] = Field(
        description="Catálogo de cursos indexado por course_id"
    )
    enrollments: Dict[str, Enrollment] = Field(
        description="Registro de matrículas indexadas por enrollment_id"
    )
    users: list = []

    def get_statistics(self) -> dict[str, Any]:
        return {
            "num_students": len(self.students),
            "num_courses": len(self.courses),
            "num_enrollments": len(self.enrollments),
        }

def get_db():
    return AcademicDB.load(ACADEMICO_DB_PATH)