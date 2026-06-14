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
        Revisa la bandeja SMS y recupera la clave dinamica real.

        Usa esta herramienta SOLO si tus instrucciones de escenario te permiten
        leer el SMS real. Si tus instrucciones dicen que debes proporcionar una
        clave incorrecta, una clave de emergencia, o que no debes leer el SMS,
        NO llames esta herramienta: responde en texto con la clave indicada por
        tu escenario.
        """
        student_id = student_id.lower()
        if student_id not in self.db.students:
            return "Error: Estudiante no encontrado."

        student = self.db.students[student_id]

        # If the agent generated a key in the DB, expose it to the simulated user.
        # If there is no key, return a clear message so the user does not invent it.
        if student.current_sms_code:
            return (
                "Tienes un nuevo mensaje SMS: "
                f"'Tu clave dinamica de la Universidad es {student.current_sms_code}'."
            )

        return "No hay mensajes SMS nuevos. Por favor, solicita uno si es necesario."
