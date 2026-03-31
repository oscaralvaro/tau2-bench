"""Toolkit for the CLC validation system."""

from typing import List

from tau2.domains.ConvalidacionCLCs_Coronado.data_model import (
    ConvalidacionCLCDB,
    EstadoSolicitud,
    Estudiante,
    ProgramaAcademico,
    Solicitud,
)
from tau2.domains.ConvalidacionCLCs_Coronado.utils import (
    CONVALIDACION_TRANSFER_MESSAGE,
)
from tau2.environment.toolkit import ToolKitBase, ToolType, is_tool


class ConvalidacionCLCTools(ToolKitBase):
    """All tools available for the CLC validation domain."""

    db: ConvalidacionCLCDB

    def __init__(self, db: ConvalidacionCLCDB) -> None:
        super().__init__(db)

    def _get_new_request_id(self) -> str:
        """Generate a deterministic unique Request ID."""
        alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        existing_ids = {solicitud.request_id for solicitud in self.db.solicitudes}
        next_index = len(self.db.solicitudes)

        while True:
            value = next_index
            suffix = ""
            for _ in range(4):
                value, remainder = divmod(value, len(alphabet))
                suffix = alphabet[remainder] + suffix

            request_id = f"REQ-{suffix}"
            if request_id not in existing_ids:
                return request_id
            next_index += 1

    def _find_estudiante(self, carnet: str) -> Estudiante:
        for estudiante in self.db.estudiantes:
            if estudiante.carnet == carnet:
                return estudiante
        raise ValueError(f"Estudiante con carnet {carnet} no encontrado.")

    @staticmethod
    def _normalize_text(value: str) -> str:
        return " ".join(value.strip().upper().split())

    @is_tool(ToolType.READ)
    def get_estudiante_details(self, carnet: str) -> Estudiante:
        """Obtener los datos de un estudiante, incluidos sus CLCs validados."""
        return self._find_estudiante(carnet)

    @is_tool(ToolType.READ)
    def listar_actividades_preaprobadas(
        self, programa: ProgramaAcademico
    ) -> List[str]:
        """Listar actividades preaprobadas para el programa indicado."""
        activities: list[str] = []
        if programa in self.db.congresos_preaprobados:
            activities.extend(self.db.congresos_preaprobados[programa])
        if programa == "ARQ":
            activities.extend(self.db.bienales_arquitectura)
        return activities

    @is_tool(ToolType.READ)
    def verificar_pago_derecho_academico(self, carnet: str, actividad: str) -> bool:
        """Verificar si existe pago academico confirmado para una actividad."""
        actividad_normalizada = self._normalize_text(actividad)
        for pago in self.db.pagos_derecho_academico:
            if (
                pago.carnet == carnet
                and self._normalize_text(pago.actividad) == actividad_normalizada
            ):
                return pago.pagado
        return False

    @is_tool(ToolType.WRITE)
    def crear_solicitud(
        self,
        carnet: str,
        nombre_completo: str,
        programa: ProgramaAcademico,
        actividad: str,
        evaluado_con_nota: bool,
        clc: int,
        archivo: str,
        status: EstadoSolicitud,
    ) -> Solicitud:
        """Crear una nueva solicitud de convalidacion con Request ID unico."""
        request_id = self._get_new_request_id()
        nueva_solicitud = Solicitud(
            request_id=request_id,
            carnet=carnet,
            nombre_completo=nombre_completo,
            programa=programa,
            actividad=actividad,
            evaluado_con_nota=evaluado_con_nota,
            clc=clc,
            archivo=archivo,
            status=status,
        )
        self.db.solicitudes.append(nueva_solicitud)

        if status == "APPROVED":
            estudiante = self._find_estudiante(carnet)
            if clc not in estudiante.clcs_validados:
                estudiante.clcs_validados.append(clc)

        return nueva_solicitud

    @is_tool(ToolType.READ)
    def consultar_estado_solicitud(self, request_id: str) -> Solicitud:
        """Consultar una solicitud existente por su Request ID."""
        for solicitud in self.db.solicitudes:
            if solicitud.request_id == request_id:
                return solicitud
        raise ValueError(f"Solicitud con ID {request_id} no encontrada.")

    @is_tool(ToolType.GENERIC)
    def transfer_to_human_agent(self, summary: str) -> str:
        """Transferir el caso a un agente humano."""
        return CONVALIDACION_TRANSFER_MESSAGE
