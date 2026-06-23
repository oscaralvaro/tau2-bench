from datetime import date
from typing import Optional

from tau2.domains.healthcare_macalupu.auth_data_model import AuthCodeService
from tau2.domains.healthcare_macalupu.data_model import (
    Analysis,
    HealthcareDB,
    Priority,
    ReferralRequest,
    ReferralRequestStatus,
    Specialty,
    User,
    UserRole,
)
from tau2.environment.toolkit import ChromaPolicyIndex, RAGToolKit, ToolType, is_tool

# States from which a SIC can be cancelled
_CANCELLABLE_STATES: set[ReferralRequestStatus] = {
    ReferralRequestStatus.BORRADOR,
    ReferralRequestStatus.ENVIADA,
    ReferralRequestStatus.PENDIENTE_DE_CITACION,
}

_SENT_STATES: set[ReferralRequestStatus] = {
    ReferralRequestStatus.ENVIADA,
    ReferralRequestStatus.PENDIENTE_DE_CITACION,
    ReferralRequestStatus.CITADA,
}


class HealthcareTools(RAGToolKit):
    """Tools for the Healthcare (Chilean health referral) domain."""

    db: HealthcareDB
    auth_service: AuthCodeService

    def __init__(
        self,
        db: HealthcareDB,
        auth_service: AuthCodeService,
        policy_index: Optional[ChromaPolicyIndex] = None,
        retrieval_k: int = 3,
    ) -> None:
        super().__init__(db, policy_index, retrieval_k)
        self.auth_service = auth_service

    def _verify_valid_run(self, run: str) -> None:
        """
        Verify that the given RUN is valid
            Format: 12345678-N or 123456789-N
            Where: N can be "K" or 0..9
        """

        # Basic type/length guard to avoid indexing errors
        if not isinstance(run, str):
            raise ValueError("El RUN ingresado es inválido.")

        valid_length = len(run) in [9, 10]

        # Only attempt indexing/slicing when the length is acceptable
        valid_sufix = False
        valid_content = False
        if valid_length:
            valid_sufix = run[-2] == "-" and (run[-1] == "K" or run[-1].isdigit())
            valid_content = run[:-2].isdigit()

        if not (valid_length and valid_sufix and valid_content):
            raise ValueError("El RUN ingresado es inválido.")

    def _get_user_or_raise(self, run: str, expected_role: Optional[UserRole] = None):
        """Return user for run if exists and optionally matches expected_role, else raise ValueError.

        Args:
            run: RUN to lookup
            expected_role: if provided, ensure user's role matches this

        Returns:
            User instance
        """
        # Validate basic format first
        self._verify_valid_run(run)

        if run not in self.db.users:
            if expected_role is None:
                raise ValueError(f"No se encontró ningún usuario con RUN {run}.")
            role_name = "médico" if expected_role == UserRole.DOCTOR else "paciente"
            raise ValueError(f"No se encontró ningún {role_name} con RUN {run}.")

        user = self.db.users[run]
        if expected_role is not None and user.role != expected_role:
            role_name = "médico" if expected_role == UserRole.DOCTOR else "paciente"
            raise ValueError(f"No se encontró ningún {role_name} con RUN {run}.")

        return user

    def _verify_valid_phone(self, phone: str) -> None:
        """
        Verify that the given phone number is valid
            Format: +569XXXXXXXX
        """

        if not isinstance(phone, str):
            raise ValueError("El número de teléfono ingresado es inválido.")

        valid_length = len(phone) == 12

        # Safe checks with length guards
        valid_country_prefix = phone.startswith("+56") if len(phone) >= 3 else False
        valid_mobile_number = (
            phone[3] == "9" if len(phone) >= 4 else False
        )  # Verifica que sea movil
        valid_content = phone[3:].isdigit() if len(phone) >= 4 else False

        if not (
            valid_length
            and valid_country_prefix
            and valid_mobile_number
            and valid_content
        ):
            raise ValueError("El número de teléfono ingresado es inválido.")

    # -------------------------------------------------------------------------
    # GENERIC tools
    # -------------------------------------------------------------------------

    @is_tool(ToolType.GENERIC)
    def send_auth_sms(self, run: str, phone: str) -> str:
        """Simulate sending an authentication code SMS to a patient's RUN."""

        phone = phone.replace(" ", "")

        self._verify_valid_phone(phone)
        # Use helper to ensure user exists
        try:
            user = self._get_user_or_raise(run)
        except ValueError:
            # Do not reveal existence information — behave as if SMS was sent
            return "SMS de autenticación enviado."

        # Unicamente genera el código si el teléfono coincide.
        if user.phone == phone:
            self.auth_service.generate_code(run)

        return "SMS de autenticación enviado."

    # -------------------------------------------------------------------------
    # READ tools
    # -------------------------------------------------------------------------

    @is_tool(ToolType.READ)
    def authenticate_user(self, run: str, code: str) -> User:
        """Verify the authentication code for a given RUN."""

        # Ensure run is valid and user exists
        user = self._get_user_or_raise(run)

        if self.auth_service.verify_code(run, code):
            self.auth_service.remove_code_by_run(run)
            return user
        else:
            raise ValueError("RUN o código incorrecto.")

    @is_tool(ToolType.READ)
    def get_request(self, sic_id: str) -> ReferralRequest:
        """
        Retrieve a specific referral request (SIC) by its ID.

        Args:
            sic_id: The SIC identifier (e.g. 'SIC-001').

        Returns:
            The full SIC record.

        Raises:
            ValueError: If no SIC with that ID is found.
        """
        try:
            return self.db.requests[sic_id]
        except KeyError:
            raise ValueError(f"No se encontró ninguna interconsulta con ID {sic_id}.")

    @is_tool(ToolType.READ)
    def get_requests_by_run(self, run: str) -> list[ReferralRequest]:
        """
        Retrieve all referral requests (SICs) associated with a patient.
        The agent is responsible for verifying that the caller has permission to access this patient's data before invoking this tool.

        Args:
            run: The patient's RUN.

        Returns:
            A list of SIC records for the patient (may be empty).

        Raises:
            ValueError: If no patient with that RUN is found.
        """

        # Ensure run exists
        self._get_user_or_raise(run)
        request_ids = self.db.requests_by_run.get(run, [])
        return [
            self.db.requests[req_id]
            for req_id in request_ids
            if req_id in self.db.requests
        ]

    @is_tool(ToolType.READ)
    def get_analysis(self, id: str) -> Analysis:
        """
        Retrieve an analysis by its ID.

        Args:
            id: The analysis ID.

        Returns:
            The analysis record.

        Raises:
            ValueError: If no analysis with that ID is found.
        """
        if id not in self.db.analyses:
            raise ValueError(f"No se encontró ningún análisis con ID {id}.")
        return self.db.analyses[id]

    # -------------------------------------------------------------------------
    # WRITE tools
    # -------------------------------------------------------------------------

    @is_tool(ToolType.WRITE)
    def create_request(
        self,
        doctor_run: str,
        patient_run: str,
        specialty: Specialty,
        cie10_code: str,
        cie10_description: str,
        reason: str,
        priority: Priority,
        attached_exams: list[str],
        is_ges: bool,
    ) -> ReferralRequest:
        """
        Create a new referral request (SIC) in 'borrador' (draft) state.
        The agent must verify all clinical and administrative criteria
        (required exams, GES flag, CESFAM match) BEFORE calling this tool.
        This tool does NOT validate clinical criteria.

        Args:
            doctor_run: RUN of the requesting doctor.
            patient_run: RUN of the patient being referred.
            specialty: Target medical specialty.
            cie10_code: CIE-10 diagnosis code (e.g. 'H26.9').
            cie10_description: Human-readable CIE-10 description.
            reason: Clinical justification for the referral.
            priority: 'P1' for urgent, 'P2' for non-urgent.
            attached_exams: List of exam's identifiers confirmed as attached.
            is_ges: True if the condition has a GES/AUGE guarantee.

        Returns:
            The newly created SIC in 'borrador' state.

        Raises:
            ValueError: If the doctor or patient is not found.
        """
        self._verify_valid_run(doctor_run)
        self._verify_valid_run(patient_run)

        # Ensure doctor and patient exist and have correct roles
        self._get_user_or_raise(doctor_run, UserRole.DOCTOR)
        self._get_user_or_raise(patient_run, UserRole.PATIENT)

        sic_id = f"SIC-{len(self.db.requests) + 1:03d}"

        sic = ReferralRequest(
            sic_id=sic_id,
            patient_run=patient_run,
            doctor_run=doctor_run,
            specialty=specialty,
            cie10_code=cie10_code,
            cie10_description=cie10_description,
            reason=reason,
            priority=priority,
            attached_exams=attached_exams,
            status=ReferralRequestStatus.BORRADOR,
            is_ges=is_ges,
            created_date=date.today().isoformat(),
            appointment_date=None,
            appointment_location=None,
        )

        self.db.requests[sic_id] = sic
        self.db.requests_by_run[patient_run].append(sic_id)

        return sic

    @is_tool(ToolType.WRITE)
    def send_request(self, sic_id: str) -> ReferralRequest:
        """
        Send a referral request (SIC), transitioning it from 'borrador' to 'enviada'.
        The agent must have already confirmed that all required exams are attached
        and that the patient and doctor belong to the same CESFAM before calling this tool.
        This tool does NOT validate clinical criteria.

        Args:
            sic_id: The ID of the SIC to send.

        Returns:
            The updated SIC in 'enviada' state.

        Raises:
            ValueError: If the SIC is not found or is not in 'borrador' state.
        """
        if sic_id not in self.db.requests:
            raise ValueError(f"No se encontró ninguna interconsulta con ID {sic_id}.")
        sic = self.db.requests[sic_id]
        if sic.status != ReferralRequestStatus.BORRADOR:
            raise ValueError(
                f"Solo se pueden enviar interconsultas en estado 'borrador'. "
                f"El estado actual de {sic_id} es '{sic.status.name}'."
            )
        sic.status = ReferralRequestStatus.ENVIADA
        return sic

    @is_tool(ToolType.WRITE)
    def cancel_request(self, sic_id: str) -> ReferralRequest:
        """
        Cancel a referral request (SIC), transitioning it to 'anulada'.
        Only SICs in 'borrador', 'enviada', o 'pendiente_de_citacion' state can be cancelled.

        Args:
            sic_id: The ID of the SIC to cancel.

        Returns:
            The updated SIC in 'anulada' state.

        Raises:
            ValueError: If the SIC is not found or its current state does not allow cancellation.
        """
        if sic_id not in self.db.requests:
            raise ValueError(f"No se encontró ninguna interconsulta con ID {sic_id}.")
        sic = self.db.requests[sic_id]
        if sic.status not in _CANCELLABLE_STATES:
            allowed = ", ".join(state.name for state in _CANCELLABLE_STATES)
            raise ValueError(
                f"La interconsulta {sic_id} no puede anularse porque está en estado '{sic.status.name}'. "
                f"Solo se pueden anular interconsultas en estado: {allowed}."
            )
        sic.status = ReferralRequestStatus.ANULADA
        return sic

    # -------------------------------------------------------------------------
    # Assert functions (used by the evaluator, not callable by the agent)
    # -------------------------------------------------------------------------

    def assert_request_status(
        self, sic_id: str, expected_status: ReferralRequestStatus
    ) -> bool:
        try:
            return self.db.requests[sic_id].status == expected_status
        except KeyError:
            raise ValueError(f"No se encontró ninguna interconsulta con ID {sic_id}.")

    def assert_request_not_sent(
        self,
        patient_run: str,
        specialty: Optional[Specialty] = None,
    ) -> bool:
        """
        Check that no SIC for a given patient (and optionally specialty) is in
        'enviada', 'pendiente_de_citacion', or 'citada' state.
        Used to verify the agent did not send a referral it should have blocked.

        Args:
            patient_run: The patient's RUN.
            specialty: Optional specialty filter. If provided, only SICs for
                       that specialty are checked.

        Returns:
            True if no matching SIC has been sent (i.e. the block was effective).
        """

        try:
            # If user not found or not a patient, treat as nothing was sent
            self._get_user_or_raise(patient_run, UserRole.PATIENT)
        except ValueError:
            return True

        for sic_id in self.db.requests_by_run.get(patient_run, []):
            if sic_id not in self.db.requests:
                continue
            sic = self.db.requests[sic_id]
            if specialty is not None and sic.specialty != specialty:
                continue
            if sic.status in _SENT_STATES:
                return False
        return True


if __name__ == "__main__":
    from tau2.domains.healthcare_macalupu.utils import HEALTHCARE_DB_PATH

    healthcare = HealthcareTools(
        HealthcareDB.load(HEALTHCARE_DB_PATH),  # pyright: ignore[reportArgumentType]
        AuthCodeService(),
    )
    print(healthcare.get_statistics())
