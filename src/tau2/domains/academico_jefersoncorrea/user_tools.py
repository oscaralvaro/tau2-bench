from tau2.domains.academico_jefersoncorrea.data_model import AcademicDB
from tau2.environment.toolkit import ToolKitBase, ToolType, is_tool


class AcademicUserTools(ToolKitBase):
    """Herramientas disponibles para el estudiante simulado."""

    db: AcademicDB

    def __init__(self, db: AcademicDB) -> None:
        super().__init__(db)

    @is_tool(ToolType.READ)
    def check_verification_sms(self, student_id: str) -> str:
        """
        Revisa la bandeja SMS y recupera el código de verificación.
        """
        student_id = student_id.lower()
        if student_id not in self.db.students:
            return "Error: Estudiante no encontrado."

        student = self.db.students[student_id]
        
        # LÓGICA INTELIGENTE:
        # Si el agente ya generó un código en la DB, lo usamos.
        # Si no hay código, devolvemos un mensaje claro para que el usuario no invente.
        if student.current_sms_code:
            return (
                "Tienes un nuevo mensaje SMS: "
                f"'Tu código de verificación de la Universidad es {student.current_sms_code}'."
            )
        
        return "No hay mensajes SMS nuevos. Por favor, solicita uno si es necesario."