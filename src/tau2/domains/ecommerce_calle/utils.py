from pathlib import Path

DOMAIN_DIR = Path(__file__).parent
DATA_DIR = Path(__file__).parents[4] / "data" / "tau2" / "domains" / "ecommerce_calle"

ECOMMERCE_DB_PATH = DATA_DIR / "db.json"
ECOMMERCE_POLICY_PATH = DATA_DIR / "policy.md"
ECOMMERCE_TASK_SET_PATH = DATA_DIR / "tasks.json"