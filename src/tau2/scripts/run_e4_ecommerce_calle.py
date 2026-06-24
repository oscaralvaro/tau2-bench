from __future__ import annotations

import argparse
from pathlib import Path

from tau2.run import EvaluationType, get_tasks, run_tasks

TASK_IDS = ["3", "8", "10", "11", "14", "16", "19", "21", "22", "23"]
MODEL = "gemini/gemma-4-26b-a4b-it"
LLM_ARGS = {
    "temperature": 0.0,
    "rate_limit_requests_per_minute": 14,
    "rate_limit_requests_per_day": 14000,
    "rate_limit_tokens_per_minute": 150000,
    "rate_limit_bucket": "gemma4-free-tier",
    "rate_limit_token_reserve": 750,
}
SAVE_PATHS = {
    "B": Path("data/simulations/sim_e4_B_headers_k3.json"),
    "C": Path("data/simulations/sim_e4_C_fixed_k3.json"),
    "D": Path("data/simulations/sim_e4_D_best_think.json"),
}


def build_env_args(condition: str, chunking_strategy: str | None) -> dict:
    if condition == "B":
        return {"chunking_strategy": "headers", "retrieval_k": 3}
    if condition == "C":
        strategy = chunking_strategy or "fixed_200"
        return {"chunking_strategy": strategy, "retrieval_k": 3}
    if condition == "D":
        strategy = chunking_strategy or "headers"
        return {"chunking_strategy": strategy, "retrieval_k": 3, "use_think": True}
    raise ValueError(f"Unsupported condition: {condition}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run E4 ecommerce_calle condition.")
    parser.add_argument("--condition", choices=["B", "C", "D"], required=True)
    parser.add_argument("--chunking-strategy", default=None)
    parser.add_argument("--save-to", default=None)
    args = parser.parse_args()

    tasks = get_tasks(task_set_name="ecommerce_calle", task_ids=TASK_IDS)
    env_args = build_env_args(args.condition, args.chunking_strategy)
    save_to = Path(args.save_to) if args.save_to else SAVE_PATHS[args.condition]

    results = run_tasks(
        domain="ecommerce_calle",
        tasks=tasks,
        agent="llm_agent",
        user="user_simulator",
        llm_agent=MODEL,
        llm_args_agent=LLM_ARGS,
        llm_user=MODEL,
        llm_args_user=LLM_ARGS,
        env_args=env_args,
        num_trials=5,
        max_steps=30,
        max_errors=10,
        save_to=save_to,
        console_display=False,
        evaluation_type=EvaluationType.ALL,
        max_concurrency=1,
        seed=300,
        log_level="ERROR",
    )
    print(f"completed {args.condition} {len(results.simulations)} simulations")


if __name__ == "__main__":
    main()
