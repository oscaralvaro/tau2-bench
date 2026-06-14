import secrets


class AuthCodeService:
    """Service for managing authentication codes."""

    def __init__(self) -> None:
        self._codes_by_run: dict[str, str] = {}
        self._codes: list[str] = []

    def generate_code(self, run: str) -> str:
        """Generate a new authentication code for the given RUN."""
        code = secrets.token_hex(4)
        self._codes_by_run[run] = code  # Garantiza que solo un código exista por RUN
        self._codes.append(code)
        return code

    def verify_code(self, run: str, code: str) -> bool:
        """Verify that the given code matches the one for the given RUN."""
        return self._codes_by_run.get(run) == code and self._codes[-1] == code

    def remove_code(self, run: str) -> None:
        """Remove the authentication code for the given RUN."""
        self._codes_by_run.pop(run, None)
