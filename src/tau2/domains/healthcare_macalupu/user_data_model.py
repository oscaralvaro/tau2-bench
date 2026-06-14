from typing import List

from pydantic import Field

from tau2.environment.db import DB


class HealthcareUserDB(DB):
    """Simple user-side DB for healthcare domain to store incoming SMS codes."""

    def __init__(self, sms_inbox: List[str]) -> None:
        self.sms_inbox = sms_inbox

    sms_inbox: List[str] = Field(
        default_factory=list, description="Received SMS messages"
    )
    used_sms: List[str] = Field(default_factory=list, description="Used SMS messages")
