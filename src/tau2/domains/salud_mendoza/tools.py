from tau2.domains.salud_mendoza.data_model import (
    DiagnosticoRAG,
    PrioridadInterconsulta,
    SaludMendozaDB,
)
from tau2.environment.toolkit import ToolKitBase, ToolType, is_tool


class SaludMendozaToolkit(ToolKitBase):
    def __init__(self, db: SaludMendozaDB):
        super().__init__(db)

    @is_tool(ToolType.READ)
    def get_patient_details(self, rut: str) -> str:
        paciente = self.db.pacientes.get(rut)
        if paciente:
            return (
                f"DATOS ENCONTRADOS: Nombre: {paciente.nombre}, RUT: {paciente.rut}, "
                f"Prevision: {paciente.prevision}, Comuna: {paciente.comuna}"
            )
        return "ERROR: El RUT ingresado no existe en el registro civil simulado."

    @is_tool(ToolType.READ)
    def search_waiting_list_by_rut(self, rut: str) -> str:
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
        if id_interconsulta in self.db.interconsultas:
            self.db.interconsultas[id_interconsulta].estado = "Resuelto Externo"
            return (
                f"ACTUALIZACION: Interconsulta {id_interconsulta} marcada como "
                "Resuelta Externamente. Gracias por informar."
            )
        return "ERROR: No se pudo encontrar la interconsulta para actualizar."

    @is_tool(ToolType.WRITE)
    def cancel_interconsulta_by_unreachability(self, id_interconsulta: str) -> str:
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
        if id_interconsulta not in self.db.interconsultas:
            return "ERROR: No se encontro la interconsulta para actualizar prioridad."

        self.db.interconsultas[id_interconsulta].prioridad = nueva_prioridad
        return (
            f"ACTUALIZACION: La interconsulta {id_interconsulta} ahora tiene prioridad "
            f"{nueva_prioridad}."
        )

    @is_tool(ToolType.READ)
    def get_available_hospital_slots(self, especialidad: str) -> str:
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

    @is_tool(ToolType.READ)
    def get_referral_requirements(self, diagnostico: DiagnosticoRAG) -> str:
        protocolo = next(
            (
                item
                for item in self.db.protocolos_rag.values()
                if item.diagnostico == diagnostico
            ),
            None,
        )
        if protocolo is None:
            return "ERROR: No existe protocolo cargado para ese diagnostico."

        obligatorios = ", ".join(protocolo.examenes_obligatorios) or "ninguno"
        sugeridos = ", ".join(protocolo.examenes_sugeridos) or "ninguno"
        signos_alarma = ", ".join(protocolo.signos_alarma) or "ninguno"
        plazo = protocolo.plazo_referencia or "No especificado"
        return (
            f"PROTOCOLO: {protocolo.diagnostico}. "
            f"Examenes obligatorios: {obligatorios}. "
            f"Examenes sugeridos: {sugeridos}. "
            f"Signos de alarma: {signos_alarma}. "
            f"Ruta asistencial: {protocolo.ruta_asistencial}. "
            f"Plazo de referencia: {plazo}."
        )

    @is_tool(ToolType.READ)
    def review_referral_request(self, solicitud_id: str) -> str:
        solicitud = self.db.solicitudes_interconsulta.get(solicitud_id)
        if solicitud is None:
            return "ERROR: La solicitud no existe."

        protocolo = next(
            (
                item
                for item in self.db.protocolos_rag.values()
                if item.diagnostico == solicitud.diagnostico_sospecha
            ),
            None,
        )
        if protocolo is None:
            return "ERROR: No existe protocolo para revisar esta solicitud."

        examenes_presentados = {item.lower() for item in solicitud.examenes_presentados}
        faltantes = [
            examen
            for examen in protocolo.examenes_obligatorios
            if examen.lower() not in examenes_presentados
        ]
        signos_alarma = {signo.lower() for signo in protocolo.signos_alarma}
        alertas = [
            alerta for alerta in solicitud.sintomas_alerta if alerta.lower() in signos_alarma
        ]

        estado = "COMPLETA"
        if faltantes:
            estado = "INCOMPLETA"
        if alertas:
            estado = "URGENTE"

        faltantes_txt = ", ".join(faltantes) if faltantes else "ninguno"
        alertas_txt = ", ".join(alertas) if alertas else "ninguno"
        presentados_txt = ", ".join(solicitud.examenes_presentados) or "ninguno"
        return (
            f"REVISION {estado}: Solicitud {solicitud.id} para {solicitud.diagnostico_sospecha}. "
            f"Examenes presentados: {presentados_txt}. "
            f"Examenes faltantes: {faltantes_txt}. "
            f"Signos de alarma detectados: {alertas_txt}. "
            f"Ruta sugerida: {protocolo.ruta_asistencial}."
        )

    @is_tool(ToolType.WRITE)
    def approve_referral_request(self, solicitud_id: str) -> str:
        solicitud = self.db.solicitudes_interconsulta.get(solicitud_id)
        if solicitud is None:
            return "ERROR: La solicitud no existe."

        revision = self.review_referral_request(solicitud_id)
        if "URGENTE" in revision:
            return "ERROR: La solicitud presenta signos de alarma y no puede aprobarse como electiva."
        if "INCOMPLETA" in revision:
            solicitud.estado_revision = "Observada"
            return "OBSERVACION: La solicitud sigue incompleta y no puede aprobarse."

        solicitud.estado_revision = "Lista para Derivacion"
        return (
            f"APROBACION: La solicitud {solicitud_id} quedo lista para derivacion "
            "segun protocolo."
        )

    @is_tool(ToolType.WRITE)
    def escalate_referral_to_emergency(self, solicitud_id: str) -> str:
        solicitud = self.db.solicitudes_interconsulta.get(solicitud_id)
        if solicitud is None:
            return "ERROR: La solicitud no existe."

        solicitud.estado_revision = "Derivar a Urgencias"
        return (
            f"ESCALAMIENTO: La solicitud {solicitud_id} fue marcada para derivacion "
            "inmediata a urgencias oftalmologicas."
        )

    @is_tool(ToolType.GENERIC)
    def transfer_to_human_agents(self, summary: str) -> str:
        return "YOU ARE BEING TRANSFERRED TO A HUMAN AGENT. PLEASE HOLD ON."
