from tau2.domains.salud_mendoza_lista.data_model import SaludDB
from tau2.environment.toolkit import ToolKitBase, ToolType, is_tool


class SaludUserToolkit(ToolKitBase):
    """
    Herramientas disponibles para el usuario simulado en el dominio salud_mendoza_lista.
    Permiten al usuario simulado recibir el codigo de verificacion SMS enviado por el agente.
    """

    def __init__(self, db: SaludDB):
        super().__init__(db)

    @is_tool(ToolType.READ)
    def get_sms_verification_code(self, rut: str) -> dict:
        """
        Permite al usuario simulado obtener el codigo de verificacion SMS que el agente
        le envio a su telefono. Simula la recepcion del mensaje de texto.
        Usar cuando el agente indique que envio un codigo SMS.

        Args:
            rut: RUT del paciente que esta esperando el codigo SMS.
        """
        codigo = self.db.sms_verification_codes.get(rut)
        if codigo is None:
            return {
                "exito": False,
                "mensaje": (
                    f"No se ha recibido ningun codigo SMS para el RUT {rut}. "
                    "Puede que el agente aun no lo haya enviado."
                ),
                "codigo": None,
            }
        return {
            "exito": True,
            "mensaje": "Codigo SMS recibido en tu telefono registrado.",
            "codigo": codigo,
        }