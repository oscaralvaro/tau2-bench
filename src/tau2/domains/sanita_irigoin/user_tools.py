from tau2.environment.toolkit import ToolKitBase, ToolType, is_tool
from tau2.domains.sanita_irigoin.data_model import ArrozDB


# Almacena los códigos SMS enviados por el agente
_sms_codes: dict = {}


class ArrozUserToolKit(ToolKitBase):
    """Herramientas del lado del usuario simulado."""
    db: ArrozDB

    def __init__(self, db: ArrozDB) -> None:
        super().__init__(db)

    @is_tool(ToolType.READ)
    def get_sms_code(self, user_id: str) -> dict:
        """
        Permite al usuario simulado obtener el código SMS que el agente
        le envió. Simula la recepción del código en el teléfono del usuario.
        Retorna el código si existe, o error si no se ha enviado ninguno.
        """
        code = _sms_codes.get(user_id)
        if not code:
            return {"error": f"No se encontró ningún código SMS para el usuario '{user_id}'."}
        return {"user_id": user_id, "codigo_sms": code}