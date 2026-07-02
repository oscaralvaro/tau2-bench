from tau2.environment.toolkit import RAGToolKit, is_tool, ToolType
from .data_model import HealthcareDB, BloqueAgenda
from typing import List


class HealthcareToolkit(RAGToolKit):

    def __init__(
        self,
        db: HealthcareDB,
        policy_index=None,
        retrieval_k: int = 3,
    ):
        super().__init__(
            db,
            policy_index=policy_index,
            retrieval_k=retrieval_k,
        )

    # -------------------------
    # CONSULTAS
    # -------------------------
    @is_tool(ToolType.READ) 
    def get_paciente(self, rut: str):
        """Obtiene un paciente por RUT"""
        return self.db.pacientes.get(rut)
    @is_tool(ToolType.READ)
    def get_interconsultas(self, rut: str):
        """Lista interconsultas de un paciente"""
        return [
            ic for ic in self.db.interconsultas.values()
            if ic.rut_paciente == rut
        ]
    @is_tool(ToolType.READ)
    def get_registros_clinicos(self, rut: str):
        """Obtiene registros clínicos del paciente"""
        return [
            r for r in self.db.registros_clinicos.values()
            if r.rut_paciente == rut
        ]

    # -------------------------
    # VALIDACIONES
    # -------------------------
    @is_tool(ToolType.READ)
    def validar_prevision(self, rut: str):
        """Verifica si el paciente es FONASA"""
        paciente = self.db.pacientes.get(rut)
        if not paciente:
            return False
        return paciente.prevision == "FONASA"

    @is_tool(ToolType.READ)
    def validar_inscripcion(self, rut: str):
        """Verifica si el paciente está inscrito en CESFAM"""
        paciente = self.db.pacientes.get(rut)
        if not paciente:
            return False
        return paciente.inscrito

    @is_tool(ToolType.READ)
    def validar_interconsulta(self, rut: str):
        """Verifica si el paciente tiene interconsulta válida"""
        for ic in self.db.interconsultas.values():
            if ic.rut_paciente == rut and ic.estado in ["validada", "pendiente_examenes", "enviada"]:
                return True
        return False
    
    @is_tool(ToolType.READ)
    def get_bloques_disponibles(self, tipo: str | None = None):
        """Obtiene los bloques de agenda disponibles."""

        bloques = [
            b for b in self.db.bloques_agenda.values()
            if b.estado_cupo == "disponible"
        ]  

        if tipo is not None:
            bloques = [
               b for b in bloques
               if b.tipo_prestacion == tipo
        ]

        return bloques

    # -------------------------
    # ACCIONES
    # -------------------------
    @is_tool(ToolType.WRITE)
    def agendar_bloque(self, bloque_id: str, tipo: str, profesionales: List[str]):
        """Agenda un bloque multiprofesional"""

        nuevo_bloque = BloqueAgenda(
            id=bloque_id,
            tipo_prestacion=tipo,
            profesionales=profesionales,
            duracion=60,
            estado_cupo="reservado"
        )

        self.db.bloques_agenda[bloque_id] = nuevo_bloque
        return f"Bloque {bloque_id} agendado correctamente"

    @is_tool(ToolType.WRITE)
    def cancelar_bloque(self, bloque_id: str):
        """Cancela un bloque existente"""
        bloque = self.db.bloques_agenda.get(bloque_id)
        if not bloque:
            return None

        bloque.estado_cupo = "disponible"
        return bloque
    
    @is_tool(ToolType.WRITE)
    def enviar_codigo_sms(self, rut: str):
        """Genera un código SMS determinístico para verificación"""
        paciente = self.db.pacientes.get(rut)

        if not paciente:
            return None

        codigo = rut.split("-")[0][:4]

        return {
            "rut": rut,
            "codigo_generado": codigo,
            "mensaje": f"SMS enviado al paciente {rut}"
        }
    
    @is_tool(ToolType.READ)
    def verificar_codigo_sms(self, rut: str, codigo: str):
        """Verifica código SMS determinístico"""

        codigo_correcto = rut.split("-")[0][:4]

        return codigo == codigo_correcto