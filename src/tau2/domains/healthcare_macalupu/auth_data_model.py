import secrets


class AuthCodeObserver:
    def update(self, new_code: str) -> None:
        pass


class AuthCodeService:
    """Service for managing authentication codes."""

    def __init__(self) -> None:
        self.observers: list[AuthCodeObserver] = []
        self._codes_by_run: dict[str, str] = {}
        self._codes: list[str] = []

    def generate_code(self, run: str) -> None:
        """Generate a new authentication code for the given RUN."""
        code = secrets.token_hex(4)
        self._codes_by_run[run] = code  # Garantiza que solo un código exista por RUN
        self._codes.append(code)

        self._notify_observers()

    def verify_code(self, run: str, code: str) -> bool:
        """Verify that the given code matches the one for the given RUN."""
        return self._codes_by_run.get(run) == code and self._codes[-1] == code

    def remove_code_by_run(self, run: str) -> None:
        """Remove the authentication code for the given RUN."""
        self._codes_by_run.pop(run, None)

    # Implementacion de patron Observer

    def add_observer(self, observer: AuthCodeObserver) -> None:
        self.observers.append(observer)

    def _notify_observers(self) -> None:
        for observer in self.observers:
            observer.update(self._codes[-1])
