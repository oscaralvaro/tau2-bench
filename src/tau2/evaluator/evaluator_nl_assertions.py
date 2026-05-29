import json
import logging
from typing import Optional

from tau2.config import DEFAULT_LLM_NL_ASSERTIONS, DEFAULT_LLM_NL_ASSERTIONS_ARGS
from tau2.data_model.message import Message, SystemMessage, UserMessage
from tau2.data_model.simulation import NLAssertionCheck, RewardInfo
from tau2.data_model.tasks import RewardType, Task
from tau2.utils.llm_utils import generate


class NLAssertionsEvaluator:
    """
    Judge that evaluates whether a trajectory adheres to all the natural-language assertions.
    """

    @classmethod
    def calculate_reward(
        cls,
        task: Task,
        full_trajectory: list[Message],
    ) -> RewardInfo:
        """
        Calculate the reward for the simulation by using an LLM to evaluate whether the trajectory adheres to all the natural-language assertions
        """
        if task.evaluation_criteria is None:
            return RewardInfo(
                reward=1.0,
                nl_assertions=[],
                info={"note": "No evaluation criteria"},
                reward_breakdown={RewardType.NL_ASSERTION: 1.0},
            )
        nl_assertions = task.evaluation_criteria.nl_assertions
        if not nl_assertions:
            return RewardInfo(
                reward=1.0,
                nl_assertions=[],
                info={"note": "No nl_assertions to evaluate"},
                reward_breakdown={RewardType.NL_ASSERTION: 1.0},
            )

        nl_assertions_checks = cls.evaluate_nl_assertions(
            full_trajectory, nl_assertions
        )

        # Calculate reward: 1 if all expectations are met, 0 otherwise
        all_expectations_met = all(result.met for result in nl_assertions_checks)
        reward = 1.0 if all_expectations_met else 0.0

        return RewardInfo(
            reward=reward,
            nl_assertions=nl_assertions_checks,
            reward_breakdown={RewardType.NL_ASSERTION: reward},
        )

    @classmethod
    def evaluate_nl_assertions(
        cls,
        trajectory: list[Message],
        nl_assertions: list[str],
    ) -> list[NLAssertionCheck]:
        """
        Evaluate whether the trajectory meets each expected outcome.

        Args:
            trajectory: List of messages from the conversation
            nl_assertions: List of natural-language assertions to evaluate

        Returns:
            List of evaluation results for each NL assertion, containing:
            - nl_assertion: The NL assertion being evaluated
            - metExpectation: Boolean indicating if the assertion was met
            - reasoning: Explanation for the evaluation
        """
        trajectory_str = "\n".join(
            [f"{message.role}: {message.content}" for message in trajectory]
        )
        # System prompt similar to the TypeScript implementation
        system_prompt = """
        TASK
        - You will be given a list of expected outcomes and a conversation that was collected during a test case run.
        - The conversation is between an agent and a customer.
        - Your job is to evaluate whether the agent satisfies each of the expected outcomes.
        - Grade each expected outcome individually.

        FORMAT
        - Your response should be a JSON object with the following fields:
        - `reasoning`: a short explanation for your classification
        - `metExpectation`: `true` if the agent satisfies the expected outcomes, `false` otherwise
        - `expectedOutcome`: repeat the expectation from the input that you are grading
        
        Example response structure:
        {
            "results": [
                {
                    "expectedOutcome": "<one of the expected outcomes from the input>",
                    "reasoning": "<reasoning trace>",
                    "metExpectation": <false or true>,
                }
            ]
        }
        """

        user_prompt = f"""
        conversation:
        {trajectory_str}
        
        expectedOutcomes:
        {nl_assertions}
        """

        messages = [
            SystemMessage(role="system", content=system_prompt),
            UserMessage(role="user", content=user_prompt),
        ]

        # We'll attempt up to N retries with increasingly strict prompts to
        # force the model to return a single JSON object. Also try to
        # extract any JSON object present in the text as a last resort.
        max_attempts = 3
        attempt = 0
        last_contents = []
        result_data = None
        while attempt < max_attempts and result_data is None:
            if attempt == 0:
                prompt_messages = messages
            else:
                strict_system = SystemMessage(
                    role="system",
                    content=(
                        "IMPORTANT: Respond ONLY with a single JSON object and NOTHING ELSE. "
                        "Do not include any prose or explanation. Return exactly a JSON object with a top-level 'results' array. "
                        "Example: {\n  \"results\": [ { \"expectedOutcome\": \"...\", \"reasoning\": \"...\", \"metExpectation\": true } ]\n}"
                    ),
                )
                prompt_messages = [strict_system, UserMessage(role="user", content=user_prompt)]

            assistant_message = generate(
                model=DEFAULT_LLM_NL_ASSERTIONS,
                messages=prompt_messages,
                **DEFAULT_LLM_NL_ASSERTIONS_ARGS,
            )
            content = assistant_message.content
            logging.debug("NL evaluator attempt %d response: %s", attempt + 1, repr(content))
            last_contents.append(content)

            # First try: use existing extractor which handles fenced blocks
            try:
                payload = cls._extract_json_payload(content)
                if payload:
                    result_data = json.loads(payload)
                    break
            except (json.JSONDecodeError, TypeError):
                result_data = None

            # Second try: attempt to find any balanced JSON object in the text
            try:
                json_candidate = cls._find_first_json_object(content)
                if json_candidate:
                    result_data = json.loads(json_candidate)
                    break
            except (json.JSONDecodeError, TypeError):
                result_data = None

            attempt += 1

        if result_data is None:
            # attach the raw responses as part of the justification for debugging
            justification = (
                "Evaluator model returned a non-JSON or empty response. Raw responses: "
                + " ||| ".join([repr(c) for c in last_contents if c is not None])
            )
            return cls._fallback_failed_checks(nl_assertions, justification)
        return [
            NLAssertionCheck(
                nl_assertion=result["expectedOutcome"],
                met=result["metExpectation"],
                justification=result["reasoning"],
            )
            for result in result_data.get("results", [])
        ]

    @staticmethod
    def _extract_json_payload(content: str | None) -> str | None:
        if content is None:
            return None
        stripped = content.strip()
        if stripped.startswith("```"):
            lines = stripped.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            stripped = "\n".join(lines).strip()
        # If the assistant included additional text around the JSON, attempt
        # to find the first JSON object in the text by locating the first
        # '{' and the last matching '}'. This helps when models prepend or
        # append explanations.
        if not stripped.startswith("{"):
            first = stripped.find("{")
            last = stripped.rfind("}")
            if first != -1 and last != -1 and last > first:
                return stripped[first : last + 1]
        return stripped

    @staticmethod
    def _find_first_json_object(content: str | None) -> Optional[str]:
        """Find the first balanced JSON object within the text by scanning
        for a '{' and finding the matching closing '}' taking nested braces
        into account. Returns the substring or None.
        """
        if not content:
            return None
        text = content
        start = text.find("{")
        while start != -1:
            depth = 0
            for i in range(start, len(text)):
                ch = text[i]
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        return text[start : i + 1]
            # if we didn't find a match, look for next '{'
            start = text.find("{", start + 1)
        return None

    @staticmethod
    def _fallback_failed_checks(
        nl_assertions: list[str], justification: str
    ) -> list[NLAssertionCheck]:
        return [
            NLAssertionCheck(
                nl_assertion=assertion,
                met=False,
                justification=justification,
            )
            for assertion in nl_assertions
        ]
