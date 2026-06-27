"""Toolkit for the CLC validation system."""

from typing import Any, List, Optional

from tau2.domains.ConvalidacionCLCs_Coronado.data_model import (
    CertificadoPDF,
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

    def _find_certificado_pdf(
        self, carnet: str, actividad: str
    ) -> Optional[CertificadoPDF]:
        actividad_normalizada = self._normalize_text(actividad)
        for certificado in self.db.certificados_pdf:
            if (
                certificado.carnet == carnet
                and self._normalize_text(certificado.actividad) == actividad_normalizada
            ):
                return certificado
        return None

    @staticmethod
    def _normalize_text(value: str) -> str:
        return " ".join(value.strip().upper().split())

    @staticmethod
    def _get_max_clcs(programa: ProgramaAcademico) -> int:
        if programa == "ARQ":
            return 8
        return 4

    @staticmethod
    def _clc_id(clc: int) -> str:
        return f"clc{clc}"

    @staticmethod
    def _get_clcs_permitidos_por_categoria(
        programa: ProgramaAcademico, categoria_actividad: str
    ) -> list[int]:
        categoria = " ".join(categoria_actividad.strip().upper().split())

        if programa == "ARQ":
            mapping = {
                "INTERCAMBIO ESTUDIANTIL": list(range(1, 9)),
                "EXTENSION": list(range(1, 9)),
                "VIDA UNIVERSITARIA": [7, 8],
                "ACTIVIDADES EXTERNAS": [5, 6, 7, 8],
                "CONGRESOS": [7, 8],
                "BIENALES": [7, 8],
                "CONGRESOS/BIENALES": [7, 8],
            }
        else:
            mapping = {
                "INTERCAMBIO ESTUDIANTIL": [1, 2, 3, 4],
                "EXTENSION": [1, 2, 3, 4],
                "EXTENSION (FACULTAD DE INGENIERIA)": [1, 2, 3, 4],
                "VIDA UNIVERSITARIA": [3, 4],
                "ACTIVIDADES EXTERNAS": [3, 4],
                "CONGRESOS": [3, 4],
            }

        if categoria not in mapping:
            raise ValueError(
                "Categoria de actividad no reconocida. "
                "Use una categoria definida en la politica del dominio."
            )

        return mapping[categoria]

    @is_tool(ToolType.READ)
    def get_estudiante_details(self, carnet: str) -> Estudiante:
        """Obtener los datos de un estudiante, incluidos sus CLCs validados."""
        return self._find_estudiante(carnet)

    @is_tool(ToolType.READ)
    def get_estudiante_clc_status(self, carnet: str) -> dict[str, Any]:
        """Obtener el estado de CLCs del estudiante, incluyendo cupo restante."""
        estudiante = self._find_estudiante(carnet)
        max_clcs = self._get_max_clcs(estudiante.programa)
        clcs_validados = sorted(set(estudiante.clcs_validados))
        clcs_disponibles = [
            clc for clc in range(1, max_clcs + 1) if clc not in clcs_validados
        ]
        return {
            "carnet": estudiante.carnet,
            "programa": estudiante.programa,
            "clcs_validados": clcs_validados,
            "clcs_validados_ids": [self._clc_id(clc) for clc in clcs_validados],
            "cantidad_clcs_validados": estudiante.cantidad_clcs_validados,
            "maximo_clcs": max_clcs,
            "clcs_disponibles": clcs_disponibles,
            "clcs_disponibles_ids": [self._clc_id(clc) for clc in clcs_disponibles],
            "tiene_todos_los_clcs": len(clcs_disponibles) == 0,
        }

    @is_tool(ToolType.READ)
    def get_clcs_permitidos_para_actividad(
        self, programa: ProgramaAcademico, categoria_actividad: str
    ) -> dict[str, Any]:
        """Obtener los CLCs permitidos segun el programa y la categoria de actividad."""
        clcs_permitidos = self._get_clcs_permitidos_por_categoria(
            programa, categoria_actividad
        )
        return {
            "programa": programa,
            "categoria_actividad": categoria_actividad,
            "clcs_permitidos": clcs_permitidos,
            "clcs_permitidos_ids": [self._clc_id(clc) for clc in clcs_permitidos],
        }

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

    @is_tool(ToolType.READ)
    def verificar_horas_certificado(self, carnet: str, actividad: str) -> dict[str, Any]:
        """Verificar las horas registradas en el certificado PDF de una actividad."""
        certificado = self._find_certificado_pdf(carnet, actividad)
        if certificado is not None:
            return {
                "carnet": certificado.carnet,
                "actividad": certificado.actividad,
                "horas_pdf": certificado.horas_pdf,
            }

        actividad_normalizada = self._normalize_text(actividad)
        for registro in self.db.horas_certificados:
            if (
                registro.carnet == carnet
                and self._normalize_text(registro.actividad) == actividad_normalizada
            ):
                return {
                    "carnet": registro.carnet,
                    "actividad": registro.actividad,
                    "horas_pdf": registro.horas_pdf,
                }
        raise ValueError(
            f"No se encontraron horas registradas en el certificado para el carnet {carnet} y la actividad '{actividad}'."
        )

    @is_tool(ToolType.READ)
    def verificar_detalles_certificado(
        self, carnet: str, actividad: str
    ) -> dict[str, Any]:
        """Obtener los datos verificables del certificado PDF, incluyendo nota y campos requeridos."""
        certificado = self._find_certificado_pdf(carnet, actividad)
        if certificado is None:
            raise ValueError(
                f"No se encontraron metadatos del certificado PDF para el carnet {carnet} y la actividad '{actividad}'."
            )

        nota_aprobatoria = (
            certificado.incluye_nota
            and certificado.nota is not None
            and certificado.nota > 11
        )
        campos_obligatorios_presentes = all(
            [
                certificado.incluye_carnet,
                certificado.incluye_nombre_actividad,
                certificado.incluye_tipo_actividad,
                certificado.incluye_horas_totales,
            ]
        )

        return {
            "carnet": certificado.carnet,
            "actividad": certificado.actividad,
            "tipo_actividad": certificado.tipo_actividad,
            "horas_pdf": certificado.horas_pdf,
            "incluye_carnet": certificado.incluye_carnet,
            "incluye_nombre_actividad": certificado.incluye_nombre_actividad,
            "incluye_tipo_actividad": certificado.incluye_tipo_actividad,
            "incluye_horas_totales": certificado.incluye_horas_totales,
            "incluye_nota": certificado.incluye_nota,
            "nota": certificado.nota,
            "campos_obligatorios_presentes": campos_obligatorios_presentes,
            "nota_aprobatoria": nota_aprobatoria,
        }

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
        horas_declaradas: int,
        status: EstadoSolicitud,
        nota: Optional[int] = None,
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
            nota=nota,
            clc=clc,
            archivo=archivo,
            horas_declaradas=horas_declaradas,
            status=status,
        )
        self.db.solicitudes.append(nueva_solicitud)

        if status == "APPROVED":
            estudiante = self._find_estudiante(carnet)
            if clc not in estudiante.clcs_validados:
                estudiante.clcs_validados.append(clc)
                estudiante.clcs_validados = sorted(set(estudiante.clcs_validados))
                estudiante.clcs_validados_ids = [
                    self._clc_id(clc_number) for clc_number in estudiante.clcs_validados
                ]
                estudiante.cantidad_clcs_validados = len(estudiante.clcs_validados)

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
