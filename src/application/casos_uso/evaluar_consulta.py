"""Caso de uso: evaluar una consulta de orientación (contracts/puertos.md)."""

import logging
from collections.abc import Sequence
from uuid import UUID

from application.ports.consulta_repository import ConsultaRepository
from application.ports.motor_inferencia import MotorInferencia
from domain.consulta import Consulta, ResultadoEvaluacion
from domain.mensajes_sistema import (
    ConfiguracionSalvaguarda,
    MensajeSistema,
    mensaje_combinacion_no_cubierta,
    mensaje_sintoma_no_cubierto,
)
from domain.resolucion_nivel import EstrategiaResolucionNivel, Resolucion
from domain.vocabulario import Medicamento, Vocabulario

logger = logging.getLogger(__name__)


class EvaluarConsulta:
    """Valida los hechos, los evalúa con el motor, resuelve el nivel y registra la consulta."""

    def __init__(
        self,
        vocabulario: Vocabulario,
        motor: MotorInferencia,
        estrategia: EstrategiaResolucionNivel,
        consultas: ConsultaRepository,
        salvaguarda: ConfiguracionSalvaguarda,
    ) -> None:
        self._vocabulario = vocabulario
        self._motor = motor
        self._estrategia = estrategia
        self._consultas = consultas
        self._salvaguarda = salvaguarda

    def ejecutar(
        self,
        medicamento: str | None,
        sintomas: Sequence[str],
        condiciones: Sequence[str],
    ) -> ResultadoEvaluacion:
        """Devuelve el resultado de la consulta; lanza VocabularioInvalido si los datos no valen."""
        hechos = self._vocabulario.validar(medicamento, sintomas, condiciones)
        resolucion = self._estrategia.resolver(hechos, self._motor.evaluar(hechos))
        mensajes_sistema = self._mensajes_sistema(resolucion, hechos.medicamento)
        consulta_id = self._registrar(
            Consulta(
                hechos=hechos,
                nivel=resolucion.nivel,
                sin_regla=resolucion.sin_regla,
                reglas_disparadas=resolucion.reglas_disparadas,
            )
        )
        return ResultadoEvaluacion(
            nivel=resolucion.nivel,
            sin_regla=resolucion.sin_regla,
            reglas_disparadas=resolucion.reglas_disparadas,
            sintomas_no_cubiertos=resolucion.sintomas_no_cubiertos,
            mensajes_sistema=mensajes_sistema,
            persistida=consulta_id is not None,
            consulta_id=consulta_id,
        )

    def _registrar(self, consulta: Consulta) -> UUID | None:
        """Guarda la consulta; si falla por un error técnico, lo registra y devuelve None.

        Única excepción a la persistencia del Principio III (FR-019): el resultado se muestra
        igual. El detalle del error va al log, donde FiltroSecretos lo sanea.
        """
        try:
            return self._consultas.guardar(consulta)
        except Exception as error:
            logger.error(
                "No se pudo persistir la consulta",
                exc_info=True,
                extra={"tipo_error": type(error).__name__},
            )
            return None

    def _mensajes_sistema(
        self, resolucion: Resolucion, medicamento: Medicamento
    ) -> tuple[MensajeSistema, ...]:
        """Devuelve los mensajes del sistema; nunca mezcla los dos tipos (FR-011, FR-020)."""
        if resolucion.sin_regla:
            return (mensaje_combinacion_no_cubierta(),)
        return tuple(
            mensaje_sintoma_no_cubierto(sintoma, medicamento, self._salvaguarda)
            for sintoma in resolucion.sintomas_no_cubiertos
        )
