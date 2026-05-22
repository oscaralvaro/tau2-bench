from tau2.domains.estaciondeservicio_Rivera.data_model import SMSRole
from tau2.domains.estaciondeservicio_Rivera.user_data_model import (
    RiveraUserDB,
    RiveraUserSession,
    SMSInboxMessage,
)
from tau2.environment.toolkit import ToolKitBase, ToolType, is_tool


class EstacionDeServicioRiveraUserTools(ToolKitBase):
    """User-side tools for SMS verification flows."""

    db: RiveraUserDB

    def __init__(self, db: RiveraUserDB) -> None:
        super().__init__(db)

    def configure_user_session(
        self,
        customer_id: str | None = None,
        user_id: str | None = None,
        role: SMSRole = "customer_contact",
        telefono: str | None = None,
        nombre: str | None = None,
    ) -> RiveraUserSession:
        """Configures the simulated user identity for SMS verification scenarios."""
        self.db.session = RiveraUserSession(
            customer_id=customer_id,
            user_id=user_id,
            role=role,
            telefono=telefono,
            nombre=nombre,
        )
        return self.db.session

    def _message_belongs_to_active_user(self, message: SMSInboxMessage) -> bool:
        session = self.db.session
        if session.customer_id is not None and message.customer_id != session.customer_id:
            return False
        if message.role != session.role:
            return False
        if message.user_id is not None and session.user_id != message.user_id:
            return False
        if session.telefono is not None and message.phone != session.telefono:
            return False
        return True

    def _get_latest_matching_sms(self) -> SMSInboxMessage | None:
        matching = [
            message
            for message in self.db.sms_inbox.values()
            if self._message_belongs_to_active_user(message)
        ]
        if not matching:
            return None
        matching.sort(key=lambda message: message.sent_at)
        return matching[-1]

    @is_tool(ToolType.READ)
    def revisar_sms_de_verificacion(self) -> str:
        """Revisa el ultimo codigo SMS de verificacion recibido por el usuario actual."""
        message = self._get_latest_matching_sms()
        if message is None:
            raise ValueError("No hay ningun codigo SMS de verificacion disponible para el usuario actual")
        message.consumed = True
        return message.code

    @is_tool(ToolType.READ)
    def revisar_bandeja_sms(self) -> str:
        """Muestra un resumen del ultimo SMS de verificacion recibido por el usuario actual."""
        message = self._get_latest_matching_sms()
        if message is None:
            return "No tienes mensajes SMS de verificacion pendientes."
        reason = message.reason or "sin motivo especificado"
        return (
            f"Ultimo SMS recibido para el cliente {message.customer_id} "
            f"con rol {message.role} a las {message.sent_at.isoformat()}. "
            f"Motivo: {reason}."
        )

    def assert_last_sms_code_equals(self, expected_code: str) -> bool:
        """Asserts that the latest matching SMS code equals the expected code."""
        message = self._get_latest_matching_sms()
        if message is None:
            return False
        return message.code == expected_code

    def assert_sms_received(self, expected_status: bool = True) -> bool:
        """Asserts whether an SMS was received for the active user."""
        return (self._get_latest_matching_sms() is not None) == expected_status
