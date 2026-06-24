from tau2.environment.rag import ChromaPolicyIndex
from tau2.domains.cable_calderon.tools import CableCalderonToolKit


def _fake_embed(texts):
    import math, random

    def make_vec(text, dim=8):
        rng = random.Random(hash(text) & 0xFFFFFFFF)
        v = [rng.gauss(0, 1) for _ in range(dim)]
        n = math.sqrt(sum(x * x for x in v)) or 1.0
        return [x / n for x in v]

    return [make_vec(t) for t in texts]


SAMPLE_POLICY = """
## Reclamos
El agente puede abrir reclamos para clientes verificados.

## Cancelaciones
Una orden no puede cancelarse si ya tiene técnico asignado y faltan menos de 24 horas.

## Cambios de plan
Antes de cambiar un plan, se debe verificar identidad.
"""


def test_retrieve_policy_returns_text():
    index = ChromaPolicyIndex(SAMPLE_POLICY, strategy="headers", _embed_fn=_fake_embed)
    kit = CableCalderonToolKit(db=None, policy_index=index)

    result = kit.retrieve_policy(query="¿puedo cancelar una orden con técnico asignado?")

    assert isinstance(result, str)
    assert len(result) > 0


def test_toolkit_has_think_tool():
    kit = CableCalderonToolKit(db=None)

    assert "think" in kit.tools