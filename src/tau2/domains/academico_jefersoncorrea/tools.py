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
        student_id = student_id.lower() # Convertimos a minúsculas para evitar errores
        if student_id not in self.db.students:
            raise ValueError(f"Estudiante '{student_id}' no encontrado en la base de datos.")
        return self.db.students[student_id]

    def _get_course(self, course_id: str) -> Course:
        course_id = course_id.upper() # Convertimos a mayúsculas para evitar errores
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
            Un diccionario con los datos del estudiante y una lista de sus matrículas activas,
            incluyendo los horarios de dichas matrículas.
        """
        student = self._get_student(student_id)
        
        enriched_enrollments = []
        for enr in self.db.enrollments.values():
            if enr.student_id == student.student_id and enr.status == "active":
                enr_data = enr.model_dump()
                # Le damos al agente el horario directamente para evitar que asuma cosas
                course = self._get_course(enr.course_id)
                enr_data["course_name"] = course.name
                enr_data["schedule"] = course.schedule
                enriched_enrollments.append(enr_data)
        
        return {
            "student_info": student.model_dump(),
            "active_enrollments": enriched_enrollments
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
        
        IMPORTANTE SOBRE LA BÚSQUEDA:
        El campo 'query' SOLO busca coincidencias exactas en el NOMBRE del curso o el ID del curso.
        NUNCA envíes conceptos abstractos como "4 créditos", "3 o 5 créditos" o "Ingeniería Informática" 
        en el query, ya que la búsqueda fallará y devolverá vacío.
        
        Si necesitas filtrar por créditos, carreras, requisitos, etc:
        1. Llama a search_courses() con query="" (vacío) para obtener la lista COMPLETA de cursos.
        2. Revisa tú mismo esa lista completa devuelta y dile al usuario cuáles opciones 
           coinciden con lo que te está pidiendo.
        
        Args:
            query: (Opcional) Texto corto para filtrar por nombre del curso o ID. Si está vacío, devuelve todos.
            
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
            ValueError: Si no cumple prerrequisitos, no hay vacantes o si ya está matriculado.
        """
        student = self._get_student(student_id)
        course = self._get_course(course_id)

        # 🚨 VALIDACIÓN PRO: Verificación estricta de Prerrequisitos
        for prereq in course.prerequisites:
            if prereq not in student.approved_courses:
                raise ValueError(f"Matrícula rechazada: El estudiante no ha aprobado el prerrequisito estricto '{prereq}'.")
        # Validación de curso ya aprobado
        if course.course_id in student.approved_courses:
            raise ValueError(f"Matrícula rechazada: El estudiante ya tiene aprobado el curso '{course.course_id}' en su historial.")    

        # Validación de vacantes
        if course.available_seats <= 0:
            raise ValueError(f"Matrícula rechazada: El curso '{course.course_id}' no tiene vacantes.")

        # Validación de duplicados
        for enr in self.db.enrollments.values():
            if enr.student_id == student.student_id and enr.course_id == course.course_id and enr.status == "active":
                raise ValueError(f"Matrícula rechazada: El estudiante ya está en '{course.course_id}'.")

        enrollment_id = f"ENROLL-{student.student_id}-{course.course_id}"
        new_enrollment = Enrollment(
            enrollment_id=enrollment_id,
            student_id=student.student_id,
            course_id=course.course_id,
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
        
        REGLAS ANTES DE USAR:
        1. Debes verificar que cumpla los prerrequisitos del 'new_course_id'.
        2. Debes verificar que el 'new_course_id' tenga vacantes disponibles.
        3. Verifica cruces de horario: Debes asegurarte de que el 'new_course_id' NO se cruce 
           con el resto de las matrículas activas del estudiante. 
           NOTA: El horario del 'old_course_id' ya NO cuenta como cruce porque el estudiante 
           será retirado de ese curso durante este cambio.
        
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
            raise ValueError(f"Cambio rechazado: El nuevo curso '{new_course.course_id}' no tiene vacantes.")
            
        # 2. Retirar el curso antiguo (libera vacante)
        dropped_enrollment = self.cancel_enrollment(student_id, old_course_id)
        
        # 3. Matricular en el nuevo curso (resta vacante)
        new_enrollment = self.create_enrollment(student_id, new_course_id)
        
        return {
            "status": "success",
            "message": f"Cambio exitoso de {old_course_id.upper()} a {new_course.course_id}.",
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
        student = self._get_student(student_id)
        course = self._get_course(course_id)
        
        target_enrollment = None
        for enr in self.db.enrollments.values():
            if enr.student_id == student.student_id and enr.course_id == course.course_id and enr.status == "active":
                target_enrollment = enr
                break
                
        if not target_enrollment:
            raise ValueError(f"Cancelación rechazada: No hay matrícula activa en '{course.course_id}'.")

        target_enrollment.status = "dropped"
        course.available_seats += 1
        
        return target_enrollment