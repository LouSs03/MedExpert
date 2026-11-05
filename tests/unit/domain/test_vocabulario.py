import dataclasses

import pytest

from domain.errores import VocabularioInvalido
from domain.vocabulario import HechosConsulta, Medicamento, Sintoma, Vocabulario
from fakes.reglas_ejemplo import (
    DOLOR_CABEZA,
    EMBARAZO,
    FIEBRE,
    IBUPROFENO,
    PARACETAMOL,
    VOCABULARIO,
)


def test_validar_devuelve_hechos_con_un_medicamento_sintomas_y_condiciones() -> None:
    hechos = VOCABULARIO.validar("PARACETAMOL", ["DOLOR_CABEZA", "FIEBRE"], ["EMBARAZO"])

    assert isinstance(hechos, HechosConsulta)
    assert hechos.medicamento == PARACETAMOL
    assert hechos.sintomas == frozenset({DOLOR_CABEZA, FIEBRE})
    assert hechos.condiciones == frozenset({EMBARAZO})


def test_validar_admite_cero_condiciones() -> None:
    hechos = VOCABULARIO.validar("IBUPROFENO", ["FIEBRE"], [])

    assert hechos.medicamento == IBUPROFENO
    assert hechos.condiciones == frozenset()


def test_validar_elimina_duplicados() -> None:
    hechos = VOCABULARIO.validar("PARACETAMOL", ["FIEBRE", "FIEBRE"], ["EMBARAZO", "EMBARAZO"])

    assert hechos.sintomas == frozenset({FIEBRE})
    assert hechos.condiciones == frozenset({EMBARAZO})


def test_validar_rechaza_todos_los_codigos_desconocidos() -> None:
    with pytest.raises(VocabularioInvalido) as error:
        VOCABULARIO.validar("ASPIRINA", ["FIEBRE", "SINTOMA_X"], ["CONDICION_Y"])

    assert set(error.value.valores_rechazados) == {"ASPIRINA", "SINTOMA_X", "CONDICION_Y"}


def test_validar_rechaza_cero_sintomas() -> None:
    with pytest.raises(VocabularioInvalido) as error:
        VOCABULARIO.validar("PARACETAMOL", [], [])

    assert error.value.problemas
    assert any("síntoma" in p for p in error.value.problemas)


def test_validar_rechaza_medicamento_ausente() -> None:
    with pytest.raises(VocabularioInvalido) as error:
        VOCABULARIO.validar("", ["FIEBRE"], [])

    assert any("medicamento" in p for p in error.value.problemas)


def test_validar_acumula_todos_los_problemas() -> None:
    with pytest.raises(VocabularioInvalido) as error:
        VOCABULARIO.validar(None, [], ["CONDICION_Y"])

    assert error.value.valores_rechazados == ("CONDICION_Y",)
    assert len(error.value.problemas) == 3


def test_catalogos_quedan_ordenados_por_id() -> None:
    vocabulario = Vocabulario(
        medicamentos=(IBUPROFENO, PARACETAMOL),
        sintomas=(FIEBRE, DOLOR_CABEZA),
        condiciones=(EMBARAZO,),
    )

    assert vocabulario.medicamentos == (PARACETAMOL, IBUPROFENO)
    assert vocabulario.sintomas == (DOLOR_CABEZA, FIEBRE)


def test_codigo_invalido_en_catalogo() -> None:
    with pytest.raises(ValueError):
        Sintoma(9, "fiebre alta", "Fiebre alta")


def test_codigos_duplicados_en_catalogo() -> None:
    with pytest.raises(ValueError):
        Vocabulario(
            medicamentos=(PARACETAMOL, Medicamento(3, "PARACETAMOL", "Otro")),
            sintomas=(FIEBRE,),
            condiciones=(),
        )


def test_hechos_exigen_al_menos_un_sintoma() -> None:
    with pytest.raises(ValueError):
        HechosConsulta(PARACETAMOL, frozenset(), frozenset())


def test_objetos_de_valor_son_inmutables() -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        FIEBRE.codigo = "OTRO"  # type: ignore[misc]
