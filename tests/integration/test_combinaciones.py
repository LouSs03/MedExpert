"""Las 16.128 combinaciones posibles: CLIPS + estrategia == oráculo de la spec (lenta).

2 medicamentos por 63 subconjuntos no vacíos de síntomas por 128 subconjuntos de condiciones.
El oráculo se escribe aquí, directamente desde FR-006, FR-009 y FR-020, sin usar el código bajo
prueba. Solo usa la base de pruebas (FR-021).
"""

from collections.abc import Iterator
from itertools import combinations
from typing import Any

import pytest
from sqlalchemy import Engine

from api.esquemas import a_resultado_dto
from application.casos_uso.cargar_base_conocimiento import CargarBaseConocimiento
from application.casos_uso.evaluar_consulta import EvaluarConsulta
from domain.base_conocimiento import BaseConocimiento
from domain.consulta import Consulta
from domain.mensajes_sistema import ConfiguracionSalvaguarda
from domain.regla import Regla
from domain.resolucion_nivel import ResolucionPorSeveridad
from infrastructure.db.postgres_regla_repository import PostgresReglaRepository
from infrastructure.inference.clips_motor_inferencia import ClipsMotorInferencia
from infrastructure.inference.fabrica_entorno import FabricaEntornoClips

pytestmark = [pytest.mark.integration, pytest.mark.lento]

SEVERIDAD = {"ORIENTAR": 1, "ADVERTIR": 2, "DERIVAR": 3}
TIPOS_SISTEMA = {"COMBINACION_NO_CUBIERTA", "SINTOMA_NO_CUBIERTO"}


class RegistroNulo:
    """No guarda nada: esta prueba solo compara razonamiento."""

    def guardar(self, consulta: Consulta) -> Any:
        return None


def _subconjuntos(elementos: list[str], minimo: int) -> Iterator[list[str]]:
    for tamano in range(minimo, len(elementos) + 1):
        yield from (list(c) for c in combinations(elementos, tamano))


def _oraculo(
    reglas: tuple[Regla, ...], med: str, sintomas: set[str], condiciones: set[str]
) -> tuple[str, bool, list[str], list[str]]:
    """Nivel, sin_regla, códigos en orden y síntomas no cubiertos según la spec."""
    disparadas = [
        r
        for r in reglas
        if r.medicamento == med
        and r.sintomas <= sintomas
        and r.condiciones <= condiciones
        and not (r.sin_condiciones and condiciones)
    ]
    if not disparadas:
        return "DERIVAR", True, [], []
    disparadas.sort(key=lambda r: (-SEVERIDAD[r.nivel.value], -r.especificidad, r.codigo))
    cubiertos = set().union(*(r.sintomas for r in disparadas))
    no_cubiertos = sorted(sintomas - cubiertos)
    nivel = max(SEVERIDAD[r.nivel.value] for r in disparadas)
    if no_cubiertos:
        nivel = max(nivel, SEVERIDAD["ADVERTIR"])
    etiqueta = next(k for k, v in SEVERIDAD.items() if v == nivel)
    return etiqueta, False, [r.codigo for r in disparadas], no_cubiertos


@pytest.fixture(scope="module")
def base(engine_pruebas: Engine) -> BaseConocimiento:
    return CargarBaseConocimiento(PostgresReglaRepository(engine_pruebas)).ejecutar()


def test_16128_combinaciones_coinciden_con_el_oraculo(base: BaseConocimiento) -> None:
    evaluar = EvaluarConsulta(
        vocabulario=base.vocabulario,
        motor=ClipsMotorInferencia(FabricaEntornoClips(base.reglas)),
        estrategia=ResolucionPorSeveridad(),
        consultas=RegistroNulo(),
        salvaguarda=ConfiguracionSalvaguarda(),
    )
    aprobados = {r.codigo: set(r.mensajes) for r in base.reglas}
    medicamentos = [m.codigo for m in base.vocabulario.medicamentos]
    sintomas = [s.codigo for s in base.vocabulario.sintomas]
    condiciones = [c.codigo for c in base.vocabulario.condiciones]

    total = 0
    discrepancias: list[str] = []
    for med in medicamentos:
        for sin in _subconjuntos(sintomas, 1):
            for con in _subconjuntos(condiciones, 0):
                total += 1
                resultado = evaluar.ejecutar(med, sin, con)
                dto = a_resultado_dto(resultado)
                obtenido = (
                    dto.nivel,
                    dto.sin_regla,
                    [r.codigo for r in dto.reglas_aplicadas],
                    sorted(s.codigo for s in dto.sintomas_no_cubiertos),
                )
                esperado = _oraculo(base.reglas, med, set(sin), set(con))
                caso = f"{med} {sin} {con}"
                if obtenido != esperado:
                    discrepancias.append(f"{caso}: {obtenido} != {esperado}")
                # SC-009: síntoma no cubierto con reglas disparadas nunca termina en Orientar.
                if dto.sintomas_no_cubiertos and dto.nivel == "ORIENTAR":
                    discrepancias.append(f"{caso}: salvaguarda en Orientar")
                # SC-003 / FR-012: todo mensaje es de una regla disparada o del sistema.
                for regla in dto.reglas_aplicadas:
                    if not set(regla.mensajes) <= aprobados[regla.codigo]:
                        discrepancias.append(f"{caso}: mensaje no aprobado en {regla.codigo}")
                if {m.tipo for m in dto.mensajes_sistema} - TIPOS_SISTEMA:
                    discrepancias.append(f"{caso}: mensaje del sistema desconocido")
                if dto.sin_regla != any(
                    m.tipo == "COMBINACION_NO_CUBIERTA" for m in dto.mensajes_sistema
                ):
                    discrepancias.append(f"{caso}: mensaje de no cubierta incoherente")

    assert total == 16_128
    assert discrepancias == [], f"{len(discrepancias)} discrepancias; primeras: {discrepancias[:5]}"
