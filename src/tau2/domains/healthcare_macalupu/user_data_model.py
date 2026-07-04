from typing import List

from pydantic import Field

from tau2.domains.healthcare_macalupu.auth_data_model import AuthCodeObserver
from tau2.environment.db import DB


class HealthcareUserDB(DB, AuthCodeObserver):
    """Simple user-side DB for healthcare domain to store incoming SMS codes."""

    sms_inbox: List[str] = Field(
        default_factory=list, description="Received SMS messages"
    )
    used_sms: List[str] = Field(default_factory=list, description="Used SMS messages")

    def update(self, new_code: str) -> None:
        self.sms_inbox.append(new_code)
