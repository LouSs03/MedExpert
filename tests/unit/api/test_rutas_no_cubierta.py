"""Presentación de una combinación no cubierta (US2; contracts/http.md, caso `sin_regla = true`)."""

import re

from fastapi.testclient import TestClient

from api.dependencias import get_evaluar_consulta
from api.main import create_app
from application.casos_uso.evaluar_consulta import EvaluarConsulta
from domain.base_conocimiento import BaseConocimiento
from domain.mensajes_sistema import TEXTO_COMBINACION_NO_CUBIERTA, ConfiguracionSalvaguarda
from domain.resolucion_nivel import ResolucionPorSeveridad
from fakes.motor import FakeMotorInferencia
from fakes.reglas_ejemplo import REGLAS_EJEMPLO, VOCABULARIO
from fakes.repositorios import ConsultaRepositoryEnMemoria

AVISO = "Prototipo académico: no reemplaza la consulta médica o farmacéutica."


def _cliente() -> TestClient:
    app = create_app()
    app.state.base = BaseConocimiento(VOCABULARIO, REGLAS_EJEMPLO)
    app.dependency_overrides[get_evaluar_consulta] = lambda: EvaluarConsulta(
        vocabulario=VOCABULARIO,
        motor=FakeMotorInferencia([]),
        estrategia=ResolucionPorSeveridad(),
        consultas=ConsultaRepositoryEnMemoria(),
        salvaguarda=ConfiguracionSalvaguarda(pendiente_aprobacion=True),
    )
    return TestClient(app)


def _texto(html: str) -> str:
    return " ".join(re.sub(r"<[^>]+>", " ", html).split())


def test_html_combinacion_no_cubierta() -> None:
    respuesta = _cliente().post(
        "/consulta", data={"medicamento": "IBUPROFENO", "sintomas": ["FIEBRE"]}
    )

    assert respuesta.status_code == 200
    html = respuesta.text
    texto = _texto(html)
    assert AVISO in texto
    assert '<section id="resultado" data-nivel="DERIVAR" data-salvaguarda="false"' in html
    assert "Derivar al médico" in texto
    assert '<aside id="mensajes-sistema"' in html
    assert TEXTO_COMBINACION_NO_CUBIERTA in texto
    assert "Pendiente de aprobación médica" not in texto
    assert "pendiente de aprobación" not in texto
    assert 'class="regla"' not in html
    explicacion = re.search(r'<div id="explicacion".*?</div>', html, re.S)
    assert explicacion is not None
    assert "Ninguna regla aplicada" in _texto(explicacion.group(0))
    assert "Salvaguarda del sistema" not in texto


def test_json_combinacion_no_cubierta() -> None:
    respuesta = _cliente().post(
        "/api/v1/consultas", json={"medicamento": "IBUPROFENO", "sintomas": ["FIEBRE"]}
    )

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["nivel"] == "DERIVAR"
    assert cuerpo["nivel_etiqueta"] == "Derivar al médico"
    assert cuerpo["sin_regla"] is True
    assert cuerpo["reglas_aplicadas"] == []
    assert cuerpo["salvaguarda_activada"] is False
    assert cuerpo["sintomas_no_cubiertos"] == []
    assert cuerpo["mensajes_sistema"] == [
        {
            "tipo": "COMBINACION_NO_CUBIERTA",
            "texto": TEXTO_COMBINACION_NO_CUBIERTA,
            "pendiente_aprobacion": False,
            "sintoma": None,
        }
    ]
