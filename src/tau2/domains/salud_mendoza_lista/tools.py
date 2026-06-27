import hashlib

from tau2.domains.salud_mendoza_lista.data_model import SaludDB
from tau2.environment.toolkit import RAGToolKit, ToolType, is_tool


class SaludToolkit(RAGToolKit):
    def __init__(self, db: SaludDB = None, policy_index=None, retrieval_k=3):
        super().__init__(db, policy_index=policy_index, retrieval_k=retrieval_k)

    # ─────────────────────────────────────────────
    # HERRAMIENTAS ORIGINALES
    # ─────────────────────────────────────────────

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
        Requiere verificacion SMS previa.
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
        Cancela la interconsulta por inubicabilidad del paciente.
        Usar cuando el paciente no responde o es incoherente tras 2 intentos.
        """
        if id_interconsulta in self.db.interconsultas:
            self.db.interconsultas[id_interconsulta].estado = "Inubicable"
            return (
                f"CIERRE DE CASO: La interconsulta {id_interconsulta} ha sido movida "
                "al registro de pacientes inubicables."
            )
        return "ERROR: ID de interconsulta no valida para cancelacion."

    @is_tool(ToolType.WRITE)
    def update_priority(self, id_interconsulta: str, nueva_prioridad: str) -> str:
        """
        Actualiza la prioridad administrativa de una interconsulta.
        Valores validos: Normal, Alta, Urgente.
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
            return f"CONSULTA: Actualmente no hay cupos disponibles para la especialidad: {especialidad}."

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
        Escala el caso a un agente humano cuando hay un reclamo agresivo o
        una situacion que requiere atencion manual.
        """
        return "YOU ARE BEING TRANSFERRED TO A HUMAN AGENT. PLEASE HOLD ON."

    @is_tool(ToolType.READ)
    def get_interconsulta_details(self, rut: str) -> str:
        """
        Obtiene los detalles completos de la interconsulta activa de un paciente.
        """
        for interconsulta in self.db.interconsultas.values():
            if interconsulta.rut_paciente == rut:
                return (
                    f"INTERCONSULTA: ID: {interconsulta.id}, "
                    f"Problema: {interconsulta.problema_salud}, "
                    f"Estado: {interconsulta.estado}, "
                    f"Prioridad: {interconsulta.prioridad}, "
                    f"Dias en espera: {interconsulta.dias_espera}"
                )
        return f"RESULTADO: No se encontro interconsulta activa para el RUT {rut}."

    # ─────────────────────────────────────────────
    # HERRAMIENTAS SMS
    # ─────────────────────────────────────────────

    @is_tool(ToolType.WRITE)
    def send_sms_verification_code(self, rut: str) -> str:
        """
        Envia un codigo de verificacion de 6 digitos al telefono registrado del paciente.
        Debe llamarse ANTES de ejecutar operaciones sensibles.
        """
        paciente = self.db.pacientes.get(rut)
        if paciente is None:
            return f"ERROR: No se encontro un paciente con RUT {rut}."

        codigo = hashlib.md5(rut.encode()).hexdigest()[:6].upper()
        self.db.sms_verification_codes[rut] = codigo

        telefono = paciente.telefono or ""
        telefono_enmascarado = f"****{telefono[-4:]}" if len(telefono) >= 4 else "****"

        return (
            f"SMS ENVIADO: Se envio un codigo de verificacion de 6 digitos al numero "
            f"{telefono_enmascarado} registrado para el paciente. "
            f"Por favor solicite al paciente que lo proporcione."
        )

    @is_tool(ToolType.READ)
    def verify_sms_code(self, rut: str, codigo: str) -> str:
        """
        Verifica si el codigo SMS proporcionado por el paciente es correcto.
        """
        codigo_esperado = self.db.sms_verification_codes.get(rut)

        if codigo_esperado is None:
            return (
                "ERROR: No hay un codigo SMS activo para este RUT. "
                "Utilice send_sms_verification_code primero."
            )

        if codigo.strip().upper() == codigo_esperado:
            del self.db.sms_verification_codes[rut]
            return "VERIFICACION EXITOSA: Codigo correcto. Puede proceder con la operacion."
        else:
            return (
                "VERIFICACION FALLIDA: El codigo proporcionado no es correcto. "
                "Puede solicitar un nuevo codigo con send_sms_verification_code."
            )

    # ─────────────────────────────────────────────
    # HERRAMIENTAS RAG CLINICO
    # ─────────────────────────────────────────────

    @is_tool(ToolType.READ)
    def get_medico_details(self, codigo_medico: str) -> str:
        """
        Obtiene los datos de un medico de APS registrado en el sistema.
        """
        medico = self.db.medicos_aps.get(codigo_medico)
        if medico is None:
            return f"ERROR: No se encontro un medico con codigo {codigo_medico} en el sistema."
        return (
            f"MEDICO ENCONTRADO: {medico.nombre}, CESFAM: {medico.cesfam}, "
            f"Comuna: {medico.comuna}, Especialidad: {medico.especialidad}"
        )

    @is_tool(ToolType.READ)
    def search_derivation_protocol(self, especialidad: str, condicion: str) -> str:
        """
        Busca en la base de conocimiento el protocolo de derivacion vigente.
        SIEMPRE usar antes de informar requisitos de derivacion.
        """
        especialidad_lower = especialidad.lower().strip()
        condicion_lower = condicion.lower().strip()

        for protocolo in self.db.protocolos_derivacion.values():
            match_esp = especialidad_lower in protocolo.especialidad.lower()
            match_cond = condicion_lower in protocolo.condicion.lower()
            if match_esp and match_cond:
                examenes = "\n  - ".join(protocolo.examenes_requeridos)
                criterios = "\n  - ".join(protocolo.criterios_inclusion)
                contra = "\n  - ".join(protocolo.contraindicaciones)
                return (
                    f"PROTOCOLO ENCONTRADO: {protocolo.condicion} ({protocolo.especialidad})\n"
                    f"Nivel: {protocolo.nivel_derivacion}\n"
                    f"Criterios de inclusion:\n  - {criterios}\n"
                    f"Examenes requeridos:\n  - {examenes}\n"
                    f"Contraindicaciones:\n  - {contra}\n"
                    f"Tiempo garantizado: {protocolo.tiempo_respuesta_garantizado_dias} dias\n"
                    f"Notas: {protocolo.notas_adicionales or 'Ninguna'}"
                )

        for protocolo in self.db.protocolos_derivacion.values():
            if condicion_lower in protocolo.condicion.lower():
                examenes = "\n  - ".join(protocolo.examenes_requeridos)
                return (
                    f"PROTOCOLO ENCONTRADO (por condicion): {protocolo.condicion} "
                    f"({protocolo.especialidad})\n"
                    f"Examenes requeridos:\n  - {examenes}\n"
                    f"Tiempo garantizado: {protocolo.tiempo_respuesta_garantizado_dias} dias"
                )

        disponibles = ", ".join(
            f"{p.condicion} ({p.especialidad})"
            for p in self.db.protocolos_derivacion.values()
        )
        return (
            f"PROTOCOLO NO ENCONTRADO: No existe protocolo para '{condicion}' en '{especialidad}'. "
            f"Protocolos disponibles: {disponibles}"
        )

    @is_tool(ToolType.WRITE)
    def create_interconsulta_from_aps(
        self,
        codigo_medico: str,
        rut_paciente_referido: str,
        condicion: str,
        especialidad_destino: str,
        examenes_adjuntos: list,
        notas_clinicas: str = "",
    ) -> str:
        """
        Crea y envia una interconsulta desde un medico de APS al nivel secundario.
        Solo ejecutar si el medico confirmo que tiene todos los examenes requeridos.
        """
        medico = self.db.medicos_aps.get(codigo_medico)
        if medico is None:
            return f"ERROR: Medico {codigo_medico} no encontrado en el sistema."

        nuevo_id = f"IC-{len(self.db.interconsultas) + 1:03d}"
        from tau2.domains.salud_mendoza_lista.data_model import Interconsulta
        nueva_ic = Interconsulta(
            id=nuevo_id,
            rut_paciente=rut_paciente_referido,
            codigo_medico_derivador=codigo_medico,
            cesfam_origen=medico.cesfam,
            problema_salud=condicion,
            especialidad_destino=especialidad_destino,
            examenes_adjuntos=examenes_adjuntos,
            notas_clinicas=notas_clinicas,
            es_ges=True,
            dias_espera=0,
            estado="Enviada",
            prioridad="Normal",
        )
        self.db.interconsultas[nuevo_id] = nueva_ic

        return (
            f"INTERCONSULTA CREADA: ID {nuevo_id} enviada exitosamente. "
            f"Especialidad destino: {especialidad_destino}. "
            f"CESFAM origen: {medico.cesfam}."
        )