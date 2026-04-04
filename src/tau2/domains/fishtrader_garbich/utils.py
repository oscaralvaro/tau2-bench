from tau2.utils.utils import DATA_DIR

FISHTRADER_GARBICH_DATA_DIR = DATA_DIR / "tau2" / "domains" / "fishtrader_garbich"
FISHTRADER_GARBICH_DB_PATH = FISHTRADER_GARBICH_DATA_DIR / "db.json"
FISHTRADER_GARBICH_POLICY_PATH = FISHTRADER_GARBICH_DATA_DIR / "policy.md"
FISHTRADER_GARBICH_TASK_SET_PATH = FISHTRADER_GARBICH_DATA_DIR / "tasks.json"


def build_sample_db():
    """
    Build the sample database for the fish trader domain from the JSON seed file.

    This keeps the domain scaffold aligned with the course recommendation of
    generating the database through the Pydantic models, while still allowing the
    JSON file to be the editable source of truth during development.
    """
    from tau2.domains.fishtrader_garbich.data_model import FishTraderDB
    from tau2.utils import load_file

    data = load_file(FISHTRADER_GARBICH_DB_PATH)
    return FishTraderDB.model_validate(data)


def dump_sample_db() -> None:
    """
    Validate the fish trader DB through Pydantic and write it back to disk.
    """
    db = build_sample_db()
    db.dump(FISHTRADER_GARBICH_DB_PATH, indent=2)


if __name__ == "__main__":
    dump_sample_db()
