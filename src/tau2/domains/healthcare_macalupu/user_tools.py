from tau2.domains.healthcare_macalupu.user_data_model import HealthcareUserDB
from tau2.environment.toolkit import ToolKitBase, ToolType, is_tool


class HealthcareUserTools(ToolKitBase):
    """User tools to simulate user-side actions like receiving SMS codes."""

    db: HealthcareUserDB

    def __init__(self, db: HealthcareUserDB):
        super().__init__(db)

    @is_tool(ToolType.READ)
    def receive_sms(self) -> str:
        """Receive the SMS code from the inbox, if any."""
        if len(self.db.sms_inbox) == 0:
            return "La bandeja de entrada está vacía"
        code = self.db.sms_inbox[-1]

        if code in self.db.used_sms:
            return "No hay nuevos SMS en la bandeja de entrada"

        return code

    @is_tool(ToolType.WRITE)
    def mark_sms_as_used(self, code: str) -> None:
        """Mark the given SMS code as used."""
        self.db.used_sms.append(code)
