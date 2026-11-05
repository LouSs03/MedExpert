"""Traducción Regla -> defrule según contracts/traduccion-clips.md."""

import pytest

from domain.nivel import Nivel
from fakes.reglas_ejemplo import R07, R10, regla
from infrastructure.inference.traductor_reglas import TraductorReglasClips

TRADUCTOR = TraductorReglasClips()


def test_plantillas_del_contrato() -> None:
    assert TRADUCTOR.plantillas() == (
        "(deftemplate medicamento (slot codigo))",
        "(deftemplate sintoma (slot codigo))",
        "(deftemplate condicion (slot codigo))",
        "(deftemplate disparo (slot regla-id))",
    )


def test_regla_con_condiciones_r10() -> None:
    assert TRADUCTOR.traducir(R10) == (
        "(defrule R10-v1\n"
        "  (medicamento (codigo PARACETAMOL))\n"
        "  (sintoma (codigo DOLOR_CABEZA))\n"
        "  (condicion (codigo EMBARAZO))\n"
        "  =>\n"
        "  (assert (disparo (regla-id 10))))"
    )


def test_regla_sin_condiciones_r07() -> None:
    assert TRADUCTOR.traducir(R07) == (
        "(defrule R07-v1\n"
        "  (medicamento (codigo PARACETAMOL))\n"
        "  (sintoma (codigo DOLOR_CABEZA))\n"
        "  (sintoma (codigo FIEBRE))\n"
        "  (not (condicion))\n"
        "  =>\n"
        "  (assert (disparo (regla-id 7))))"
    )


def test_sintomas_y_condiciones_en_orden_alfabetico() -> None:
    r = regla(
        99,
        "IBUPROFENO",
        Nivel.DERIVAR,
        ("FIEBRE", "DOLOR_MUSCULAR"),
        ("HIPERTENSION", "ADULTO_MAYOR"),
    )

    lineas = TRADUCTOR.traducir(r).splitlines()

    assert lineas[2:6] == [
        "  (sintoma (codigo DOLOR_MUSCULAR))",
        "  (sintoma (codigo FIEBRE))",
        "  (condicion (codigo ADULTO_MAYOR))",
        "  (condicion (codigo HIPERTENSION))",
    ]
    assert "(not (condicion))" not in TRADUCTOR.traducir(r)


def test_rechaza_codigo_con_caracteres_no_permitidos() -> None:
    r = regla(98, "PARACETAMOL", Nivel.ORIENTAR, ("FIEBRE",))
    object.__setattr__(r, "sintomas", frozenset({"FIEBRE) (assert"}))

    with pytest.raises(ValueError):
        TRADUCTOR.traducir(r)


@pytest.mark.parametrize("identificador", ["1)", 1.5, True])
def test_rechaza_regla_id_no_entero(identificador: object) -> None:
    r = regla(97, "PARACETAMOL", Nivel.ORIENTAR, ("FIEBRE",))
    object.__setattr__(r, "id", identificador)

    with pytest.raises(ValueError):
        TRADUCTOR.traducir(r)
