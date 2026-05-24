from tau2.environment.toolkit import ToolKitBase, is_tool, ToolType
from .data_model import HealthcareDB, BloqueAgenda
from typing import List


class HealthcareToolkit(ToolKitBase):

    def __init__(self, db: HealthcareDB):
        self.db = db

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
        return f"Bloque {bloque_id} cancelado correctamente"