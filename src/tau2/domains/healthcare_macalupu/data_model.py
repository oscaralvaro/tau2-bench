from enum import Enum
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from tau2.domains.healthcare_macalupu.utils import HEALTHCARE_DB_PATH
from tau2.environment.db import DB


class ReferralRequestStatus(int, Enum):
    BORRADOR = 0
    ENVIADA = 1
    PENDIENTE_DE_CITACION = 2
    CITADA = 3
    DEVUELTA = 4
    NO_PERTINENTE = 5
    ATENDIDA = 6
    ANULADA = 7


Priority = Literal["P1", "P2"]


class Specialty(str, Enum):
    OFTALMOLOGIA = "OFTA"
    OTORRINOLARINGOLOGIA = "OTOR"
    MEDICINA_INTERNA = "MEIN"


class ReferralRequest(BaseModel):
    """Solicitud de Interconsulta."""

    sic_id: str = Field(description="Unique identifier for the referral request")
    patient_run: str = Field(description="Patient's RUN (national ID)")
    doctor_run: str = Field(description="Requesting doctor's RUT")
    specialty: Specialty = Field(description="Target medical specialty")
    cie10_code: str = Field(description="CIE-10 diagnosis code")
    cie10_description: str = Field(description="CIE-10 diagnosis description")
    reason: str = Field(description="Clinical reason for referral")
    priority: Priority = Field(
        description="Priority level: P1 (urgent) or P2 (non-urgent)"
    )
    attached_exams: List[str] = Field(description="List of attached exam's identifiers")
    status: ReferralRequestStatus = Field(
        description="Current status of the referral request"
    )
    is_ges: bool = Field(
        description="Whether the condition is covered by GES guarantee"
    )
    created_date: str = Field(description="Creation date in YYYY-MM-DD format")
    appointment_date: Optional[str] = Field(
        None, description="Appointment date in YYYY-MM-DD HH:MM format, if assigned"
    )
    appointment_location: Optional[str] = Field(
        None, description="Name of the establishment where the appointment is scheduled"
    )


class UserRole(str, Enum):
    PATIENT = "Patient"
    DOCTOR = "Doctor"


class User(BaseModel):
    """User registered in the system."""

    run: str = Field(description="User's RUN in XXXXXXXX-X format")
    name: str = Field(description="User's full name")
    birth_date: str = Field(description="User's birth date in YYYY-MM-DD format")
    cesfam: str = Field(description="CESFAM where the user is belongs")
    role: UserRole = Field(description="User's role in the system")
    phone: str = Field(description="User's phone number in +569XXXXXXXX format")


class Analysis(BaseModel):
    """Analysis of a patient's referral request."""

    id: str = Field(description="Analysis ID")
    description: str = Field(description="Analysis description")
    patient_run: str = Field(description="Patient's RUN (unique national identifier)")
    details: Optional[str] = Field(description="Analysis details")


class HealthcareDB(DB):
    """Database for the Chilean health referral agent."""

    users: Dict[str, User] = Field(description="Dictionary of users indexed by RUN")

    requests: Dict[str, ReferralRequest] = Field(
        description="Dictionary of referral requests indexed by SIC ID"
    )

    requests_by_run: Dict[str, list[str]] = Field(
        description="Dictionary of referral requests indexed by RUN"
    )

    analyses: Dict[str, Analysis] = Field(
        description="Dictionary of analyses indexed by analysis ID"
    )
