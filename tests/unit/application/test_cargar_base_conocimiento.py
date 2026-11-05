import dataclasses
import logging

import pytest

from application.casos_uso.cargar_base_conocimiento import CargarBaseConocimiento
from domain.base_conocimiento import BaseConocimiento
from domain.errores import BaseConocimientoNoDisponible
from domain.nivel import Nivel
from fakes.reglas_ejemplo import R01, R07, REGLAS_EJEMPLO, VOCABULARIO, regla
from fakes.repositorios import MENSAJE_FALLO_SIMULADO, ReglaRepositoryEnMemoria


def test_carga_correcta() -> None:
    base = CargarBaseConocimiento(ReglaRepositoryEnMemoria(VOCABULARIO, REGLAS_EJEMPLO)).ejecutar()

    assert isinstance(base, BaseConocimiento)
    assert base.vocabulario is VOCABULARIO
    assert base.reglas == REGLAS_EJEMPLO


def test_cero_reglas_no_disponible() -> None:
    with pytest.raises(BaseConocimientoNoDisponible):
        CargarBaseConocimiento(ReglaRepositoryEnMemoria(VOCABULARIO, [])).ejecutar()


def test_error_del_repositorio_no_disponible_sin_url() -> None:
    repositorio = ReglaRepositoryEnMemoria(
        VOCABULARIO, REGLAS_EJEMPLO, error=RuntimeError(MENSAJE_FALLO_SIMULADO)
    )

    with pytest.raises(BaseConocimientoNoDisponible) as error:
        CargarBaseConocimiento(repositorio).ejecutar()

    assert "postgresql" not in error.value.motivo
    assert "secreto" not in error.value.motivo
    assert "postgresql" not in str(error.value)
    assert error.value.__cause__ is None
    assert error.value.__suppress_context__ is True


def test_codigo_de_regla_duplicado() -> None:
    otra_r01 = dataclasses.replace(R01, id=101, version=2)

    with pytest.raises(BaseConocimientoNoDisponible):
        CargarBaseConocimiento(ReglaRepositoryEnMemoria(VOCABULARIO, [R01, otra_r01])).ejecutar()


@pytest.mark.parametrize(
    "fuera_de_vocabulario",
    [
        regla(90, "ASPIRINA", Nivel.ORIENTAR, ("FIEBRE",)),
        regla(91, "PARACETAMOL", Nivel.ORIENTAR, ("TOS_SECA",)),
        regla(92, "PARACETAMOL", Nivel.ADVERTIR, ("FIEBRE",), ("ASMA",)),
    ],
)
def test_codigo_no_presente_en_el_vocabulario(fuera_de_vocabulario: object) -> None:
    repositorio = ReglaRepositoryEnMemoria(VOCABULARIO, [R01, fuera_de_vocabulario])  # type: ignore[list-item]

    with pytest.raises(BaseConocimientoNoDisponible):
        CargarBaseConocimiento(repositorio).ejecutar()


def test_especificidad_incoherente_avisa_sin_fallar(caplog: pytest.LogCaptureFixture) -> None:
    incoherente = dataclasses.replace(R07, especificidad=5)

    with caplog.at_level(logging.WARNING):
        base = CargarBaseConocimiento(
            ReglaRepositoryEnMemoria(VOCABULARIO, [R01, incoherente])
        ).ejecutar()

    assert len(base.reglas) == 2
    avisos = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert any("R07" in r.getMessage() for r in avisos)
