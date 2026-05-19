from tau2.environment.toolkit import is_tool, ToolType
from .environment import get_environment

@is_tool(ToolType.READ)
def check_phone_messages(phone_number: str) -> str:
    """
    Simula revisar los mensajes de texto del teléfono del usuario.
    Útil para recuperar códigos de verificación SMS.
    
    Args:
        phone_number: El número de teléfono a revisar.
    """
    env = get_environment()
    db = env.db
    
    # Buscamos al estudiante por su teléfono
    for student in db.students.values():
        if student.phone_number == phone_number:
            if student.current_sms_code:
                return f"Tienes un nuevo mensaje: 'Tu código de verificación de la Universidad es {student.current_sms_code}'"
            return "No hay mensajes nuevos."
            
    return "Error: Número de teléfono no encontrado o no tienes acceso a este dispositivo."