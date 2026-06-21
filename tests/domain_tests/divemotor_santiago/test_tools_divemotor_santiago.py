import math
import random

from tau2.domains.divemotor_santiago.environment import get_environment
from tau2.environment.rag import THINK_INSTRUCTION, ChromaPolicyIndex


def _fake_embed(texts):
    def _vector(text, dimension=8):
        rng = random.Random(hash(text) & 0xFFFFFFFF)
        values = [rng.gauss(0, 1) for _ in range(dimension)]
        norm = math.sqrt(sum(value * value for value in values)) or 1.0
        return [value / norm for value in values]

    return [_vector(text) for text in texts]


def test_divemotor_tools_sale_flow():
    env = get_environment(use_rag=False)

    cliente = env.use_tool("get_cliente", cliente_id="c1")
    assert cliente.id == "c1"

    vehiculos = env.use_tool("buscar_vehiculos", tipo="camion")
    assert len(vehiculos) == 1
    assert vehiculos[0].id == "v1"

    cotizacion = env.use_tool("crear_cotizacion", cliente_id="c1", vehiculo_id="v1")
    assert cotizacion.id == "cot_1"
    assert cotizacion.estado == "pendiente"

    envio = env.use_tool("enviar_codigo_sms", cliente_id="c1", rol_requerido="user")
    assert envio["estado"] == "codigo_enviado"

    codigo = env.use_user_tool("recibir_codigo_sms", cliente_id="c1")
    assert codigo["cliente_id"] == "c1"

    verificacion = env.use_tool(
        "verificar_codigo_sms",
        cliente_id="c1",
        codigo=codigo["codigo"],
        rol_requerido="user",
    )
    assert verificacion["estado"] == "verificado"

    cotizacion = env.use_tool("aprobar_cotizacion", cotizacion_id="cot_1")
    assert cotizacion.estado == "aprobada"

    pedido = env.use_tool("crear_pedido", cotizacion_id="cot_1")
    assert pedido.id == "ped_1"
    assert pedido.estado == "confirmado"
    assert env.tools.db.vehiculos["v1"].stock == 2

    pedido = env.use_tool("cancelar_pedido", pedido_id="ped_1")
    assert pedido.estado == "cancelado"


def test_divemotor_tools_reject_invalid_sale():
    env = get_environment(use_rag=False)

    assert (
        env.use_tool("crear_cotizacion", cliente_id="c2", vehiculo_id="v1")
        == "Error: presupuesto insuficiente"
    )
    assert (
        env.use_tool("crear_cotizacion", cliente_id="c1", vehiculo_id="v3")
        == "Error: sin stock"
    )
    assert env.use_tool("crear_pedido", cotizacion_id="cot_1") == (
        "Error: cotizacion no existe"
    )


def test_divemotor_sms_rejects_wrong_code_and_role():
    env = get_environment(use_rag=False)

    assert (
        env.use_tool("enviar_codigo_sms", cliente_id="c4", rol_requerido="user")
        == "Error: rol no autorizado"
    )

    envio = env.use_tool("enviar_codigo_sms", cliente_id="c1", rol_requerido="user")
    assert envio["estado"] == "codigo_enviado"

    codigo = env.use_user_tool("dar_codigo_sms_incorrecto", cliente_id="c1")
    assert (
        env.use_tool(
            "verificar_codigo_sms",
            cliente_id="c1",
            codigo=codigo["codigo"],
            rol_requerido="user",
        )
        == "Error: codigo incorrecto"
    )

    cotizacion = env.use_tool("crear_cotizacion", cliente_id="c1", vehiculo_id="v1")
    assert cotizacion.id == "cot_1"
    assert env.use_tool("aprobar_cotizacion", cotizacion_id="cot_1") == (
        "Error: identidad no verificada"
    )


def test_divemotor_retrieve_policy_uses_configured_k(monkeypatch):
    import tau2.domains.divemotor_santiago.environment as environment_module

    class FakePolicyIndex(ChromaPolicyIndex):
        def __init__(self, policy_text, strategy="headers", _embed_fn=None):
            super().__init__(
                policy_text,
                strategy=strategy,
                _embed_fn=_fake_embed,
            )

    monkeypatch.setattr(
        environment_module,
        "ChromaPolicyIndex",
        FakePolicyIndex,
    )

    env = environment_module.get_environment(retrieval_k=2, use_rag=True)
    result = env.use_tool(
        "retrieve_policy",
        query="requisitos para aprobar una cotizacion con SMS",
    )

    assert env.tools.retrieval_k == 2
    assert result
    assert result.count("---") == 1


def test_divemotor_think_is_available_and_instruction_is_conditional(monkeypatch):
    import tau2.domains.divemotor_santiago.environment as environment_module

    class FakePolicyIndex(ChromaPolicyIndex):
        def __init__(self, policy_text, strategy="headers", _embed_fn=None):
            super().__init__(
                policy_text,
                strategy=strategy,
                _embed_fn=_fake_embed,
            )

    monkeypatch.setattr(
        environment_module,
        "ChromaPolicyIndex",
        FakePolicyIndex,
    )

    env_without_think = environment_module.get_environment(
        use_think=False,
        use_rag=True,
    )
    env_with_think = environment_module.get_environment(
        use_think=True,
        use_rag=True,
    )

    assert env_with_think.tools.has_tool("think")
    assert env_with_think.use_tool("think", thought="validar politica") == ""
    assert THINK_INSTRUCTION not in env_without_think.policy
    assert THINK_INSTRUCTION in env_with_think.policy
