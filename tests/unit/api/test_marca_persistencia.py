"""Marca interna de consulta no persistida (FR-019): cabecera y atributo data-, sin texto."""

import re

import pytest
from fastapi.testclient import TestClient

from api.dependencias import get_evaluar_consulta
from api.main import create_app
from application.casos_uso.evaluar_consulta import EvaluarConsulta
from domain.base_conocimiento import BaseConocimiento
from domain.mensajes_sistema import ConfiguracionSalvaguarda
from domain.resolucion_nivel import ResolucionPorSeveridad
from fakes.motor import FakeMotorInferencia
from fakes.reglas_ejemplo import R18, REGLAS_EJEMPLO, VOCABULARIO
from fakes.repositorios import ConsultaRepositoryEnMemoria

FORMULARIO = {"medicamento": "IBUPROFENO", "sintomas": ["DOLOR_CABEZA", "FIEBRE"]}


def _cliente(fallar: bool) -> TestClient:
    app = create_app()
    app.state.base = BaseConocimiento(VOCABULARIO, REGLAS_EJEMPLO)
    app.dependency_overrides[get_evaluar_consulta] = lambda: EvaluarConsulta(
        vocabulario=VOCABULARIO,
        motor=FakeMotorInferencia([R18]),
        estrategia=ResolucionPorSeveridad(),
        consultas=ConsultaRepositoryEnMemoria(fallar=fallar),
        salvaguarda=ConfiguracionSalvaguarda(),
    )
    return TestClient(app)


@pytest.mark.parametrize("fallar, valor", [(False, "true"), (True, "false")])
def test_cabecera_en_html_y_json(fallar: bool, valor: str) -> None:
    cliente = _cliente(fallar)

    html = cliente.post("/consulta", data=FORMULARIO)
    api = cliente.post("/api/v1/consultas", json=FORMULARIO)

    assert html.status_code == 200
    assert api.status_code == 200
    assert html.headers["X-Consulta-Persistida"] == valor
    assert api.headers["X-Consulta-Persistida"] == valor
    assert api.json()["persistida"] is (not fallar)


@pytest.mark.parametrize("fallar, valor", [(False, "true"), (True, "false")])
def test_atributo_data_en_el_resultado(fallar: bool, valor: str) -> None:
    html = _cliente(fallar).post("/consulta", data=FORMULARIO).text

    assert re.search(rf'<section id="resultado"[^>]*data-consulta-persistida="{valor}"', html)


def test_no_persistida_no_cambia_nada_visible() -> None:
    persistida = _cliente(False).post("/consulta", data=FORMULARIO).text
    no_persistida = _cliente(True).post("/consulta", data=FORMULARIO).text

    def sin_marca(html: str) -> str:
        return html.replace('data-consulta-persistida="false"', "").replace(
            'data-consulta-persistida="true"', ""
        )

    assert persistida != no_persistida
    assert sin_marca(persistida) == sin_marca(no_persistida)


def test_json_solo_difiere_en_persistida() -> None:
    persistida = _cliente(False).post("/api/v1/consultas", json=FORMULARIO).json()
    no_persistida = _cliente(True).post("/api/v1/consultas", json=FORMULARIO).json()

    assert persistida.pop("persistida") is True
    assert no_persistida.pop("persistida") is False
    assert persistida == no_persistida


def test_errores_de_validacion_no_llevan_la_marca() -> None:
    respuesta = _cliente(False).post("/consulta", data={"medicamento": "IBUPROFENO"})

    assert respuesta.status_code == 422
    assert "X-Consulta-Persistida" not in respuesta.headers
