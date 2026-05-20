from typing import Optional
from tau2.environment.toolkit import ToolKitBase, ToolType, is_tool
from tau2.domains.cable_calderon.data_model import CableCalderonDB
import random



class CableCalderonToolKit(ToolKitBase):
    """Herramientas del agente para el dominio CableHogar"""

    db: CableCalderonDB

    @is_tool(ToolType.READ)
    def get_client_details(self, cliente_id: str) -> dict:
        """
        Obtiene los datos completos de un cliente, incluyendo nombre del titular,
        teléfono, email, dirección, estado de deuda y contactos autorizados.
        Usar para verificar identidad y datos del cliente antes de realizar cambios.
        """
        cliente = self.db.clientes.get(cliente_id)
        if not cliente:
            return {"error": f"No se encontró cliente con ID {cliente_id}"}
        return cliente.model_dump()
    
    @is_tool(ToolType.READ)
    def get_service_details(self, cliente_id: str) -> dict:
        """
        Obtiene los detalles del servicio activo de un cliente: plan contratado,
        estado del servicio, fecha de inicio y vencimiento.
        """
        servicio = next(
            (s for s in self.db.servicios.values() if s.cliente_id == cliente_id),
            None
        )
        if not servicio:
            return {"error": f"No se encontró servicio para el cliente {cliente_id}"}

        plan = self.db.planes.get(servicio.plan_id)
        return {
            **servicio.model_dump(),
            "plan_nombre": plan.nombre if plan else "Desconocido",
            "plan_precio": plan.precio_mensual if plan else None,
        }

    @is_tool(ToolType.READ)
    def list_available_plans(self, tipo: Optional[str] = None) -> dict:
        """
        Lista todos los planes disponibles. Opcionalmente filtra por tipo:
        'internet', 'cable' o 'combo'.
        """
        planes = list(self.db.planes.values())
        if tipo:
            planes = [p for p in planes if p.tipo == tipo]
        if not planes:
            return {"error": f"No se encontraron planes para el tipo '{tipo}'"}
        return {"planes": [p.model_dump() for p in planes]}

    @is_tool(ToolType.READ)
    def get_order_details(self, orden_id: str) -> dict:
        """
        Obtiene los detalles de una orden de instalación: tipo, fecha programada,
        hora, técnico asignado y estado actual.
        """
        orden = self.db.ordenes.get(orden_id)
        if not orden:
            return {"error": f"No se encontró orden con ID {orden_id}"}
        return orden.model_dump()

    @is_tool(ToolType.WRITE)
    def schedule_installation(
        self,
        cliente_id: str,
        tipo: str,
        fecha_programada: str,
        hora_programada: str
    ) -> dict:
        """
        Agenda una nueva orden de instalación o visita técnica para un cliente.
        tipo puede ser: 'instalacion_nueva', 'mantenimiento' o 'retiro'.
        fecha_programada en formato YYYY-MM-DD, hora_programada en formato HH:MM.
        No se puede agendar si el cliente tiene deuda pendiente.
        """
        cliente = self.db.clientes.get(cliente_id)
        if not cliente:
            return {"error": f"No se encontró cliente con ID {cliente_id}"}
        if cliente.tiene_deuda:
            return {
                "error": f"El cliente tiene una deuda pendiente de S/ {cliente.monto_deuda:.2f}. "
                         f"Debe regularizar su situación antes de agendar una instalación."
            }
        tipos_validos = ["instalacion_nueva", "mantenimiento", "retiro"]
        if tipo not in tipos_validos:
            return {"error": f"Tipo inválido. Debe ser uno de: {tipos_validos}"}

        nueva_id = f"O{str(len(self.db.ordenes) + 1).zfill(3)}"
        from tau2.domains.cable_calderon.data_model import OrdenInstalacion
        nueva_orden = OrdenInstalacion(
            orden_id=nueva_id,
            cliente_id=cliente_id,
            tipo=tipo,
            fecha_programada=fecha_programada,
            hora_programada=hora_programada,
            tecnico_asignado=None,
            estado="pendiente"
        )
        self.db.ordenes[nueva_id] = nueva_orden
        return {
            "mensaje": f"Orden agendada exitosamente.",
            "orden": nueva_orden.model_dump()
        }

    @is_tool(ToolType.WRITE)
    def reschedule_installation(
        self,
        orden_id: str,
        nueva_fecha: str,
        nueva_hora: str
    ) -> dict:
        """
        Reprograma una orden de instalación existente a una nueva fecha y hora.
        Solo se puede reprogramar si faltan MÁS DE 48 horas para la fecha actual (2026-03-30).
        nueva_fecha en formato YYYY-MM-DD, nueva_hora en formato HH:MM.
        """
        from datetime import datetime
        orden = self.db.ordenes.get(orden_id)
        if not orden:
            return {"error": f"No se encontró orden con ID {orden_id}"}
        if orden.estado in ["completada", "cancelada", "en_curso"]:
            return {"error": f"La orden {orden_id} está en estado '{orden.estado}' y no puede reprogramarse."}

        fecha_actual = datetime.strptime("2026-03-30 23:00", "%Y-%m-%d %H:%M")
        fecha_orden = datetime.strptime(f"{orden.fecha_programada} {orden.hora_programada}", "%Y-%m-%d %H:%M")
        diferencia_horas = (fecha_orden - fecha_actual).total_seconds() / 3600

        if diferencia_horas <= 48:
            return {
                "error": f"No se puede reprogramar la orden {orden_id}. "
                         f"Solo quedan {diferencia_horas:.1f} horas para la fecha programada. "
                         f"Se requieren más de 48 horas de anticipación."
            }

        orden.fecha_programada = nueva_fecha
        orden.hora_programada = nueva_hora
        return {
            "mensaje": f"Orden {orden_id} reprogramada exitosamente.",
            "orden": orden.model_dump()
        }

    @is_tool(ToolType.WRITE)
    def cancel_installation(self, orden_id: str) -> dict:
        """
        Cancela una orden de instalación.
        No se puede cancelar si la orden ya tiene técnico asignado y faltan
        menos de 24 horas. Tampoco si está en estado 'en_curso' o 'completada'.
        """
        from datetime import datetime
        orden = self.db.ordenes.get(orden_id)
        if not orden:
            return {"error": f"No se encontró orden con ID {orden_id}"}
        if orden.estado in ["completada", "en_curso"]:
            return {"error": f"La orden {orden_id} está en estado '{orden.estado}' y no puede cancelarse."}
        if orden.estado == "cancelada":
            return {"error": f"La orden {orden_id} ya está cancelada."}

        if orden.tecnico_asignado:
            from datetime import datetime as dt
            fecha_actual = datetime.strptime("2026-03-30 23:00", "%Y-%m-%d %H:%M")
            fecha_orden = datetime.strptime(f"{orden.fecha_programada} {orden.hora_programada}", "%Y-%m-%d %H:%M")
            diferencia_horas = (fecha_orden - fecha_actual).total_seconds() / 3600
            if diferencia_horas <= 24:
                return {
                    "error": f"No se puede cancelar la orden {orden_id}. "
                             f"Ya tiene técnico asignado ({orden.tecnico_asignado}) y "
                             f"faltan menos de 24 horas ({diferencia_horas:.1f}h)."
                }

        orden.estado = "cancelada"
        return {
            "mensaje": f"Orden {orden_id} cancelada exitosamente.",
            "orden": orden.model_dump()
        }

    @is_tool(ToolType.WRITE)
    def upgrade_plan(self, cliente_id: str, nuevo_plan_id: str) -> dict:
        """
        Realiza un upgrade del plan de servicio de un cliente a un plan de mayor nivel.
        Solo se permite pasar a un plan de nivel superior (upgrade).
        No se permite downgrade. El servicio debe estar en estado 'activo'.
        """
        servicio = next(
            (s for s in self.db.servicios.values() if s.cliente_id == cliente_id),
            None
        )
        if not servicio:
            return {"error": f"No se encontró servicio para el cliente {cliente_id}"}
        if servicio.estado != "activo":
            return {"error": f"El servicio del cliente {cliente_id} está '{servicio.estado}'. Solo se puede hacer upgrade a servicios activos."}

        plan_actual = self.db.planes.get(servicio.plan_id)
        plan_nuevo = self.db.planes.get(nuevo_plan_id)

        if not plan_nuevo:
            return {"error": f"No se encontró plan con ID {nuevo_plan_id}"}
        if plan_nuevo.nivel <= plan_actual.nivel:
            return {
                "error": f"No se puede realizar downgrade. El plan '{plan_nuevo.nombre}' (nivel {plan_nuevo.nivel}) "
                         f"es igual o inferior al plan actual '{plan_actual.nombre}' (nivel {plan_actual.nivel}). "
                         f"Para downgrades se requiere la intervención de un supervisor."
            }

        servicio.plan_id = nuevo_plan_id
        return {
            "mensaje": f"Plan actualizado exitosamente.",
            "plan_anterior": plan_actual.nombre,
            "plan_nuevo": plan_nuevo.nombre,
            "nuevo_precio": plan_nuevo.precio_mensual
        }

    @is_tool(ToolType.WRITE)
    def create_complaint(
        self,
        cliente_id: str,
        tipo: str,
        descripcion: str
    ) -> dict:
        """
        Abre un nuevo reclamo para un cliente.
        tipo puede ser: 'señal', 'facturacion', 'instalacion' u 'otro'.
        Los reclamos de tipo 'señal' se atienden en 72 horas hábiles.
        """
        cliente = self.db.clientes.get(cliente_id)
        if not cliente:
            return {"error": f"No se encontró cliente con ID {cliente_id}"}

        tipos_validos = ["señal", "facturacion", "instalacion", "otro"]
        if tipo not in tipos_validos:
            return {"error": f"Tipo inválido. Debe ser uno de: {tipos_validos}"}

        nuevo_id = f"R{str(len(self.db.reclamos) + 1).zfill(3)}"
        from tau2.domains.cable_calderon.data_model import Reclamo
        nuevo_reclamo = Reclamo(
            reclamo_id=nuevo_id,
            cliente_id=cliente_id,
            tipo=tipo,
            descripcion=descripcion,
            estado="abierto",
            fecha_creacion="2026-03-30",
            fecha_resolucion=None
        )
        self.db.reclamos[nuevo_id] = nuevo_reclamo

        mensaje = f"Reclamo {nuevo_id} creado exitosamente."
        if tipo == "señal":
            mensaje += " Será atendido en un plazo de 72 horas hábiles."

        return {
            "mensaje": mensaje,
            "reclamo": nuevo_reclamo.model_dump()
        }

    @is_tool(ToolType.READ)
    def get_complaint_status(self, reclamo_id: str) -> dict:
        """
        Consulta el estado actual de un reclamo existente.
        Retorna tipo, descripción, estado y fechas de creación y resolución.
        """
        reclamo = self.db.reclamos.get(reclamo_id)
        if not reclamo:
            return {"error": f"No se encontró reclamo con ID {reclamo_id}"}
        return reclamo.model_dump()
    @is_tool
    def send_sms_code(self, cliente_id: str) -> str:
        """
        Envía un código de verificación SMS de 6 dígitos al número de teléfono
        registrado del cliente. Usar ANTES de realizar operaciones sensibles que
        requieran verificación de identidad (cambio de plan, cancelación de orden,
        reprogramación, apertura de reclamos).
 
        El código expira al ser verificado exitosamente o al enviarse uno nuevo.
 
        Args:
            cliente_id: ID del cliente que debe recibir el código SMS.
 
        Returns:
            Confirmación de que el SMS fue enviado con el número enmascarado,
            o un mensaje de error si el cliente no existe.
        """
        cliente = self.db.clientes.get(cliente_id)
        if not cliente:
            return f"Error: no se encontró el cliente '{cliente_id}'."
 
        # Generar código de 6 dígitos
        codigo = str(random.randint(100000, 999999))
 
        # Guardar en la DB para que el user_tools pueda leerlo
        self.db.pending_sms_code = codigo
        self.db.pending_sms_cliente_id = cliente_id
 
        # Enmascarar el teléfono para mostrar solo los últimos 3 dígitos
        telefono = cliente.telefono
        telefono_enmascarado = "*" * (len(telefono) - 3) + telefono[-3:]
 
        return (
            f"Código SMS enviado exitosamente al número {telefono_enmascarado} "
            f"del titular {cliente.nombre_titular}. "
            f"Solicita al cliente que te proporcione el código de 6 dígitos recibido."
        )
 
    @is_tool
    def verify_sms_code(self, cliente_id: str, codigo: str, rol: str = "user") -> str:
        """
        Verifica el código SMS proporcionado por el cliente. Debe llamarse después de
        send_sms_code() y luego de que el cliente haya comunicado el código recibido.
 
        También valida el rol del solicitante (user = cliente titular, employee = empleado
        de la empresa). Solo los roles autorizados pueden continuar con operaciones sensibles.
 
        Args:
            cliente_id: ID del cliente que está verificando su identidad.
            codigo: El código de 6 dígitos que el cliente proporcionó.
            rol: Rol del solicitante. Valores válidos: 'user' (cliente) o 'employee'.
 
        Returns:
            Confirmación de identidad verificada exitosamente, o mensaje de error
            si el código es incorrecto, no existe código pendiente, o el rol es inválido.
        """
        # Validar rol
        roles_validos = ["user", "employee"]
        if rol not in roles_validos:
            return (
                f"Error: rol '{rol}' no reconocido. "
                f"Los roles válidos son: {', '.join(roles_validos)}."
            )
 
        # Verificar que existe un código pendiente para este cliente
        codigo_esperado = getattr(self.db, "pending_sms_code", None)
        cliente_esperado = getattr(self.db, "pending_sms_cliente_id", None)
 
        if not codigo_esperado or not cliente_esperado:
            return (
                "Error: no hay ningún código SMS pendiente de verificación. "
                "Usa send_sms_code primero para enviar un código al cliente."
            )
 
        if cliente_esperado != cliente_id:
            return (
                f"Error: el código pendiente corresponde a otro cliente. "
                f"Envía un nuevo código al cliente '{cliente_id}' con send_sms_code."
            )
 
        # Verificar el código
        if codigo.strip() != codigo_esperado:
            return (
                "Error: el código ingresado es incorrecto. "
                "Solicita al cliente que verifique el SMS recibido e intente nuevamente."
            )
 
        # Código correcto -> limpiar el código pendiente
        self.db.pending_sms_code = None
        self.db.pending_sms_cliente_id = None
 
        cliente = self.db.clientes.get(cliente_id)
        nombre = cliente.nombre_titular if cliente else cliente_id
 
        return (
            f"Identidad verificada exitosamente. "
            f"Cliente: {nombre} (ID: {cliente_id}) | Rol: {rol}. "
            f"Puede proceder con la operación solicitada."
        )