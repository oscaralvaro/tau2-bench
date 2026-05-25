from tau2.data_model.message import AssistantMessage, UserMessage
from tau2.evaluator.evaluator_nl_assertions import NLAssertionsEvaluator


def test_evaluate_nl_assertions_falls_back_when_response_is_not_json(monkeypatch):
    monkeypatch.setattr(
        "tau2.evaluator.evaluator_nl_assertions.generate",
        lambda **kwargs: AssistantMessage(role="assistant", content="not json"),
    )

    checks = NLAssertionsEvaluator.evaluate_nl_assertions(
        [UserMessage(role="user", content="hello")],
        ["The agent should greet the user."],
    )

    assert len(checks) == 1
    assert checks[0].nl_assertion == "The agent should greet the user."
    assert checks[0].met is False
    assert "non-JSON" in checks[0].justification


def test_evaluate_nl_assertions_accepts_json_in_code_fence(monkeypatch):
    monkeypatch.setattr(
        "tau2.evaluator.evaluator_nl_assertions.generate",
        lambda **kwargs: AssistantMessage(
            role="assistant",
            content=(
                "```json\n"
                '{"results":[{"expectedOutcome":"The agent should greet the user.",'
                '"reasoning":"The agent said hello.","metExpectation":true}]}\n'
                "```"
            ),
        ),
    )

    checks = NLAssertionsEvaluator.evaluate_nl_assertions(
        [UserMessage(role="user", content="hello")],
        ["The agent should greet the user."],
    )

    assert len(checks) == 1
    assert checks[0].nl_assertion == "The agent should greet the user."
    assert checks[0].met is True
    assert checks[0].justification == "The agent said hello."
