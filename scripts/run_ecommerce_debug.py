import argparse
import sys

from tau2.cli import main


def build_throttle_args(bucket: str) -> str:
    return (
        '{"temperature": 0.0, '
        '"rate_limit_requests_per_minute": 27, '
        '"rate_limit_requests_per_day": 14000, '
        '"rate_limit_tokens_per_minute": 15000, '
        '"rate_limit_token_reserve": 750, '
        f'"rate_limit_bucket": "{bucket}"'
        "}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Debug wrapper for tau2 run")
    parser.add_argument("--domain", default="ecommerce_calle")
    parser.add_argument("--agent", default="llm_agent")
    parser.add_argument("--agent-llm", required=True)
    parser.add_argument("--user-llm", required=True)
    parser.add_argument("--num-trials", default="1")
    parser.add_argument("--num-tasks")
    parser.add_argument("--save-to", default="ecommerce_pass1")
    parser.add_argument("--log-level", default="DEBUG")
    parser.add_argument("--max-concurrency", default="1")
    parser.add_argument("--task-ids", nargs="*")
    parser.add_argument("--rate-limit-bucket", default="google-free-tier")
    return parser.parse_args()


def run() -> None:
    args = parse_args()
    throttle_args = build_throttle_args(args.rate_limit_bucket)

    sys.argv = [
        "tau2",
        "run",
        "--domain",
        args.domain,
        "--agent",
        args.agent,
        "--agent-llm",
        args.agent_llm,
        "--agent-llm-args",
        throttle_args,
        "--user-llm",
        args.user_llm,
        "--user-llm-args",
        throttle_args,
        "--num-trials",
        args.num_trials,
        "--max-concurrency",
        args.max_concurrency,
        "--save-to",
        args.save_to,
        "--log-level",
        args.log_level,
    ]

    if args.num_tasks:
        sys.argv.extend(["--num-tasks", args.num_tasks])

    if args.task_ids:
        sys.argv.extend(["--task-ids", *args.task_ids])

    main()


if __name__ == "__main__":
    run()
