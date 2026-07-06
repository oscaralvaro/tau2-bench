"""
user_tools.py - Herramientas del lado del usuario para el dominio cable_calderon.

El usuario simulado puede usar estas herramientas para:
  - Consultar el código SMS de verificación recibido en su teléfono
  - Ver los datos básicos de su propia cuenta

El flujo de verificación por SMS es:
  1. El agente llama a send_sms_code(cliente_id) -> genera un código y lo guarda en la DB
  2. El usuario llama a get_sms_code() -> lee el código almacenado en la DB
  3. El usuario le comunica el código al agente
  4. El agente llama a verify_sms_code(cliente_id, codigo) -> valida el código

Esto simula de forma controlada el flujo de autenticación de dos factores (2FA) por SMS.
"""

from tau2.environment.toolkit import ToolKitBase, is_tool
from tau2.domains.cable_calderon.data_model import CableCalderonDB


class CableUserToolKit(ToolKitBase):
    """
    Herramientas disponibles para el usuario simulado en el dominio cable_calderon.
    El usuario tiene acceso limitado: solo puede leer su propio estado (teléfono simulado).
    """

    db: CableCalderonDB

    @is_tool
    def get_sms_code(self) -> str:
        """
        Consulta el código de verificación SMS más reciente almacenado en el dispositivo
        del usuario (simulado). Este código fue enviado previamente por el agente.

        Usar esta herramienta cuando el agente indique que ha enviado un código SMS
        al número de teléfono registrado y solicite que el usuario lo proporcione.

        Returns:
            El código SMS de 6 dígitos si existe uno pendiente, o un mensaje indicando
            que no hay ningún código pendiente.
        """
        # El código SMS se almacena en la DB bajo la clave 'pending_sms_code'
        # El agente lo genera con send_sms_code() y el usuario lo lee aquí.
        codigo = getattr(self.db, "pending_sms_code", None)
        cliente_id = getattr(self.db, "pending_sms_cliente_id", None)

        if not codigo or not cliente_id:
            return (
                "No hay ningún código SMS pendiente en tu dispositivo. "
                "Espera a que el agente envíe el código a tu número registrado."
            )

        return (
            f"Código SMS recibido en tu teléfono: {codigo}. "
            f"Proporciona este código al agente para continuar."
        )

    @is_tool
    def get_my_account_info(self, cliente_id: str) -> str:
        """
        Consulta la información básica de tu propia cuenta de cliente.
        Solo disponible para el titular de la cuenta.

        Args:
            cliente_id: Tu ID de cliente (por ejemplo, 'C001').

        Returns:
            Nombre del titular, teléfono registrado y estado del servicio,
            o un mensaje de error si el cliente no existe.
        """
        cliente = self.db.clientes.get(cliente_id)
        if not cliente:
            return f"No se encontró ninguna cuenta con el ID '{cliente_id}'."

        # Buscar el servicio activo del cliente
        servicio_info = "Sin servicio registrado"
        for s in self.db.servicios.values():
            if s.cliente_id == cliente_id:
                plan = self.db.planes.get(s.plan_id)
                nombre_plan = plan.nombre if plan else s.plan_id
                servicio_info = (
                    f"Plan: {nombre_plan} | Estado: {s.estado} | "
                    f"Vencimiento: {s.fecha_vencimiento}"
                )
                break

        deuda_info = ""
        if cliente.tiene_deuda:
            deuda_info = f" | Deuda pendiente: S/ {cliente.monto_deuda:.2f}"

        return (
            f"Cuenta: {cliente.cliente_id} | "
            f"Titular: {cliente.nombre_titular} | "
            f"Teléfono: {cliente.telefono} | "
            f"Email: {cliente.email} | "
            f"{servicio_info}"
            f"{deuda_info}"
        )