"""Consulta en tres pasos: navegación, estado en la URL, opciones bloqueadas y errores."""

import re
from urllib.parse import parse_qs, urlsplit

from fastapi.testclient import TestClient

from api.dependencias import get_evaluar_consulta
from api.main import create_app
from application.casos_uso.evaluar_consulta import EvaluarConsulta
from domain.base_conocimiento import BaseConocimiento
from domain.mensajes_sistema import ConfiguracionSalvaguarda
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
        salvaguarda=ConfiguracionSalvaguarda(),
    )
    return TestClient(app)


def _texto(html: str) -> str:
    return " ".join(re.sub(r"<[^>]+>", " ", html).split())


def test_portada_con_cifras_reales_y_enlace_al_paso_1() -> None:
    html = _cliente().get("/").text

    assert AVISO in html
    assert f"{len(REGLAS_EJEMPLO)} reglas revisadas" in _texto(html)
    assert "Paracetamol e Ibuprofeno" in _texto(html)
    assert 'href="/consulta/paso/1"' in html


def test_paso_1_bloquea_los_medicamentos_sin_reglas() -> None:
    html = _cliente().get("/consulta/paso/1").text

    bloqueados = re.findall(
        r'<button type="button" class="opcion opcion-bloqueada" disabled>\s*'
        r'<span class="opcion-texto">([^<]+)</span>',
        html,
    )
    assert bloqueados == ["Naproxeno", "Diclofenaco", "Aspirina", "Azitromicina"]
    assert html.count("Próximamente") >= 4
    assert 'aria-disabled="true"' in html
    assert 'aria-label="Elija un medicamento para continuar"' in html
    assert "Volver al paso anterior" not in html


def test_paso_2_bloquea_malestar_general_y_conserva_el_medicamento() -> None:
    html = _cliente().get("/consulta/paso/2", params={"medicamento": "IBUPROFENO"}).text

    assert '<span class="opcion-texto">Malestar general</span>' in html
    assert '<input type="hidden" name="medicamento" value="IBUPROFENO">' in html
    assert '<li class="chip">Ibuprofeno</li>' in html
    volver = re.search(r'<a class="volver" href="([^"]+)"', html)
    assert volver is not None
    assert parse_qs(urlsplit(volver.group(1).replace("&amp;", "&")).query) == {
        "medicamento": ["IBUPROFENO"]
    }


def test_paso_3_conserva_todo_el_estado_y_marca_lo_elegido() -> None:
    html = (
        _cliente()
        .get(
            "/consulta/paso/3",
            params={
                "medicamento": "PARACETAMOL",
                "sintomas": ["DOLOR_CABEZA", "FIEBRE"],
                "condiciones": ["EMBARAZO"],
            },
        )
        .text
    )

    assert '<form class="form-paso" method="post" action="/consulta"' in html
    assert '<input type="hidden" name="sintomas" value="FIEBRE">' in html
    assert re.search(r'data-valor="EMBARAZO"\s+aria-pressed="true"', html)
    assert re.search(r'data-ninguna\s+aria-pressed="false"', html)
    assert 'aria-disabled="false"' in html
    assert "No tengo ninguna de estas condiciones" in html
    for chip in ("Paracetamol", "Dolor de cabeza", "Fiebre"):
        assert f'<li class="chip">{chip}</li>' in html


def test_paso_3_ninguna_desde_la_url_habilita_el_avance() -> None:
    html = (
        _cliente()
        .get(
            "/consulta/paso/3",
            params={"medicamento": "PARACETAMOL", "sintomas": ["FIEBRE"], "ninguna": "1"},
        )
        .text
    )

    assert re.search(r'data-ninguna\s+aria-pressed="true"', html)
    assert 'aria-disabled="false"' in html


def test_saltar_al_paso_2_sin_medicamento_vuelve_al_paso_1_con_error() -> None:
    respuesta = _cliente().get("/consulta/paso/2")

    assert respuesta.status_code == 422
    assert "Seleccione el medicamento que desea tomar" in respuesta.text
    assert "Debe elegir exactamente un medicamento." in _texto(respuesta.text)


def test_saltar_al_paso_3_sin_sintomas_vuelve_al_paso_2_con_error() -> None:
    respuesta = _cliente().get("/consulta/paso/3", params={"medicamento": "PARACETAMOL"})

    assert respuesta.status_code == 422
    assert "Seleccione el síntoma a tratar" in respuesta.text
    assert "Debe marcar al menos un síntoma." in _texto(respuesta.text)


def test_codigo_desconocido_en_la_url_no_avanza() -> None:
    respuesta = _cliente().get("/consulta/paso/2", params={"medicamento": "NAPROXENO"})

    assert respuesta.status_code == 422
    assert "Seleccione el medicamento que desea tomar" in respuesta.text


def test_post_con_medicamento_desconocido_muestra_el_paso_1() -> None:
    respuesta = _cliente().post(
        "/consulta", data={"medicamento": "ASPIRINA", "sintomas": ["FIEBRE"]}
    )

    assert respuesta.status_code == 422
    assert "Seleccione el medicamento que desea tomar" in respuesta.text
    assert '<input type="hidden" name="sintomas" value="FIEBRE">' in respuesta.text


def test_las_tres_pantallas_cargan_el_script_de_seleccion() -> None:
    cliente = _cliente()
    urls = [
        "/consulta/paso/1",
        "/consulta/paso/2?medicamento=PARACETAMOL",
        "/consulta/paso/3?medicamento=PARACETAMOL&sintomas=FIEBRE",
    ]
    for url in urls:
        assert "/estaticos/consulta.js" in cliente.get(url).text
    assert cliente.get("/estaticos/consulta.js").status_code == 200
