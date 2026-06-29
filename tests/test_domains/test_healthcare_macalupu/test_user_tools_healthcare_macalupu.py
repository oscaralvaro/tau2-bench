import pytest

from tau2.domains.healthcare_macalupu.auth_data_model import AuthCodeService
from tau2.domains.healthcare_macalupu.user_data_model import HealthcareUserDB
from tau2.domains.healthcare_macalupu.user_tools import HealthcareUserTools


@pytest.fixture
def auth_and_user_tools():
    auth = AuthCodeService()
    # Share auth._codes list so user inbox reflects generated codes
    user_db = HealthcareUserDB()
    user_tools = HealthcareUserTools(user_db)
    auth.add_observer(user_db)
    return auth, user_tools


def test_receive_and_mark_used(auth_and_user_tools):
    auth, user_tools = auth_and_user_tools
    # Generate a code (generate_code does not return the code to the caller)
    auth.generate_code("22222222-2")

    # The user retrieves the code via the user tools inbox
    code = user_tools.receive_sms()
    assert len(code) > 0 and isinstance(code, str)

    # Mark it as used and now receive_sms must indicate no new SMS
    user_tools.mark_sms_as_used(code)
    assert user_tools.receive_sms() == "No hay nuevos SMS en la bandeja de entrada"
