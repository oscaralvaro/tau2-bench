from tau2.domains.salud_mendoza_lista.data_model import (
    PrioridadInterconsulta,
    SaludDB,
)
from tau2.environment.toolkit import ToolKitBase, ToolType, is_tool


class SaludToolkit(ToolKitBase):
    def __init__(self, db: SaludDB):
        super().__init__(db)

    @is_tool(ToolType.READ)
    def get_patient_details(self, rut: str) -> str:
        """
        Obtiene el perfil del paciente, incluyendo nombre, prevision y comuna.
        """
        paciente = self.db.pacientes.get(rut)
        if paciente:
            return (
                f"DATOS ENCONTRADOS: Nombre: {paciente.nombre}, RUT: {paciente.rut}, "
                f"Prevision: {paciente.prevision}, Comuna: {paciente.comuna}"
            )
        return "ERROR: El RUT ingresado no existe en el registro civil simulado."

    @is_tool(ToolType.READ)
    def search_waiting_list_by_rut(self, rut: str) -> str:
        """
        Busca si el paciente tiene alguna interconsulta pendiente en la lista de espera.
        """
        for interconsulta in self.db.interconsultas.values():
            if interconsulta.rut_paciente == rut:
                ges_status = "ES GES" if interconsulta.es_ges else "NO ES GES"
                return (
                    f"INTERCONSULTA ENCONTRADA: ID: {interconsulta.id}, "
                    f"Problema: {interconsulta.problema_salud}, Estado: {interconsulta.estado}, "
                    f"Dias en espera: {interconsulta.dias_espera}, "
                    f"Prioridad: {interconsulta.prioridad}, {ges_status}"
                )
        return "RESULTADO: El paciente no registra interconsultas pendientes en la lista de espera."

    @is_tool(ToolType.WRITE)
    def create_appointment_reservation(self, id_interconsulta: str, slot_id: str) -> str:
        """
        Reserva un cupo hospitalario para una interconsulta especifica.
        """
        if id_interconsulta not in self.db.interconsultas:
            return "ERROR: El ID de interconsulta proporcionado no existe."
        if slot_id not in self.db.agenda_disponible:
            return "ERROR: El ID del cupo ya no esta disponible o es invalido."

        interconsulta = self.db.interconsultas[id_interconsulta]
        slot = self.db.agenda_disponible.pop(slot_id)
        if slot.especialidad != interconsulta.problema_salud:
            self.db.agenda_disponible[slot_id] = slot
            return (
                "ERROR: El cupo seleccionado no corresponde a la especialidad requerida "
                "por la interconsulta."
            )

        interconsulta.estado = "Agendado"
        return (
            f"RESERVA EXITOSA: La interconsulta {id_interconsulta} ha sido agendada "
            f"en {slot.hospital} para el {slot.fecha_hora}."
        )

    @is_tool(ToolType.WRITE)
    def update_interconsulta_as_resolved_externally(self, id_interconsulta: str) -> str:
        """
        Marca la interconsulta como resuelta externamente.
        """
        if id_interconsulta in self.db.interconsultas:
            self.db.interconsultas[id_interconsulta].estado = "Resuelto Externo"
            return (
                f"ACTUALIZACION: Interconsulta {id_interconsulta} marcada como "
                "Resuelta Externamente. Gracias por informar."
            )
        return "ERROR: No se pudo encontrar la interconsulta para actualizar."

    @is_tool(ToolType.WRITE)
    def cancel_interconsulta_by_unreachability(self, id_interconsulta: str) -> str:
        """
        Cancela o suspende una interconsulta por inubicabilidad.
        """
        if id_interconsulta in self.db.interconsultas:
            self.db.interconsultas[id_interconsulta].estado = "Inubicable"
            return (
                f"CIERRE DE CASO: La interconsulta {id_interconsulta} ha sido movida "
                "al registro de pacientes inubicables."
            )
        return "ERROR: ID de interconsulta no valida para cancelacion."

    @is_tool(ToolType.WRITE)
    def update_priority(
        self, id_interconsulta: str, nueva_prioridad: PrioridadInterconsulta
    ) -> str:
        """
        Actualiza la prioridad administrativa de una interconsulta.
        """
        if id_interconsulta not in self.db.interconsultas:
            return "ERROR: No se encontro la interconsulta para actualizar prioridad."

        self.db.interconsultas[id_interconsulta].prioridad = nueva_prioridad
        return (
            f"ACTUALIZACION: La interconsulta {id_interconsulta} ahora tiene prioridad "
            f"{nueva_prioridad}."
        )

    @is_tool(ToolType.READ)
    def get_available_hospital_slots(self, especialidad: str) -> str:
        """
        Consulta la agenda medica disponible para una especialidad.
        """
        slots = [
            slot
            for slot in self.db.agenda_disponible.values()
            if slot.especialidad.lower() == especialidad.lower()
        ]
        if not slots:
            return (
                f"CONSULTA: Actualmente no hay cupos disponibles para la especialidad: {especialidad}."
            )

        res = f"CUPOS DISPONIBLES PARA {especialidad.upper()}:\n"
        for slot in slots:
            res += (
                f"- ID Cupo: {slot.id} | Hospital: {slot.hospital} | "
                f"Fecha/Hora: {slot.fecha_hora}\n"
            )
        return res

    @is_tool(ToolType.GENERIC)
    def transfer_to_human_agents(self, summary: str) -> str:
        """
        Escala el caso a un agente humano cuando hay un reclamo agresivo o una
        situacion que requiere atencion manual.
        """
        return "YOU ARE BEING TRANSFERRED TO A HUMAN AGENT. PLEASE HOLD ON."
