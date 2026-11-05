"""Caso de uso: evaluar una consulta de orientación (contracts/puertos.md)."""

from collections.abc import Sequence

from application.ports.consulta_repository import ConsultaRepository
from application.ports.motor_inferencia import MotorInferencia
from domain.consulta import Consulta, ResultadoEvaluacion
from domain.mensajes_sistema import ConfiguracionSalvaguarda, mensaje_sintoma_no_cubierto
from domain.resolucion_nivel import EstrategiaResolucionNivel
from domain.vocabulario import Vocabulario


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
        mensajes_sistema = tuple(
            mensaje_sintoma_no_cubierto(sintoma, hechos.medicamento, self._salvaguarda)
            for sintoma in resolucion.sintomas_no_cubiertos
        )
        consulta_id = self._consultas.guardar(
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
            persistida=True,
            consulta_id=consulta_id,
        )
