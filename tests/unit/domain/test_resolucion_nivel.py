import random

from domain.nivel import Nivel
from domain.resolucion_nivel import EstrategiaResolucionNivel, ResolucionPorSeveridad
from domain.vocabulario import Condicion, HechosConsulta, Medicamento, Sintoma
from fakes.reglas_ejemplo import (
    DOLOR_CABEZA,
    DOLOR_DENTAL,
    EMBARAZO,
    FIEBRE,
    IBUPROFENO,
    PARACETAMOL,
    R01,
    R02,
    R07,
    R10,
    R11,
    R18,
    regla,
)

ESTRATEGIA = ResolucionPorSeveridad()


def _hechos(
    medicamento: Medicamento, *sintomas: Sintoma, condiciones: tuple[Condicion, ...] = ()
) -> HechosConsulta:
    return HechosConsulta(medicamento, frozenset(sintomas), frozenset(condiciones))


def _codigos(resolucion_reglas: tuple[object, ...]) -> list[str]:
    return [d.regla.codigo for d in resolucion_reglas]  # type: ignore[attr-defined]


def test_es_una_estrategia_sustituible() -> None:
    estrategia: EstrategiaResolucionNivel = ESTRATEGIA
    assert callable(estrategia.resolver)


def test_sin_reglas_deriva_y_no_evalua_la_salvaguarda() -> None:
    resolucion = ESTRATEGIA.resolver(_hechos(IBUPROFENO, FIEBRE, DOLOR_DENTAL), [])

    assert resolucion.nivel is Nivel.DERIVAR
    assert resolucion.sin_regla is True
    assert resolucion.reglas_disparadas == ()
    assert resolucion.sintomas_no_cubiertos == ()


def test_todo_cubierto_devuelve_el_maximo_de_severidad() -> None:
    hechos = _hechos(PARACETAMOL, DOLOR_CABEZA, FIEBRE, condiciones=(EMBARAZO,))
    resolucion = ESTRATEGIA.resolver(hechos, [R10, R11])

    assert resolucion.nivel is Nivel.DERIVAR
    assert resolucion.sin_regla is False
    assert resolucion.sintomas_no_cubiertos == ()


def test_todo_cubierto_con_solo_orientar() -> None:
    resolucion = ESTRATEGIA.resolver(_hechos(PARACETAMOL, DOLOR_CABEZA, FIEBRE), [R01, R02, R07])

    assert resolucion.nivel is Nivel.ORIENTAR
    assert resolucion.sintomas_no_cubiertos == ()


def test_salvaguarda_eleva_orientar_a_advertir() -> None:
    resolucion = ESTRATEGIA.resolver(_hechos(IBUPROFENO, DOLOR_CABEZA, FIEBRE), [R18])

    assert resolucion.nivel is Nivel.ADVERTIR
    assert resolucion.sin_regla is False
    assert resolucion.sintomas_no_cubiertos == (FIEBRE,)
    assert _codigos(resolucion.reglas_disparadas) == ["R18"]


def test_salvaguarda_nunca_rebaja_derivar() -> None:
    hechos = _hechos(PARACETAMOL, FIEBRE, DOLOR_DENTAL, condiciones=(EMBARAZO,))
    resolucion = ESTRATEGIA.resolver(hechos, [R11])

    assert resolucion.nivel is Nivel.DERIVAR
    assert resolucion.sintomas_no_cubiertos == (DOLOR_DENTAL,)


def test_salvaguarda_mantiene_advertir() -> None:
    hechos = _hechos(PARACETAMOL, DOLOR_CABEZA, DOLOR_DENTAL, condiciones=(EMBARAZO,))
    resolucion = ESTRATEGIA.resolver(hechos, [R10])

    assert resolucion.nivel is Nivel.ADVERTIR
    assert resolucion.sintomas_no_cubiertos == (DOLOR_DENTAL,)


def test_sintomas_no_cubiertos_ordenados_por_id() -> None:
    hechos = _hechos(IBUPROFENO, DOLOR_DENTAL, DOLOR_CABEZA, FIEBRE)
    resolucion = ESTRATEGIA.resolver(hechos, [R18])

    assert resolucion.sintomas_no_cubiertos == (FIEBRE, DOLOR_DENTAL)


def test_orden_fr009_severidad_especificidad_codigo() -> None:
    resolucion = ESTRATEGIA.resolver(
        _hechos(PARACETAMOL, DOLOR_CABEZA, FIEBRE, condiciones=(EMBARAZO,)),
        [R01, R02, R07, R10, R11],
    )

    assert _codigos(resolucion.reglas_disparadas) == ["R11", "R10", "R07", "R01", "R02"]
    assert [d.orden for d in resolucion.reglas_disparadas] == [1, 2, 3, 4, 5]


def test_orden_con_empates_de_nivel_y_especificidad_desempata_por_codigo() -> None:
    r30 = regla(30, "PARACETAMOL", Nivel.ADVERTIR, ("FIEBRE",), ("EMBARAZO",))
    r05 = regla(5, "PARACETAMOL", Nivel.ADVERTIR, ("DOLOR_CABEZA",), ("EMBARAZO",))
    r20 = regla(20, "PARACETAMOL", Nivel.ADVERTIR, ("FIEBRE",))
    hechos = _hechos(PARACETAMOL, DOLOR_CABEZA, FIEBRE, condiciones=(EMBARAZO,))

    resolucion = ESTRATEGIA.resolver(hechos, [r20, r30, r05])

    assert _codigos(resolucion.reglas_disparadas) == ["R05", "R30", "R20"]


def test_misma_salida_al_barajar_la_entrada() -> None:
    hechos = _hechos(PARACETAMOL, DOLOR_CABEZA, FIEBRE, condiciones=(EMBARAZO,))
    entrada = [R01, R02, R07, R10, R11]
    esperado = ESTRATEGIA.resolver(hechos, entrada)
    generador = random.Random(2026)

    for _ in range(20):
        barajada = entrada[:]
        generador.shuffle(barajada)
        assert ESTRATEGIA.resolver(hechos, barajada) == esperado


def test_regla_repetida_aparece_una_sola_vez() -> None:
    resolucion = ESTRATEGIA.resolver(_hechos(PARACETAMOL, DOLOR_CABEZA), [R01, R01])

    assert _codigos(resolucion.reglas_disparadas) == ["R01"]
