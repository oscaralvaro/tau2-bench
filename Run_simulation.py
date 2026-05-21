import os
import sys
from pathlib import Path
from datetime import datetime


sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from tau2.cli import main


def _build_save_name(base_name: str) -> str:
    """
    Avoid interactive resume prompts by picking a fresh output name when needed.
    """
    output_path = Path(__file__).resolve().parent / "data" / "simulations" / f"{base_name}.json"
    if not output_path.exists():
        return base_name

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{base_name}_{timestamp}"

throttle_args = (
    '{"temperature": 0.0, '
    '"rate_limit_requests_per_minute": 27, '
    '"rate_limit_requests_per_day": 14000, '
    '"rate_limit_tokens_per_minute": 15000, '
    '"rate_limit_token_reserve": 750, '
    '"rate_limit_bucket": "google-free-tier"}'
)

sys.argv = [
    "tau2",
    "run",
    "--domain",          "ecommerce_calle",
    "--agent-llm",       "openrouter/google/gemma-3-27b-it",
    "--agent-llm-args",  throttle_args,
    "--user-llm",         "openrouter/google/gemma-3-27b-it",
    "--user-llm-args",   throttle_args,
    "--num-trials",      "1",
    "--max-concurrency", "1",
    "--save-to",         _build_save_name("ecommerce_pass1"),
    "--log-level",       "ERROR",
]

main()
