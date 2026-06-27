import datetime

from tau2.domains.estaciondeservicio_Rivera.data_model import Customer, FuelStationDB
from tau2.domains.estaciondeservicio_Rivera.environment import (
    EstacionDeServicioRiveraEnvironment,
)
from tau2.domains.estaciondeservicio_Rivera.tools import EstacionDeServicioRiveraTools
from tau2.domains.estaciondeservicio_Rivera.user_data_model import RiveraUserDB
from tau2.domains.estaciondeservicio_Rivera.user_tools import (
    EstacionDeServicioRiveraUserTools,
)


def test_user_tool_can_read_latest_sms_code():
    agent_db = FuelStationDB(
        clientes={
            "cliente_0001": Customer(
                id_cliente="cliente_0001",
                nombre_contacto="Elena Paredes",
                razon_social="Transporte Rivera Norte SAC",
                ruc="20601234567",
                telefono="987654321",
                email="elena@riveranorte.pe",
                direccion_fiscal="Calle San Martin 145, Sullana, Piura",
                direcciones_entrega=["Planta Sullana, Zona Industrial Lote 12, Sullana, Piura"],
                correo_facturacion="facturacion@riveranorte.pe",
            )
        }
    )
    tools = EstacionDeServicioRiveraTools(agent_db)
    tools._get_now = lambda: datetime.datetime(2026, 3, 30, 10, 0, 0)

    user_db = RiveraUserDB()
    user_tools = EstacionDeServicioRiveraUserTools(user_db)
    user_tools.configure_user_session(
        customer_id="cliente_0001",
        role="customer_contact",
        telefono="987654321",
        nombre="Elena Paredes",
    )

    env = EstacionDeServicioRiveraEnvironment(
        domain_name="estaciondeservicio_Rivera",
        policy="policy",
        tools=tools,
        user_tools=user_tools,
    )

    dispatch = env.tools.send_sms_verification_code(
        id_cliente="cliente_0001",
        reason="Confirmar cancelacion",
    )
    env.sync_tools()

    code = env.user_tools.revisar_sms_de_verificacion()
    assert code == env.tools.db.sms_verifications[dispatch.verification_id].code
    assert env.user_tools.assert_sms_received(True) is True
