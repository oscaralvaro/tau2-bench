"""Herramientas disponibles para el usuario simulado en el dominio ConvalidacionCLCs."""

from tau2.environment.toolkit import ToolKitBase, ToolType, is_tool


class ConvalidacionCLCUserTools(ToolKitBase):
    """Herramientas del lado del usuario simulado para convalidacion de CLCs.

    Recibe una referencia al mismo diccionario _sms_codes que usa ConvalidacionCLCTools,
    lo que permite al usuario simulado recuperar el codigo SMS que el agente envio.
    El rol 'user' es el unico que tiene acceso a receive_sms_code(), garantizando
    que el agente no puede obtener el codigo por esta via.
    """

    def __init__(self, sms_codes: dict) -> None:
        super().__init__(None)
        self._sms_codes = sms_codes

    @is_tool(ToolType.READ)
    def receive_sms_code(self) -> str:
        """Obtener el ultimo codigo SMS de verificacion enviado al usuario simulado.

        Usa esta herramienta cuando el agente te pida que proporciones el codigo
        de verificacion que recibiste por SMS. Retorna el codigo tal como fue enviado.
        """
        if not self._sms_codes:
            return "No hay codigo SMS disponible todavia. El agente aun no ha enviado un codigo."
        return list(self._sms_codes.values())[-1]
