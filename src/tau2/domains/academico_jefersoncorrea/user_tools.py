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
        Revisa la bandeja SMS del estudiante y recupera el código de verificación.

        Usa esta herramienta cuando el agente indique que envió un SMS o pida el
        código de 6 dígitos para continuar una operación sensible.

        Args:
            student_id: ID del estudiante que está realizando la solicitud.
        """
        student_id = student_id.lower()
        if student_id not in self.db.students:
            return "Error: Estudiante no encontrado."

        student = self.db.students[student_id]
        if student.current_sms_code:
            return (
                "Tienes un nuevo mensaje SMS: "
                f"'Tu código de verificación de la Universidad es {student.current_sms_code}'."
            )
        return "No hay mensajes SMS nuevos."

    @is_tool(ToolType.READ)
    def check_phone_messages(self, phone_number: str) -> str:
        """
        Revisa los mensajes SMS del teléfono registrado del estudiante.

        Args:
            phone_number: Número de teléfono registrado del estudiante.
        """
        for student in self.db.students.values():
            if student.phone_number == phone_number:
                if student.current_sms_code:
                    return (
                        "Tienes un nuevo mensaje SMS: "
                        f"'Tu código de verificación de la Universidad es {student.current_sms_code}'."
                    )
                return "No hay mensajes SMS nuevos."

        return "Error: Número de teléfono no encontrado o sin acceso."
