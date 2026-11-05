import dataclasses

import pytest

from domain.nivel import EstadoRegla, Nivel
from domain.regla import Regla, ReglaDisparada
from fakes.reglas_ejemplo import R07, R10


def _datos(**cambios: object) -> dict[str, object]:
    datos: dict[str, object] = {
        "id": 99,
        "codigo": "R99",
        "version": 1,
        "medicamento": "PARACETAMOL",
        "sintomas": frozenset({"FIEBRE"}),
        "condiciones": frozenset(),
        "sin_condiciones": True,
        "especificidad": 1,
        "nivel": Nivel.ORIENTAR,
        "estado": EstadoRegla.APROBADA,
        "mensajes": ("Mensaje.",),
    }
    datos.update(cambios)
    return datos


def test_regla_valida() -> None:
    regla = Regla(**_datos())  # type: ignore[arg-type]

    assert regla.codigo == "R99"
    assert regla.sintomas == frozenset({"FIEBRE"})


def test_sin_condiciones_no_admite_condiciones() -> None:
    with pytest.raises(ValueError):
        Regla(**_datos(condiciones=frozenset({"EMBARAZO"}), sin_condiciones=True))  # type: ignore[arg-type]


def test_exige_al_menos_un_sintoma() -> None:
    with pytest.raises(ValueError):
        Regla(**_datos(sintomas=frozenset()))  # type: ignore[arg-type]


def test_exige_al_menos_un_mensaje() -> None:
    with pytest.raises(ValueError):
        Regla(**_datos(mensajes=()))  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "campo, valor",
    [
        ("codigo", "r99"),
        ("medicamento", "paracetamol"),
        ("sintomas", frozenset({"FIEBRE) (assert"})),
        ("condiciones", frozenset({"1EMBARAZO"})),
    ],
)
def test_rechaza_codigos_con_formato_invalido(campo: str, valor: object) -> None:
    cambios: dict[str, object] = {campo: valor}
    if campo == "condiciones":
        cambios["sin_condiciones"] = False
    with pytest.raises(ValueError):
        Regla(**_datos(**cambios))  # type: ignore[arg-type]


def test_regla_es_inmutable() -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        R07.nivel = Nivel.DERIVAR  # type: ignore[misc]


def test_regla_con_condiciones() -> None:
    assert R10.condiciones == frozenset({"EMBARAZO"})
    assert R10.sin_condiciones is False
    assert R10.especificidad == 2


def test_regla_disparada() -> None:
    disparada = ReglaDisparada(regla=R07, orden=1)

    assert disparada.regla is R07
    assert disparada.orden == 1
