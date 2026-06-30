import math
import random

from tau2.data_model.message import AssistantMessage, ToolCall
from tau2.domains.restaurante_joaquin_cachay.data_model import (
    RestauranteJoaquinCachayDB,
)
from tau2.domains.restaurante_joaquin_cachay.environment import get_environment
from tau2.domains.restaurante_joaquin_cachay.tools import RestauranteJoaquinCachayTools
from tau2.domains.restaurante_joaquin_cachay.user_data_model import RestaurantUserDB
from tau2.domains.restaurante_joaquin_cachay.utils import (
    RESTAURANTE_JOAQUIN_CACHAY_DB_PATH,
)
from tau2.environment.rag import THINK_INSTRUCTION, ChromaPolicyIndex


def _fake_embed(texts):
    def make_vec(text, dim=8):
        rng = random.Random(hash(text) & 0xFFFFFFFF)
        values = [rng.gauss(0, 1) for _ in range(dim)]
        norm = math.sqrt(sum(x * x for x in values)) or 1.0
        return [x / norm for x in values]

    return [make_vec(text) for text in texts]


def test_get_environment_propagates_chunking_strategy(monkeypatch) -> None:
    import tau2.domains.restaurante_joaquin_cachay.environment as env_mod

    db = RestauranteJoaquinCachayDB.load(RESTAURANTE_JOAQUIN_CACHAY_DB_PATH)
    created_strategies = []
    original_cls = env_mod.ChromaPolicyIndex

    class SpyIndex(original_cls):
        def __init__(self, policy_text, strategy="headers", _embed_fn=None):
            created_strategies.append(strategy)
            super().__init__(policy_text, strategy=strategy, _embed_fn=_fake_embed)

    monkeypatch.setattr(env_mod, "ChromaPolicyIndex", SpyIndex)

    get_environment(
        db=db,
        user_db=RestaurantUserDB(),
        use_rag=True,
        chunking_strategy="fixed_200",
    )

    assert created_strategies == ["fixed_200"]


def test_get_environment_propagates_retrieval_k(monkeypatch) -> None:
    import tau2.domains.restaurante_joaquin_cachay.environment as env_mod

    db = RestauranteJoaquinCachayDB.load(RESTAURANTE_JOAQUIN_CACHAY_DB_PATH)
    original_cls = env_mod.ChromaPolicyIndex

    class FakeIndex(original_cls):
        def __init__(self, policy_text, strategy="headers", _embed_fn=None):
            super().__init__(policy_text, strategy=strategy, _embed_fn=_fake_embed)

    monkeypatch.setattr(env_mod, "ChromaPolicyIndex", FakeIndex)

    env = get_environment(
        db=db,
        user_db=RestaurantUserDB(),
        use_rag=True,
        retrieval_k=7,
    )

    assert env.tools.retrieval_k == 7


def test_get_environment_use_think_appends_instruction(monkeypatch) -> None:
    import tau2.domains.restaurante_joaquin_cachay.environment as env_mod

    db = RestauranteJoaquinCachayDB.load(RESTAURANTE_JOAQUIN_CACHAY_DB_PATH)
    original_cls = env_mod.ChromaPolicyIndex

    class FakeIndex(original_cls):
        def __init__(self, policy_text, strategy="headers", _embed_fn=None):
            super().__init__(policy_text, strategy=strategy, _embed_fn=_fake_embed)

    monkeypatch.setattr(env_mod, "ChromaPolicyIndex", FakeIndex)

    env = get_environment(
        db=db,
        user_db=RestaurantUserDB(),
        use_rag=True,
        use_think=True,
    )

    assert THINK_INSTRUCTION in env.policy


def test_get_environment_hides_rag_tools_when_disabled() -> None:
    db = RestauranteJoaquinCachayDB.load(RESTAURANTE_JOAQUIN_CACHAY_DB_PATH)

    env = get_environment(
        db=db,
        user_db=RestaurantUserDB(),
        use_rag=False,
    )

    assert "retrieve_policy" not in env.tools.get_tools()
    assert "think" not in env.tools.get_tools()


def test_environment_replay_rehydrates_policy_index_without_env_args(monkeypatch) -> None:
    import tau2.domains.restaurante_joaquin_cachay.environment as env_mod
    import tau2.domains.restaurante_joaquin_cachay.tools as tools_mod

    db = RestauranteJoaquinCachayDB.load(RESTAURANTE_JOAQUIN_CACHAY_DB_PATH)
    original_env_index = env_mod.ChromaPolicyIndex

    class FakeIndex(original_env_index):
        def __init__(self, policy_text, strategy="headers", _embed_fn=None):
            super().__init__(policy_text, strategy=strategy, _embed_fn=_fake_embed)

    monkeypatch.setattr(env_mod, "ChromaPolicyIndex", FakeIndex)
    monkeypatch.setattr(tools_mod, "ChromaPolicyIndex", FakeIndex)

    rag_env = get_environment(
        db=db,
        user_db=RestaurantUserDB(),
        use_rag=True,
    )
    tool_call = ToolCall(
        id="call-1",
        name="retrieve_policy",
        arguments={"query": "Como debo manejar una cancelacion con SMS?"},
        requestor="assistant",
    )
    tool_message = rag_env.get_response(tool_call)

    replay_env = get_environment(
        db=RestauranteJoaquinCachayDB.load(RESTAURANTE_JOAQUIN_CACHAY_DB_PATH),
        user_db=RestaurantUserDB(),
        use_rag=False,
    )
    replay_env.set_state(
        initialization_data=None,
        initialization_actions=None,
        message_history=[
            AssistantMessage(role="assistant", content=None, tool_calls=[tool_call]),
            tool_message,
        ],
    )

    assert isinstance(replay_env.tools, RestauranteJoaquinCachayTools)
    assert replay_env.tools.policy_index is not None
