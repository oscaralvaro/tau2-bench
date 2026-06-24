from tau2.evaluator.evaluator import _get_environment_constructor


def test_environment_constructor_receives_e4_env_args(monkeypatch):
    received = {}

    def fake_constructor(**kwargs):
        received.update(kwargs)
        return object()

    monkeypatch.setattr(
        "tau2.evaluator.evaluator.registry.get_env_constructor",
        lambda domain: fake_constructor,
    )

    constructor = _get_environment_constructor(
        "divemotor_santiago",
        {
            "chunking_strategy": "fixed_200",
            "retrieval_k": 3,
            "use_think": False,
        },
    )
    constructor(solo_mode=False)

    assert received == {
        "chunking_strategy": "fixed_200",
        "retrieval_k": 3,
        "use_think": False,
        "solo_mode": False,
    }
