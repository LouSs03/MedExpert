"""Fallo técnico de persistencia: única excepción del Principio III (FR-019)."""

import logging
from collections.abc import Iterator

import pytest

from application.casos_uso.evaluar_consulta import EvaluarConsulta
from domain.consulta import ResultadoEvaluacion
from domain.mensajes_sistema import ConfiguracionSalvaguarda
from domain.regla import Regla
from domain.resolucion_nivel import ResolucionPorSeveridad
from fakes.motor import FakeMotorInferencia
from fakes.reglas_ejemplo import R18, VOCABULARIO
from fakes.repositorios import ConsultaRepositoryEnMemoria
from infrastructure.logging import REDACTADO, FiltroSecretos


@pytest.fixture
def caplog_saneado(caplog: pytest.LogCaptureFixture) -> Iterator[pytest.LogCaptureFixture]:
    """caplog con el filtro de secretos instalado, como en producción (configurar_logging)."""
    filtro = FiltroSecretos()
    caplog.handler.addFilter(filtro)
    caplog.set_level(logging.ERROR)
    yield caplog
    caplog.handler.removeFilter(filtro)


def _ejecutar(disparadas: list[Regla], fallar: bool) -> ResultadoEvaluacion:
    caso = EvaluarConsulta(
        vocabulario=VOCABULARIO,
        motor=FakeMotorInferencia(disparadas),
        estrategia=ResolucionPorSeveridad(),
        consultas=ConsultaRepositoryEnMemoria(fallar=fallar),
        salvaguarda=ConfiguracionSalvaguarda(),
    )
    return caso.ejecutar("IBUPROFENO", ["DOLOR_CABEZA", "FIEBRE"], [])


@pytest.mark.parametrize("disparadas", [[R18], []], ids=["con-salvaguarda", "sin-regla"])
def test_fallo_de_registro_muestra_el_resultado_completo(
    disparadas: list[Regla], caplog_saneado: pytest.LogCaptureFixture
) -> None:
    correcto = _ejecutar(disparadas, fallar=False)
    fallido = _ejecutar(disparadas, fallar=True)

    assert fallido.persistida is False
    assert fallido.consulta_id is None
    assert fallido.nivel is correcto.nivel
    assert fallido.sin_regla is correcto.sin_regla
    assert fallido.reglas_disparadas == correcto.reglas_disparadas
    assert fallido.sintomas_no_cubiertos == correcto.sintomas_no_cubiertos
    assert fallido.mensajes_sistema == correcto.mensajes_sistema


def test_fallo_de_registro_queda_en_el_log_con_detalle_saneado(
    caplog_saneado: pytest.LogCaptureFixture,
) -> None:
    _ejecutar([R18], fallar=True)

    errores = [r for r in caplog_saneado.records if r.levelno == logging.ERROR]
    assert len(errores) == 1
    registro = errores[0]
    assert registro.getMessage() == "No se pudo persistir la consulta"
    assert getattr(registro, "tipo_error", None) == "RuntimeError"
    assert registro.exc_info is not None
    texto = caplog_saneado.text
    assert "RuntimeError" in texto
    assert "fallo simulado" in texto
    assert REDACTADO in texto
    assert "secreto" not in texto
    assert "postgresql://" not in texto


def test_registro_correcto_no_escribe_errores(caplog_saneado: pytest.LogCaptureFixture) -> None:
    resultado = _ejecutar([R18], fallar=False)

    assert resultado.persistida is True
    assert resultado.consulta_id is not None
    assert [r for r in caplog_saneado.records if r.levelno >= logging.ERROR] == []
