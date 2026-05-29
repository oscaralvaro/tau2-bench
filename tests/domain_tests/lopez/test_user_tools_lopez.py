from tau2.data_model.message import ToolCall
from tau2.domains.lopez.environment import get_environment


def test_revisar_bandeja_sms_devuelve_mensaje_recibido():
    env = get_environment()
    env.user_tools.db.cliente_actual_id = "c2"
    env.use_tool("enviar_codigo_verificacion_sms", cliente_id="c2", rol_requerido="cliente")
    mensajes = env.use_user_tool("revisar_bandeja_sms")
    assert len(mensajes) == 1
    assert mensajes[0].cliente_id == "c2"
    assert mensajes[0].rol_requerido == "cliente"
    assert mensajes[0].codigo == "000001"


def test_leer_ultimo_codigo_sms():
    env = get_environment()
    env.user_tools.db.cliente_actual_id = "c2"
    env.use_tool("enviar_codigo_verificacion_sms", cliente_id="c2", rol_requerido="cliente")
    codigo = env.use_user_tool("leer_ultimo_codigo_sms")
    assert codigo == "000001"


def test_leer_ultimo_codigo_sms_sin_cliente_configurado_falla():
    env = get_environment()
    response = env.get_response(
        ToolCall(
            id="u1",
            name="leer_ultimo_codigo_sms",
            arguments={},
            requestor="user",
        )
    )
    assert response.error
