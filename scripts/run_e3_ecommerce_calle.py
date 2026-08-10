from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

import tau2.config as tau2_config
import tau2.evaluator.evaluator_nl_assertions as nl_eval_module
from tau2.evaluator.evaluator import EvaluationType
from tau2.run import get_tasks, run_tasks


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent-llm", default="gemini/gemma-4-31b-it")
    parser.add_argument("--user-llm", default="gemini/gemma-4-31b-it")
    parser.add_argument("--nl-assertions-llm", default="gemini/gemma-4-31b-it")
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--num-retries", type=int, default=6)
    parser.add_argument("--num-trials", type=int, default=5)
    parser.add_argument("--max-concurrency", type=int, default=1)
    parser.add_argument("--max-steps", type=int, default=100)
    parser.add_argument("--max-errors", type=int, default=10)
    parser.add_argument("--seed", type=int, default=300)
    parser.add_argument("--log-level", default="INFO")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def set_policy(policy_path: Path, prompts_dir: Path, base_policy: str, prompt_file: str | None) -> None:
    if prompt_file is None:
        policy_path.write_text(base_policy, encoding="utf-8")
        return

    prompt_path = prompts_dir / prompt_file
    policy_path.write_text(prompt_path.read_text(encoding="utf-8"), encoding="utf-8")


def parse_relaxed_json(text: str) -> dict:
    text = (text or "").strip()
    if not text:
        raise ValueError("El evaluador NL devolvio contenido vacio.")

    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
        text = text.strip()

    for candidate in (text, text[text.find("{") : text.rfind("}") + 1] if "{" in text and "}" in text else ""):
        if not candidate:
            continue
        try:
            data = json.loads(candidate)
            if isinstance(data, dict):
                return data
            if isinstance(data, list):
                return {"results": data}
        except json.JSONDecodeError:
            continue

    raise ValueError(f"No se pudo extraer JSON valido del evaluador NL: {text[:400]}")


def install_custom_nl_evaluator(model: str, timeout: int, num_retries: int) -> None:
    tau2_config.DEFAULT_LLM_NL_ASSERTIONS = model
    tau2_config.DEFAULT_LLM_NL_ASSERTIONS_ARGS = {
        "temperature": 0.0,
        "timeout": timeout,
        "num_retries": num_retries,
    }
    nl_eval_module.DEFAULT_LLM_NL_ASSERTIONS = model
    nl_eval_module.DEFAULT_LLM_NL_ASSERTIONS_ARGS = {
        "temperature": 0.0,
        "timeout": timeout,
        "num_retries": num_retries,
    }

    def _evaluate_nl_assertions(cls, trajectory, nl_assertions):
        trajectory_str = "\n".join(
            [f"{message.role}: {message.content}" for message in trajectory]
        )
        system_prompt = """
        TASK
        - You will be given a list of expected outcomes and a conversation that was collected during a test case run.
        - The conversation is between an agent and a customer.
        - Your job is to evaluate whether the agent satisfies each of the expected outcomes.
        - Grade each expected outcome individually.

        FORMAT
        - Return ONLY a valid JSON object. Do not add markdown fences or extra text.
        - Use the fields:
        - `reasoning`: a short explanation for your classification
        - `metExpectation`: `true` if the agent satisfies the expected outcome, `false` otherwise
        - `expectedOutcome`: repeat the expectation from the input that you are grading

        Example response structure:
        {
            "results": [
                {
                    "expectedOutcome": "<one of the expected outcomes from the input>",
                    "reasoning": "<reasoning trace>",
                    "metExpectation": true
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
            nl_eval_module.SystemMessage(role="system", content=system_prompt),
            nl_eval_module.UserMessage(role="user", content=user_prompt),
        ]

        assistant_message = nl_eval_module.generate(
            model=model,
            messages=messages,
            **tau2_config.DEFAULT_LLM_NL_ASSERTIONS_ARGS,
        )
        result_data = parse_relaxed_json(assistant_message.content or "")
        results = result_data.get("results", [])
        if isinstance(results, dict):
            results = [results]

        normalized = []
        for result in results:
            expected_outcome = result.get("expectedOutcome") or result.get("nl_assertion")
            met = result.get("metExpectation")
            if isinstance(met, str):
                met = met.strip().lower() == "true"
            reasoning = result.get("reasoning") or result.get("justification") or ""
            normalized.append(
                nl_eval_module.NLAssertionCheck(
                    nl_assertion=expected_outcome,
                    met=bool(met),
                    justification=reasoning,
                )
            )
        return normalized

    nl_eval_module.NLAssertionsEvaluator.evaluate_nl_assertions = classmethod(
        _evaluate_nl_assertions
    )


def main() -> None:
    args = parse_args()

    if not os.environ.get("GEMINI_API_KEY"):
        raise RuntimeError("GEMINI_API_KEY no esta configurada en la terminal actual.")

    root = Path(__file__).resolve().parents[1]
    policy_path = root / "data" / "tau2" / "domains" / "ecommerce_calle" / "policy.md"
    prompts_dir = root / "data" / "tau2" / "domains" / "ecommerce_calle" / "prompts"
    simulations_dir = root / "data" / "simulations"
    base_policy = policy_path.read_text(encoding="utf-8")

    # Keep NL-assertion judging on Gemini too, without modifying the repo config.
    install_custom_nl_evaluator(
        args.nl_assertions_llm,
        timeout=args.timeout,
        num_retries=args.num_retries,
    )

    runs = [
        {
            "name": "sim_e3_baseline",
            "prompt": None,
            "task_split_name": "base_top10hard",
            "task_ids": None,
        },
        {
            "name": "sim_e3_exp1_task8",
            "prompt": "policy_e3_exp1.md",
            "task_split_name": None,
            "task_ids": ["8"],
        },
        {
            "name": "sim_e3_exp2_task8",
            "prompt": "policy_e3_exp2.md",
            "task_split_name": None,
            "task_ids": ["8"],
        },
        {
            "name": "sim_e3_exp3_task14",
            "prompt": "policy_e3_exp3.md",
            "task_split_name": None,
            "task_ids": ["14"],
        },
        {
            "name": "sim_e3_exp4_task14",
            "prompt": "policy_e3_exp4.md",
            "task_split_name": None,
            "task_ids": ["14"],
        },
        {
            "name": "sim_e3_exp5_task23",
            "prompt": "policy_e3_exp5.md",
            "task_split_name": None,
            "task_ids": ["23"],
        },
        {
            "name": "sim_e3_exp6_task23",
            "prompt": "policy_e3_exp6.md",
            "task_split_name": None,
            "task_ids": ["23"],
        },
        {
            "name": "sim_e3_final",
            "prompt": None,
            "task_split_name": "base",
            "task_ids": None,
        },
    ]

    try:
        for run in runs:
            set_policy(policy_path, prompts_dir, base_policy, run["prompt"])
            save_to = simulations_dir / f"{run['name']}.json"
            tasks = get_tasks(
                "ecommerce_calle",
                task_split_name=run["task_split_name"],
                task_ids=run["task_ids"],
            )

            print(f"\n==> {run['name']}")
            print(f"tasks={len(tasks)} save_to={save_to}")
            if args.dry_run:
                continue

            run_tasks(
                domain="ecommerce_calle",
                tasks=tasks,
                agent="llm_agent",
                user="user_simulator",
                llm_agent=args.agent_llm,
                llm_args_agent={
                    "temperature": 0.0,
                    "timeout": args.timeout,
                    "num_retries": args.num_retries,
                },
                llm_user=args.user_llm,
                llm_args_user={
                    "temperature": 0.0,
                    "timeout": args.timeout,
                    "num_retries": args.num_retries,
                },
                num_trials=args.num_trials,
                max_steps=args.max_steps,
                max_errors=args.max_errors,
                save_to=save_to,
                console_display=True,
                evaluation_type=EvaluationType.ALL_WITH_NL_ASSERTIONS,
                max_concurrency=args.max_concurrency,
                seed=args.seed,
                log_level=args.log_level,
            )
    finally:
        policy_path.write_text(base_policy, encoding="utf-8")


if __name__ == "__main__":
    main()
