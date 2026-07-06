from tau2.domains.lopez.user_data_model import LopezUserDB, SMSInboxMessage
from tau2.environment.toolkit import ToolKitBase, ToolType, is_tool


class LopezUserTools(ToolKitBase):
    db: LopezUserDB

    def __init__(self, db: LopezUserDB) -> None:
        super().__init__(db)

    @is_tool(ToolType.READ)
    def revisar_bandeja_sms(self) -> list[SMSInboxMessage]:
        """
        Revisar los SMS de verificacion recibidos por el usuario.

        Returns:
            Lista de mensajes SMS del cliente actual.
        """
        if self.db.cliente_actual_id is None:
            return []
        mensajes = [
            sms for sms in self.db.sms_inbox if sms.cliente_id == self.db.cliente_actual_id
        ]
        for sms in mensajes:
            sms.leido = True
        return mensajes

    @is_tool(ToolType.READ)
    def leer_ultimo_codigo_sms(self) -> str:
        """
        Leer el codigo del SMS mas reciente del cliente actual.

        Returns:
            Codigo numerico mas reciente.
        """
        if self.db.cliente_actual_id is None:
            raise ValueError("No hay cliente actual configurado en el simulador")
        mensajes = [
            sms for sms in self.db.sms_inbox if sms.cliente_id == self.db.cliente_actual_id
        ]
        if not mensajes:
            raise ValueError("No hay SMS recibidos para el cliente actual")
        ultimo = mensajes[-1]
        ultimo.leido = True
        return ultimo.codigo

    def assert_sms_recibido(self, cliente_id: str, rol_requerido: str) -> bool:
        return any(
            sms.cliente_id == cliente_id and sms.rol_requerido == rol_requerido
            for sms in self.db.sms_inbox
        )
