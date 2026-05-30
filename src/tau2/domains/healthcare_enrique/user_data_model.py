from pydantic import Field
from tau2.environment.db import DB


class HealthcareUserDB(DB):
    sms_code: str | None = Field(
        default=None,
        description="Último código SMS recibido por el usuario"
    )