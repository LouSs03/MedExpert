"""Pantalla de resultado: métricas reales, explicación del nivel y filas de recomendaciones."""

import re

from fastapi.testclient import TestClient

from api.dependencias import get_evaluar_consulta
from api.main import create_app
from application.casos_uso.evaluar_consulta import EvaluarConsulta
from domain.base_conocimiento import BaseConocimiento
from domain.mensajes_sistema import ConfiguracionSalvaguarda
from domain.regla import Regla
from domain.resolucion_nivel import ResolucionPorSeveridad
from fakes.motor import FakeMotorInferencia
from fakes.reglas_ejemplo import R01, R02, R07, R11, R18, REGLAS_EJEMPLO, VOCABULARIO
from fakes.repositorios import ConsultaRepositoryEnMemoria


def _resultado(disparadas: list[Regla], datos: dict[str, object]) -> str:
    app = create_app()
    app.state.base = BaseConocimiento(VOCABULARIO, REGLAS_EJEMPLO)
    app.dependency_overrides[get_evaluar_consulta] = lambda: EvaluarConsulta(
        vocabulario=VOCABULARIO,
        motor=FakeMotorInferencia(disparadas),
        estrategia=ResolucionPorSeveridad(),
        consultas=ConsultaRepositoryEnMemoria(),
        salvaguarda=ConfiguracionSalvaguarda(),
    )
    respuesta = TestClient(app).post("/consulta", data=datos)
    assert respuesta.status_code == 200
    return respuesta.text


def _texto(html: str) -> str:
    return " ".join(re.sub(r"<[^>]+>", " ", html).split())


def _metricas(html: str) -> dict[str, str]:
    pares = re.findall(r"<dt>([^<]+)</dt>\s*<dd>([^<]+)</dd>", html)
    return {etiqueta: valor for etiqueta, valor in pares}


def test_salvaguarda_que_sube_el_nivel() -> None:
    html = _resultado(
        [R18],
        {"medicamento": "IBUPROFENO", "sintomas": ["DOLOR_CABEZA", "FIEBRE"], "ninguna": "true"},
    )
    texto = _texto(html)

    assert "Resultado de tu consulta" in texto
    assert "Advertir : consulta antes de usar" in texto
    assert 'class="insignia-nivel insignia-advertir"' in html
    assert _metricas(html) == {
        "Regla aplicada": "R18",
        "Síntomas sin orientación específica": "1",
        "Reglas revisadas en la base": str(len(REGLAS_EJEMPLO)),
    }
    assert "Por eso el nivel sube de Orientar a Advertir." in texto
    for chip in ("Ibuprofeno", "Dolor de cabeza", "Fiebre", "Sin condiciones"):
        assert f'<li class="chip">{chip}</li>' in html


def test_varias_reglas_cuentan_las_reglas_aplicadas() -> None:
    html = _resultado(
        [R07, R01, R02], {"medicamento": "PARACETAMOL", "sintomas": ["DOLOR_CABEZA", "FIEBRE"]}
    )

    assert _metricas(html) == {
        "Reglas aplicadas": "3",
        "Síntomas sin orientación específica": "0",
        "Reglas revisadas en la base": str(len(REGLAS_EJEMPLO)),
    }
    assert "El nivel es el más severo entre las reglas aplicadas: Orientar." in _texto(html)
    assert 'class="insignia-nivel insignia-orientar"' in html


def test_cada_fila_es_un_mensaje_de_regla_sin_texto_añadido() -> None:
    html = _resultado(
        [R07, R01, R02], {"medicamento": "PARACETAMOL", "sintomas": ["DOLOR_CABEZA", "FIEBRE"]}
    )

    filas = re.findall(
        r'<li class="fila">\s*<span class="insignia-regla"[^>]*>(R\d\d)</span>\s*'
        r'<span class="fila-texto">([^<]+)</span>',
        html,
    )
    esperadas = [(r.codigo, m) for r in (R07, R01, R02) for m in r.mensajes]
    assert filas == esperadas


def test_sin_regla_cuenta_todos_los_sintomas_marcados() -> None:
    html = _resultado(
        [], {"medicamento": "IBUPROFENO", "sintomas": ["FIEBRE", "DOLOR_DENTAL"], "ninguna": "true"}
    )
    texto = _texto(html)

    assert "Derivar al médico : caso no cubierto" in texto
    assert 'class="insignia-nivel insignia-derivar"' in html
    assert _metricas(html) == {
        "Reglas aplicadas": "0",
        "Síntomas sin orientación específica": "2",
        "Reglas revisadas en la base": str(len(REGLAS_EJEMPLO)),
    }


def test_salvaguarda_que_no_baja_derivar() -> None:
    html = _resultado(
        [R11],
        {
            "medicamento": "PARACETAMOL",
            "sintomas": ["FIEBRE", "DOLOR_DENTAL"],
            "condiciones": ["EMBARAZO"],
        },
    )
    texto = _texto(html)

    assert "El nivel no baja: se mantiene en Derivar al médico." in texto
    assert "Por eso el nivel sube" not in texto
    assert '<li class="chip">Embarazo</li>' in html
    assert "Sin condiciones" not in texto


def test_cuatro_pantallas_con_la_franja_de_prototipo() -> None:
    app = create_app()
    app.state.base = BaseConocimiento(VOCABULARIO, REGLAS_EJEMPLO)
    cliente = TestClient(app)
    aviso = "Prototipo académico: no reemplaza la consulta médica o farmacéutica."
    for url in (
        "/",
        "/consulta/paso/1",
        "/consulta/paso/2?medicamento=PARACETAMOL",
        "/consulta/paso/3?medicamento=PARACETAMOL&sintomas=FIEBRE",
    ):
        assert '<p id="aviso"' in cliente.get(url).text
        assert aviso in cliente.get(url).text
    assert aviso in _resultado([R01], {"medicamento": "PARACETAMOL", "sintomas": ["DOLOR_CABEZA"]})
