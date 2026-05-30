from tau2.environment.toolkit import ToolKitBase, is_tool, ToolType
from .user_data_model import HealthcareUserDB


class HealthcareUserTools(ToolKitBase):

    def __init__(self, db: HealthcareUserDB):
        self.db = db

    @is_tool(ToolType.READ)
    def leer_codigo_sms(self):
        """Obtiene el último código SMS recibido"""
        return self.db.sms_code