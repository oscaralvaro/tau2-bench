# src/tau2/domains/academico_jefersoncorrea/tools.py
from typing import List, Optional
import uuid

from tau2.domains.academico_jefersoncorrea.data_model import AcademicDB, Student, Course, Enrollment
from tau2.environment.toolkit import ToolKitBase, ToolType, is_tool

class AcademicTools(ToolKitBase):
    """
    Herramientas para el agente de Orientación Académica.
    Usa estas herramientas para consultar información del estudiante, buscar cursos disponibles, 
    y gestionar (crear, actualizar o cancelar) sus matrículas.
    """

    db: AcademicDB

    def __init__(self, db: AcademicDB) -> None:
        super().__init__(db)

    # --- Métodos Privados Auxiliares ---
    def _get_student(self, student_id: str) -> Student:
        if student_id not in self.db.students:
            raise ValueError(f"Estudiante '{student_id}' no encontrado en la base de datos.")
        return self.db.students[student_id]

    def _get_course(self, course_id: str) -> Course:
        if course_id not in self.db.courses:
            raise ValueError(f"Curso '{course_id}' no encontrado en el catálogo.")
        return self.db.courses[course_id]

    # ==========================================
    # 1. Herramienta: get_user_details (READ)
    # ==========================================
    @is_tool(ToolType.READ)
    def get_student_details(self, student_id: str) -> dict:
        """
        Obtiene los detalles de un estudiante (nombre, créditos y cursos ya aprobados) 
        junto con sus matrículas activas del semestre actual.
        
        Uso: SIEMPRE llama a esta herramienta al inicio de la conversación para verificar 
        la identidad del estudiante y saber qué cursos ya aprobó (prerrequisitos).
        
        Args:
            student_id: El ID único del estudiante (ejemplo: 'u2024001').
            
        Returns:
            Un diccionario con los datos del estudiante y una lista de sus matrículas activas.
        """
        student = self._get_student(student_id)
        active_enrollments = [
            enr for enr in self.db.enrollments.values()
            if enr.student_id == student_id and enr.status == "active"
        ]
        
        return {
            "student_info": student.model_dump(),
            "active_enrollments": [enr.model_dump() for enr in active_enrollments]
        }

    # ==========================================
    # 2. Herramienta: search_X (READ)
    # ==========================================
    @is_tool(ToolType.READ)
    def search_courses(self, query: str = "") -> List[Course]:
        """
        Busca cursos en el catálogo académico. Devuelve información vital como:
        créditos, prerrequisitos, horarios y VACANTES DISPONIBLES.
        
        Uso: Usa esta herramienta cuando el estudiante pregunte por cursos disponibles 
        o antes de matricularlo para verificar que el curso tenga vacantes y no cruce horario.
        
        Args:
            query: (Opcional) Texto para filtrar por nombre del curso o ID. Si está vacío, devuelve todos.
            
        Returns:
            Lista de cursos que coinciden con la búsqueda.
        """
        all_courses = list(self.db.courses.values())
        if not query:
            return all_courses
            
        query_lower = query.lower()
        return [
            course for course in all_courses 
            if query_lower in course.name.lower() or query_lower in course.course_id.lower()
        ]

    # ==========================================
    # 3. Herramienta: create_X (WRITE)
    # ==========================================
    @is_tool(ToolType.WRITE)
    def create_enrollment(self, student_id: str, course_id: str) -> Enrollment:
        """
        Matricula a un estudiante en un nuevo curso (crea una matrícula).
        
        REGLAS ANTES DE USAR:
        1. Debes haber verificado que el estudiante cumple los 'prerequisites'.
        2. Debes haber verificado que el curso tiene 'available_seats' > 0.
        3. Debes asegurarte de que el horario no se cruce con sus otras matrículas.
        
        Args:
            student_id: ID del estudiante.
            course_id: ID del curso a matricular (ej. 'IND305').
            
        Returns:
            El registro de la matrícula creada exitosamente.
            
        Raises:
            ValueError: Si no hay vacantes o si ya está matriculado.
        """
        student = self._get_student(student_id)
        course = self._get_course(course_id)

        if course.available_seats <= 0:
            raise ValueError(f"Matrícula rechazada: El curso '{course_id}' no tiene vacantes.")

        # Evitar duplicados
        for enr in self.db.enrollments.values():
            if enr.student_id == student_id and enr.course_id == course_id and enr.status == "active":
                raise ValueError(f"Matrícula rechazada: El estudiante ya está en '{course_id}'.")

        enrollment_id = f"ENROLL-{str(uuid.uuid4())[:8].upper()}"
        new_enrollment = Enrollment(
            enrollment_id=enrollment_id,
            student_id=student_id,
            course_id=course_id,
            status="active"
        )

        self.db.enrollments[enrollment_id] = new_enrollment
        course.available_seats -= 1
        
        return new_enrollment

    # ==========================================
    # 4. Herramienta: update_X (WRITE)
    # ==========================================
    @is_tool(ToolType.WRITE)
    def update_enrollment_swap(self, student_id: str, old_course_id: str, new_course_id: str) -> dict:
        """
        Actualiza la matrícula cambiando (swapping) un curso por otro. 
        Retira al estudiante del 'old_course_id' y lo matricula en el 'new_course_id' en una sola acción.
        
        Uso: Cuando el estudiante pide cambiar de curso.
        
        Args:
            student_id: ID del estudiante.
            old_course_id: ID del curso del que se va a retirar.
            new_course_id: ID del nuevo curso al que desea ingresar.
            
        Returns:
            Un mensaje de confirmación y los detalles de la nueva matrícula.
            
        Raises:
            ValueError: Si el nuevo curso no tiene vacantes o el estudiante no está en el curso antiguo.
        """
        # 1. Validar que el nuevo curso exista y tenga vacantes
        new_course = self._get_course(new_course_id)
        if new_course.available_seats <= 0:
            raise ValueError(f"Cambio rechazado: El nuevo curso '{new_course_id}' no tiene vacantes.")
            
        # 2. Retirar el curso antiguo (libera vacante)
        dropped_enrollment = self.cancel_enrollment(student_id, old_course_id)
        
        # 3. Matricular en el nuevo curso (resta vacante)
        new_enrollment = self.create_enrollment(student_id, new_course_id)
        
        return {
            "status": "success",
            "message": f"Cambio exitoso de {old_course_id} a {new_course_id}.",
            "new_enrollment": new_enrollment.model_dump()
        }

    # ==========================================
    # 5. Herramienta: cancel_X (WRITE)
    # ==========================================
    @is_tool(ToolType.WRITE)
    def cancel_enrollment(self, student_id: str, course_id: str) -> Enrollment:
        """
        Cancela la matrícula de un estudiante en un curso específico y libera la vacante.
        
        Uso: Cuando el estudiante solicita explícitamente retirarse de un curso.
        
        Args:
            student_id: ID del estudiante.
            course_id: ID del curso a cancelar.
            
        Returns:
            El registro de la matrícula con estado 'dropped'.
            
        Raises:
            ValueError: Si no se encuentra una matrícula activa para ese curso.
        """
        target_enrollment = None
        for enr in self.db.enrollments.values():
            if enr.student_id == student_id and enr.course_id == course_id and enr.status == "active":
                target_enrollment = enr
                break
                
        if not target_enrollment:
            raise ValueError(f"Cancelación rechazada: No hay matrícula activa en '{course_id}'.")

        target_enrollment.status = "dropped"
        course = self._get_course(course_id)
        course.available_seats += 1
        
        return target_enrollment