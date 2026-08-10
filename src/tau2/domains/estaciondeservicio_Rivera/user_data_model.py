import datetime
from typing import Dict

from pydantic import Field

from tau2.domains.estaciondeservicio_Rivera.data_model import SMSRole
from tau2.environment.db import DB
from tau2.utils.pydantic_utils import BaseModelNoExtra


class RiveraUserSession(BaseModelNoExtra):
    """Represents the simulated user identity in the conversation."""

    customer_id: str | None = Field(
        default=None,
        description="Customer identifier associated with the current user",
    )
    user_id: str | None = Field(
        default=None,
        description="Specific user identifier associated with the conversation, if any",
    )
    role: SMSRole = Field(
        default="customer_contact",
        description="Role used by the simulated user for SMS verification",
    )
    telefono: str | None = Field(
        default=None,
        description="Phone number available to the simulated user",
    )
    nombre: str | None = Field(
        default=None,
        description="Display name of the simulated user",
    )


class SMSInboxMessage(BaseModelNoExtra):
    """Represents an SMS message delivered to the user inbox."""

    verification_id: str = Field(description="Verification identifier")
    customer_id: str = Field(description="Customer identifier associated with the SMS")
    role: SMSRole = Field(description="Role that must validate the SMS")
    user_id: str | None = Field(
        default=None,
        description="Target user identifier when applicable",
    )
    phone: str = Field(description="Phone number that received the SMS")
    code: str = Field(description="Verification code delivered by SMS")
    reason: str | None = Field(
        default=None,
        description="Reason for the SMS verification",
    )
    sent_at: datetime.datetime = Field(
        description="Date and time when the SMS was delivered"
    )
    consumed: bool = Field(
        default=False,
        description="Whether the simulated user has already checked this SMS",
    )


class RiveraUserDB(DB):
    """User-side database for the SMS verification flow."""

    session: RiveraUserSession = Field(
        default_factory=RiveraUserSession,
        description="Current simulated user identity",
    )
    sms_inbox: Dict[str, SMSInboxMessage] = Field(
        default_factory=dict,
        description="Inbox of SMS verification messages indexed by verification_id",
    )
