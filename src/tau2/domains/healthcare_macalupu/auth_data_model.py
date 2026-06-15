# Garantiza codigos deterministas y evita errores de tau2bench
_CODES_CANDIDATES: list[str] = [
    "1529f2ef",
    "0be9ac20",
    "60d0d8c1",
    "0cd9bbc5",
    "5d276b45",
    "ca5522eb",
    "2a688775",
    "dfaedc70",
    "26e408d9",
    "9d018901",
    "5ad5b975",
    "7d7df21a",
    "454e98aa",
    "b21681d8",
    "ed45b35f",
    "89317ce7",
]


class AuthCodeObserver:
    def update(self, new_code: str) -> None:
        pass


class AuthCodeService:
    """Service for managing authentication codes."""

    def __init__(self) -> None:
        self._next_selection_idx = 0
        self.observers: list[AuthCodeObserver] = []
        self._codes_by_run: dict[str, str] = {}
        self._codes: list[str] = []

    def generate_code(self, run: str) -> None:
        """Generate a new authentication code for the given RUN."""
        code = _CODES_CANDIDATES[self._next_selection_idx]
        if self._next_selection_idx < 15:
            self._next_selection_idx += 1
        else:
            raise IndexError("No more codes available")
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
