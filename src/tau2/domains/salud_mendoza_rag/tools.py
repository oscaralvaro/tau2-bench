from tau2.domains.salud_mendoza_rag.data_model import SaludMendozaRAGDB
from tau2.environment.toolkit import ToolKitBase, ToolType, is_tool


class SaludRAGToolkit(ToolKitBase):
    def __init__(self, db: SaludMendozaRAGDB):
        super().__init__(db)

    @is_tool(ToolType.READ)
    def buscar_protocolo_rag(self, diagnostico: str) -> str:
        """Busca los examenes requeridos para un diagnostico segun protocolo."""
        diagnostico_normalizado = diagnostico.strip().lower()
        for protocolo in self.db.protocolos.values():
            if diagnostico_normalizado in protocolo.diagnostico.lower():
                requeridos = ", ".join(
                    examen.nombre for examen in protocolo.examenes_requeridos
                )
                return (
                    f"Protocolo para {protocolo.diagnostico}: "
                    f"Requiere {requeridos}. Ref: {protocolo.link_referencia}"
                )
        return "No se encontro un protocolo especifico para ese diagnostico."

    @is_tool(ToolType.WRITE)
    def validar_interconsulta(self, id_solicitud: str) -> str:
        """Valida si la solicitud cumple con los examenes obligatorios del protocolo."""
        solicitud = self.db.solicitudes.get(id_solicitud)
        if solicitud is None:
            return "Solicitud no encontrada."

        protocolo = next(
            (
                item
                for item in self.db.protocolos.values()
                if item.diagnostico == solicitud.diagnostico_sospecha
            ),
            None,
        )
        if protocolo is None:
            return "No hay un protocolo de validacion cargado para este diagnostico."

        examenes_adjuntos = {examen.strip().lower() for examen in solicitud.examenes_adjuntos}
        faltantes = [
            examen.nombre
            for examen in protocolo.examenes_requeridos
            if examen.nombre.strip().lower() not in examenes_adjuntos
        ]

        if faltantes:
            solicitud.estado = "Rechazada por Protocolo"
            return (
                "VALIDACION FALLIDA: Faltan los siguientes examenes obligatorios: "
                + ", ".join(faltantes)
            )

        solicitud.estado = "Validada"
        return "VALIDACION EXITOSA: La solicitud cumple los requisitos y puede ser enviada."

    @is_tool(ToolType.WRITE)
    def adjuntar_examen_a_solicitud(self, id_solicitud: str, nombre_examen: str) -> str:
        """Adjunta un examen a una solicitud antes de validar."""
        solicitud = self.db.solicitudes.get(id_solicitud)
        if solicitud is None:
            return "Solicitud no encontrada."

        examen_normalizado = nombre_examen.strip()
        ya_adjuntos = {examen.strip().lower() for examen in solicitud.examenes_adjuntos}
        if examen_normalizado.lower() in ya_adjuntos:
            return "El examen ya estaba adjunto."

        solicitud.examenes_adjuntos.append(examen_normalizado)
        return (
            f"Examen '{examen_normalizado}' adjuntado con exito a la solicitud {id_solicitud}."
        )

    @is_tool(ToolType.GENERIC)
    def transfer_to_human_agents(self, summary: str) -> str:
        """
        Escala el caso a un supervisor humano cuando el medico insiste en incumplir
        el protocolo o cuando la solicitud no puede cursarse de forma segura.
        """
        return "YOU ARE BEING TRANSFERRED TO A HUMAN AGENT. PLEASE HOLD ON."
