import hashlib
import json
import math
import random
from pathlib import Path
from shutil import rmtree

from tau2.data_model.message import AssistantMessage, ToolCall, ToolMessage
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
    assert (
        replay_env.tools.retrieve_policy("Como debo manejar una cancelacion con SMS?")
        == tool_message.content
    )


def test_environment_replay_recovers_fixed_chunking_from_cached_tool_message(
    monkeypatch,
) -> None:
    import tau2.domains.restaurante_joaquin_cachay.environment as env_mod
    import tau2.domains.restaurante_joaquin_cachay.tools as tools_mod

    db = RestauranteJoaquinCachayDB.load(RESTAURANTE_JOAQUIN_CACHAY_DB_PATH)
    temp_dir = Path("data/test_cache_env_args_restaurante_replay")

    try:
        rmtree(temp_dir, ignore_errors=True)
        temp_dir.mkdir(parents=True, exist_ok=True)
        monkeypatch.setattr(env_mod, "_POLICY_CACHE_DIR", temp_dir)

        tools_mod.RestauranteJoaquinCachayTools._POLICY_RESULT_CACHE.clear()
        tools_mod.RestauranteJoaquinCachayTools._POLICY_RESULT_CACHE_FILES_LOADED.clear()

        replay_env = get_environment(
            db=db,
            user_db=RestaurantUserDB(),
            use_rag=False,
        )
        policy_text = replay_env.tools._policy_text
        assert policy_text is not None
        policy_digest = hashlib.sha1(policy_text.encode("utf-8")).hexdigest()
        query = (
            "Existen reglas especiales o excepciones para clientes Gold VIP "
            "en pedidos o disponibilidad?"
        )
        expected_content = "## Cuando Rechazar\n\n- el item solicitado esta no disponible"
        cache_path = temp_dir / f"policy_results_fixed_200_{policy_digest}.json"
        payload = {
            f"fixed_200:{policy_digest}||3||{query}": expected_content,
        }
        cache_path.write_text(
            json.dumps(payload, ensure_ascii=False, sort_keys=True),
            encoding="utf-8",
        )

        tool_call = ToolCall(
            id="call-fixed-200",
            name="retrieve_policy",
            arguments={"query": query},
            requestor="assistant",
        )
        tool_message = ToolMessage(
            id="call-fixed-200",
            role="tool",
            content=expected_content,
            requestor="assistant",
            error=False,
        )

        replay_env.set_state(
            initialization_data=None,
            initialization_actions=None,
            message_history=[
                AssistantMessage(role="assistant", content=None, tool_calls=[tool_call]),
                tool_message,
            ],
        )

        assert replay_env.tools._chunking_strategy == "fixed_200"
        assert replay_env.tools.retrieve_policy(query) == expected_content
    finally:
        tools_mod.RestauranteJoaquinCachayTools._POLICY_RESULT_CACHE.clear()
        tools_mod.RestauranteJoaquinCachayTools._POLICY_RESULT_CACHE_FILES_LOADED.clear()
        rmtree(temp_dir, ignore_errors=True)




def test_get_environment_reuses_cached_policy_index(monkeypatch) -> None:
    import tau2.domains.restaurante_joaquin_cachay.environment as env_mod

    db = RestauranteJoaquinCachayDB.load(RESTAURANTE_JOAQUIN_CACHAY_DB_PATH)
    created = []
    original_cls = env_mod.ChromaPolicyIndex
    env_mod._POLICY_INDEX_CACHE.clear()

    class FakeIndex(original_cls):
        def __init__(self, policy_text, strategy="headers", _embed_fn=None):
            created.append((strategy, len(policy_text)))
            super().__init__(policy_text, strategy=strategy, _embed_fn=_fake_embed)

    monkeypatch.setattr(env_mod, "ChromaPolicyIndex", FakeIndex)

    env_one = get_environment(
        db=db,
        user_db=RestaurantUserDB(),
        use_rag=True,
        chunking_strategy="headers",
    )
    env_two = get_environment(
        db=RestauranteJoaquinCachayDB.load(RESTAURANTE_JOAQUIN_CACHAY_DB_PATH),
        user_db=RestaurantUserDB(),
        use_rag=True,
        chunking_strategy="headers",
    )

    assert env_one.tools.policy_index is env_two.tools.policy_index
    assert created == [("headers", len(env_one.tools._policy_text))]


def test_get_environment_reuses_persisted_policy_chunk_embeddings(monkeypatch) -> None:
    import tau2.domains.restaurante_joaquin_cachay.environment as env_mod

    db = RestauranteJoaquinCachayDB.load(RESTAURANTE_JOAQUIN_CACHAY_DB_PATH)
    embed_calls = []
    env_mod._POLICY_INDEX_CACHE.clear()

    def fake_make_embed_fn():
        def embed(texts):
            embed_calls.append(list(texts))
            return _fake_embed(texts)

        return embed

    temp_dir = Path("data/test_cache_env_args_restaurante")
    try:
        rmtree(temp_dir, ignore_errors=True)
        temp_dir.mkdir(parents=True, exist_ok=True)
        monkeypatch.setattr(env_mod, "_POLICY_CACHE_DIR", temp_dir)
        monkeypatch.setattr(env_mod, "_make_gemini_embed_fn", fake_make_embed_fn)

        get_environment(
            db=db,
            user_db=RestaurantUserDB(),
            use_rag=True,
            chunking_strategy="fixed_200",
        )

        assert len(embed_calls) == 1
        env_mod._POLICY_INDEX_CACHE.clear()
        get_environment(
            db=RestauranteJoaquinCachayDB.load(RESTAURANTE_JOAQUIN_CACHAY_DB_PATH),
            user_db=RestaurantUserDB(),
            use_rag=True,
            chunking_strategy="fixed_200",
        )

        assert len(embed_calls) == 1
    finally:
        rmtree(temp_dir, ignore_errors=True)
