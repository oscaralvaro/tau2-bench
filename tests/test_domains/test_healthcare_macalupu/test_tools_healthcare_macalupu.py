import pytest

from tau2.domains.healthcare_macalupu.auth_data_model import AuthCodeService
from tau2.domains.healthcare_macalupu.data_model import (
    HealthcareDB,
    ReferralRequest,
    ReferralRequestStatus,
    Specialty,
    User,
    UserRole,
)
from tau2.domains.healthcare_macalupu.tools import HealthcareTools
from tau2.domains.healthcare_macalupu.user_data_model import HealthcareUserDB
from tau2.domains.healthcare_macalupu.user_tools import HealthcareUserTools


@pytest.fixture
def healthcare_db():
    # Two users: one doctor and two patients
    users = {
        "11111111-1": User(
            run="11111111-1",
            name="Dr. Test",
            birth_date="1970-01-01",
            cesfam="CESFAM Test A",
            role=UserRole.DOCTOR,
            phone="+56911111111",
        ),
        "22222222-2": User(
            run="22222222-2",
            name="Paciente Test",
            birth_date="1980-02-02",
            cesfam="CESFAM Test A",
            role=UserRole.PATIENT,
            phone="+56922222222",
        ),
        "33333333-3": User(
            run="33333333-3",
            name="Paciente Con Cita",
            birth_date="1960-03-03",
            cesfam="CESFAM Test A",
            role=UserRole.PATIENT,
            phone="+56933333333",
        ),
    }

    # Build a few referral requests with different statuses
    requests = {
        "SIC-001": ReferralRequest(
            sic_id="SIC-001",
            patient_run="22222222-2",
            doctor_run="11111111-1",
            specialty=Specialty.OFTALMOLOGIA,
            cie10_code="H26.9",
            cie10_description="Catarata",
            reason="Prueba",
            priority="P2",
            attached_exams=["a-001"],
            status=ReferralRequestStatus.BORRADOR,
            is_ges=False,
            created_date="2025-01-01",
            appointment_date=None,
            appointment_location=None,
        ),
        "SIC-002": ReferralRequest(
            sic_id="SIC-002",
            patient_run="22222222-2",
            doctor_run="11111111-1",
            specialty=Specialty.OTORRINOLARINGOLOGIA,
            cie10_code="H91.9",
            cie10_description="Hipoacusia",
            reason="Prueba 2",
            priority="P2",
            attached_exams=["a-002"],
            status=ReferralRequestStatus.ENVIADA,
            is_ges=False,
            created_date="2025-02-01",
            appointment_date=None,
            appointment_location=None,
        ),
        "SIC-003": ReferralRequest(
            sic_id="SIC-003",
            patient_run="33333333-3",
            doctor_run="11111111-1",
            specialty=Specialty.OFTALMOLOGIA,
            cie10_code="H26.9",
            cie10_description="Catarata",
            reason="Cita asignada",
            priority="P1",
            attached_exams=["a-003"],
            status=ReferralRequestStatus.CITADA,
            is_ges=False,
            created_date="2025-03-01",
            appointment_date="2025-07-10 09:00",
            appointment_location="Hospital Test",
        ),
    }

    requests_by_run = {
        "22222222-2": ["SIC-001", "SIC-002"],
        "33333333-3": ["SIC-003"],
    }

    return HealthcareDB(
        users=users, requests=requests, requests_by_run=requests_by_run, analyses={}
    )


@pytest.fixture
def auth_and_tools(healthcare_db):
    auth = AuthCodeService()
    # Share auth._codes list with user DB inbox so user_tools can read generated codes
    user_db = HealthcareUserDB(sms_inbox=auth._codes)
    tools = HealthcareTools(healthcare_db, auth)
    user_tools = HealthcareUserTools(user_db)
    auth.add_observer(user_db)
    return auth, tools, user_tools


class TestAuthFlow:
    def test_send_and_receive_code(self, auth_and_tools):
        auth, tools, user_tools = auth_and_tools
        # Send auth SMS to patient 22222222-2
        resp = tools.send_auth_sms("22222222-2", "+56922222222")
        assert isinstance(resp, str)
        # The user tools inbox should contain the generated code
        code = user_tools.receive_sms()
        assert len(code) > 0 and isinstance(code, str)

    def test_authenticate_with_correct_code(self, auth_and_tools):
        auth, tools, user_tools = auth_and_tools
        # Generate code explicitly and authenticate
        auth.generate_code("22222222-2")

        # El usuario recibe el código a través de receive_sms
        code = user_tools.receive_sms()

        # El agente autentica al usuariocon el código recibido
        user = tools.authenticate_user("22222222-2", code)
        assert user.run == "22222222-2"

    def test_authenticate_with_wrong_code_raises(self, auth_and_tools):
        _, tools, _ = auth_and_tools
        with pytest.raises(ValueError):
            tools.authenticate_user("22222222-2", "deadbeef")

    def test_authenticate_with_old_code_fails(self, auth_and_tools):
        auth, tools, user_tools = auth_and_tools
        # Generate first code and capture it via user inbox
        auth.generate_code("22222222-2")
        old_code = user_tools.receive_sms()
        # Generate a new (fresh) code
        auth.generate_code("22222222-2")
        new_code = user_tools.receive_sms()

        # Old code should no longer be valid
        with pytest.raises(ValueError):
            tools.authenticate_user("22222222-2", old_code)

        # New code should authenticate successfully
        user = tools.authenticate_user("22222222-2", new_code)
        assert user.run == "22222222-2"


class TestRequestLifecycle:
    def test_create_request_adds_and_links(self, auth_and_tools, healthcare_db):
        _, tools, _ = auth_and_tools
        before_count = len(healthcare_db.requests)
        sic = tools.create_request(
            doctor_run="11111111-1",
            patient_run="22222222-2",
            specialty=Specialty.OTORRINOLARINGOLOGIA,
            cie10_code="H91.9",
            cie10_description="Hipoacusia",
            reason="Razón",
            priority="P2",
            attached_exams=["a-010"],
            is_ges=False,
        )
        assert len(healthcare_db.requests) == before_count + 1
        assert sic.status == ReferralRequestStatus.BORRADOR
        assert sic.sic_id in healthcare_db.requests_by_run["22222222-2"]

    def test_send_request_transitions(self, auth_and_tools, healthcare_db):
        _, tools, _ = auth_and_tools
        # Ensure SIC-001 is borrador
        assert (
            healthcare_db.requests["SIC-001"].status == ReferralRequestStatus.BORRADOR
        )
        tools.send_request("SIC-001")
        assert healthcare_db.requests["SIC-001"].status == ReferralRequestStatus.ENVIADA

    def test_send_request_bad_state_raises(self, auth_and_tools):
        _, tools, _ = auth_and_tools
        with pytest.raises(ValueError):
            tools.send_request("SIC-002")  # already ENVIADA

    def test_cancel_allowed_and_disallowed(self, auth_and_tools, healthcare_db):
        _, tools, _ = auth_and_tools
        # Cancel SIC-001 (now ENVIADA from previous test run or BORRADOR)
        # Re-create state to BORRADOR to be safe
        healthcare_db.requests["SIC-001"].status = ReferralRequestStatus.BORRADOR
        tools.cancel_request("SIC-001")
        assert healthcare_db.requests["SIC-001"].status == ReferralRequestStatus.ANULADA

        # Attempt to cancel a CITADA should raise
        with pytest.raises(ValueError):
            tools.cancel_request("SIC-003")

    def test_assert_request_status_and_not_sent(self, auth_and_tools, healthcare_db):
        _, tools, _ = auth_and_tools
        assert tools.assert_request_status("SIC-002", ReferralRequestStatus.ENVIADA)
        assert not tools.assert_request_status("SIC-001", ReferralRequestStatus.ENVIADA)
        # Patient 33333333-3 has a CITADA SIC, so assert_request_not_sent should be False
        assert tools.assert_request_not_sent("33333333-3") is False
        # Non-existent patient should return True
        assert tools.assert_request_not_sent("99999999-9") is True
