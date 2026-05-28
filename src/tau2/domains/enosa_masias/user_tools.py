from tau2.environment.toolkit import ToolKitBase, ToolType, is_tool
from tau2.domains.enosa_masias.data_model import EnosaDB

class EnosaUserToolKit(ToolKitBase):
    """Herramientas del usuario (cliente) para interactuar en ENOSA."""
    db: EnosaDB

    def __init__(self, db: EnosaDB) -> None:
        super().__init__(db)

    @is_tool(ToolType.READ)
    def read_sms_code(self) -> str:
        """Simula que el usuario lee un SMS en su celular."""
        return "123456"  