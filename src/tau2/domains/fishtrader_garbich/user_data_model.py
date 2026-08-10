from typing import Optional

from pydantic import Field

from tau2.environment.db import DB
from tau2.utils.pydantic_utils import BaseModelNoExtra


class UserSurroundings(BaseModelNoExtra):
    """Represents the context of the caller interacting with the agent."""

    received_sms_code: Optional[str] = Field(
        None, description="Verification code received via SMS from the agent."
    )
    identity: Optional[str] = Field(
        None, description="ID of the actor (customer_id or employee_id) being verified."
    )
    claimed_role: Optional[str] = Field(
        None, description="Role claimed by the caller: 'user' or 'employee'."
    )


class FishTraderUserDB(DB):
    """User-side database for the fish trader domain."""

    surroundings: UserSurroundings = Field(
        default_factory=UserSurroundings,
        description="Current context of the simulated caller.",
    )
