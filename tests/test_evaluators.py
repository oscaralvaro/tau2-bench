from tau2.data_model.message import AssistantMessage
from tau2.evaluator.evaluator_communicate import CommunicateEvaluator
from tau2.evaluator.evaluator_nl_assertions import NLAssertionsEvaluator


def test_communicate_evaluator_matches_accents():
    checks = CommunicateEvaluator.evaluate_communicate_info(
        [
            AssistantMessage(
                role="assistant",
                content="La Habitación Doble cuesta 180.0 por noche.",
            )
        ],
        ["Habitacion Doble"],
    )

    assert checks[0].met is True


def test_nl_assertion_parser_accepts_markdown_json_block():
    result = NLAssertionsEvaluator._parse_json_response(
        """
        ```json
        {
          "results": [
            {
              "expectedOutcome": "El agente no inventa datos.",
              "reasoning": "La respuesta se mantiene dentro de la politica.",
              "metExpectation": true
            }
          ]
        }
        ```
        """
    )

    assert result["results"][0]["metExpectation"] is True
