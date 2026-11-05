"""Motor CLIPS real con reglas de ejemplo: FR-006, aislamiento (FR-016), concurrencia (SC-008)."""

from concurrent.futures import ThreadPoolExecutor

import pytest

from domain.vocabulario import HechosConsulta
from fakes.reglas_ejemplo import (
    DOLOR_CABEZA,
    DOLOR_DENTAL,
    EMBARAZO,
    FIEBRE,
    HIPERTENSION,
    IBUPROFENO,
    PARACETAMOL,
    REGLAS_EJEMPLO,
    USO_ASPIRINA,
    VOCABULARIO,
)
from infrastructure.inference.clips_motor_inferencia import ClipsMotorInferencia
from infrastructure.inference.fabrica_entorno import FabricaEntornoClips

FABRICA = FabricaEntornoClips(REGLAS_EJEMPLO)
MOTOR = ClipsMotorInferencia(FABRICA)


def _codigos(med: str, sintomas: list[str], condiciones: list[str]) -> set[str]:
    hechos = VOCABULARIO.validar(med, sintomas, condiciones)
    return {r.codigo for r in MOTOR.evaluar(hechos)}


def test_dispara_cuando_estan_todos_los_hechos() -> None:
    assert _codigos("PARACETAMOL", ["DOLOR_CABEZA"], []) == {"R01"}
    assert _codigos("PARACETAMOL", ["DOLOR_CABEZA"], ["EMBARAZO"]) == {"R10"}


def test_no_dispara_si_falta_un_hecho() -> None:
    assert _codigos("PARACETAMOL", ["DOLOR_DENTAL"], []) == set()
    assert _codigos("IBUPROFENO", ["FIEBRE"], []) == set()


def test_los_hechos_de_mas_no_bloquean() -> None:
    assert _codigos("PARACETAMOL", ["DOLOR_CABEZA", "FIEBRE"], []) == {"R01", "R02", "R07"}
    assert _codigos("PARACETAMOL", ["FIEBRE", "DOLOR_DENTAL"], ["EMBARAZO", "DIABETES"]) == {"R11"}


@pytest.mark.parametrize("condicion", ["EMBARAZO", "HIPERTENSION", "USO_ASPIRINA"])
def test_regla_sin_condiciones_no_dispara_con_cualquier_condicion(condicion: str) -> None:
    disparadas = _codigos("PARACETAMOL", ["DOLOR_CABEZA"], [condicion])

    assert "R01" not in disparadas


def test_el_medicamento_debe_coincidir() -> None:
    assert _codigos("IBUPROFENO", ["DOLOR_CABEZA"], []) == {"R18"}


def test_devuelve_las_entidades_regla_cargadas() -> None:
    hechos = VOCABULARIO.validar("PARACETAMOL", ["FIEBRE"], ["EMBARAZO"])

    (regla,) = MOTOR.evaluar(hechos)

    assert regla is next(r for r in REGLAS_EJEMPLO if r.codigo == "R11")


def test_cada_entorno_es_nuevo_y_no_comparte_hechos() -> None:
    primero = FABRICA.crear()
    primero.assert_string("(sintoma (codigo FIEBRE))")
    segundo = FABRICA.crear()

    assert primero is not segundo
    assert [f for f in segundo.facts() if f.template.name == "sintoma"] == []
    assert len(list(segundo.rules())) == len(REGLAS_EJEMPLO)


def test_evaluaciones_sucesivas_no_se_contaminan() -> None:
    assert _codigos("PARACETAMOL", ["FIEBRE"], ["EMBARAZO"]) == {"R11"}
    assert _codigos("PARACETAMOL", ["DOLOR_CABEZA"], []) == {"R01"}


def test_veinte_hilos_simultaneos_igual_que_en_secuencia() -> None:
    casos = [
        HechosConsulta(m, frozenset(s), frozenset(c))
        for m, s, c in [
            (PARACETAMOL, {DOLOR_CABEZA}, set()),
            (PARACETAMOL, {DOLOR_CABEZA}, {EMBARAZO}),
            (PARACETAMOL, {FIEBRE}, {EMBARAZO}),
            (PARACETAMOL, {DOLOR_CABEZA, FIEBRE}, set()),
            (PARACETAMOL, {DOLOR_CABEZA}, {HIPERTENSION}),
            (IBUPROFENO, {DOLOR_CABEZA}, set()),
            (IBUPROFENO, {FIEBRE}, set()),
            (PARACETAMOL, {DOLOR_DENTAL}, {USO_ASPIRINA}),
            (IBUPROFENO, {DOLOR_CABEZA, FIEBRE}, set()),
            (PARACETAMOL, {FIEBRE, DOLOR_DENTAL}, {EMBARAZO}),
        ]
    ] * 2
    secuencial = [frozenset(r.codigo for r in MOTOR.evaluar(h)) for h in casos]

    with ThreadPoolExecutor(max_workers=20) as grupo:
        concurrente = list(
            grupo.map(lambda h: frozenset(r.codigo for r in MOTOR.evaluar(h)), casos)
        )

    assert len(casos) == 20
    assert concurrente == secuencial
