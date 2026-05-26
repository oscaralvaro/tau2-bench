from tau2.domains.fishtrader_garbich.user_data_model import FishTraderUserDB
from tau2.environment.toolkit import ToolKitBase, ToolType, is_tool


class FishTraderUserTools(ToolKitBase):
    """User-side tools for the fish trader domain."""

    db: FishTraderUserDB

    def __init__(self, db: FishTraderUserDB) -> None:
        super().__init__(db)

    @is_tool(ToolType.READ)
    def check_sms(self) -> str:
        """
        Check your SMS inbox for a verification code sent by the agent.
        Returns the code if one has been received, or a message indicating no code is available.
        """
        code = self.db.surroundings.received_sms_code
        if code is None:
            return "No verification code has been received yet."
        return f"You have received an SMS verification code: {code}"
