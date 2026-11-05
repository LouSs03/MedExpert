"""Rutas HTML y JSON de la consulta (contracts/http.md) con dependencias sustituidas."""

import re

import pytest
from fastapi.testclient import TestClient

from api.dependencias import get_evaluar_consulta
from api.main import create_app
from application.casos_uso.evaluar_consulta import EvaluarConsulta
from domain.base_conocimiento import BaseConocimiento
from domain.mensajes_sistema import ConfiguracionSalvaguarda
from domain.regla import Regla
from domain.resolucion_nivel import ResolucionPorSeveridad
from fakes.motor import FakeMotorInferencia
from fakes.reglas_ejemplo import R01, R02, R07, R18, REGLAS_EJEMPLO, VOCABULARIO
from fakes.repositorios import ConsultaRepositoryEnMemoria

AVISO = "Prototipo académico: no reemplaza la consulta médica o farmacéutica."
BASE = BaseConocimiento(VOCABULARIO, REGLAS_EJEMPLO)


def _cliente(
    disparadas: list[Regla] | None = None,
    pendiente: bool = True,
    disponible: bool = True,
) -> TestClient:
    app = create_app()
    app.state.base = BASE if disponible else None

    def evaluar() -> EvaluarConsulta:
        return EvaluarConsulta(
            vocabulario=VOCABULARIO,
            motor=FakeMotorInferencia(disparadas or []),
            estrategia=ResolucionPorSeveridad(),
            consultas=ConsultaRepositoryEnMemoria(),
            salvaguarda=ConfiguracionSalvaguarda(pendiente_aprobacion=pendiente),
        )

    app.dependency_overrides[get_evaluar_consulta] = evaluar
    return TestClient(app)


def _texto(html: str) -> str:
    """Texto visible aproximado: sin etiquetas y con espacios normalizados."""
    return " ".join(re.sub(r"<[^>]+>", " ", html).split())


def test_formulario_muestra_el_vocabulario_y_el_aviso() -> None:
    respuesta = _cliente().get("/consulta/paso/1")

    assert respuesta.status_code == 200
    html = respuesta.text
    assert AVISO in html
    assert html.count('name="medicamento"') == 2
    assert html.count('name="sintomas"') == 6
    assert html.count('name="condiciones"') == 7
    for termino in (*VOCABULARIO.medicamentos, *VOCABULARIO.sintomas, *VOCABULARIO.condiciones):
        assert f'value="{termino.codigo}"' in html
    assert "Adulto mayor (60 años o más)" in html


def test_resultado_html_con_mensajes_agrupados_en_orden() -> None:
    cliente = _cliente([R02, R01, R07])

    respuesta = cliente.post(
        "/consulta", data={"medicamento": "PARACETAMOL", "sintomas": ["DOLOR_CABEZA", "FIEBRE"]}
    )

    assert respuesta.status_code == 200
    html = respuesta.text
    assert AVISO in html
    assert '<section id="resultado" data-nivel="ORIENTAR" data-salvaguarda="false"' in html
    texto = _texto(html)
    assert "Orientar" in texto
    posiciones = [
        texto.index(m)
        for m in (
            "Mensaje de ejemplo R07 (1).",
            "Mensaje de ejemplo R07 (2).",
            "Mensaje de ejemplo R01.",
            "Mensaje de ejemplo R02.",
        )
    ]
    assert posiciones == sorted(posiciones)
    explicacion = re.search(r'<div id="explicacion".*?</div>', html, re.S)
    assert explicacion is not None
    assert "Reglas aplicadas: R07, R01, R02" in _texto(explicacion.group(0))
    assert 'id="mensajes-sistema"' not in html


def test_resultado_html_con_salvaguarda_pendiente() -> None:
    respuesta = _cliente([R18], pendiente=True).post(
        "/consulta", data={"medicamento": "IBUPROFENO", "sintomas": ["DOLOR_CABEZA", "FIEBRE"]}
    )

    html = respuesta.text
    texto = _texto(html)
    assert '<section id="resultado" data-nivel="ADVERTIR" data-salvaguarda="true"' in html
    assert '<aside id="mensajes-sistema"' in html
    assert html.index("Mensaje de ejemplo R18.") < html.index('<aside id="mensajes-sistema"')
    assert "Mensaje del sistema (no proviene de una regla validada)" in texto
    assert "Pendiente de aprobación médica" in texto
    assert "«Fiebre» no tiene orientación específica con Ibuprofeno" in texto
    assert (
        "Salvaguarda del sistema (pendiente de aprobación médica): "
        "síntomas sin regla aplicable: Fiebre" in texto
    )


def test_resultado_html_con_salvaguarda_aprobada_sin_distintivo() -> None:
    respuesta = _cliente([R18], pendiente=False).post(
        "/consulta", data={"medicamento": "IBUPROFENO", "sintomas": ["DOLOR_CABEZA", "FIEBRE"]}
    )

    texto = _texto(respuesta.text)
    assert "Pendiente de aprobación médica" not in texto
    assert "pendiente de aprobación" not in texto
    assert "Salvaguarda del sistema: síntomas sin regla aplicable: Fiebre" in texto


def test_formulario_422_con_errores_y_valores_marcados() -> None:
    respuesta = _cliente().post(
        "/consulta", data={"medicamento": "PARACETAMOL", "condiciones": ["EMBARAZO"]}
    )

    assert respuesta.status_code == 422
    html = respuesta.text
    assert AVISO in html
    assert "Debe marcar al menos un síntoma." in _texto(html)
    assert re.search(r'value="PARACETAMOL"[^>]*checked', html)
    assert re.search(r'value="EMBARAZO"[^>]*checked', html)
    assert not re.search(r'value="IBUPROFENO"[^>]*checked', html)


def test_api_json_resultado_dto() -> None:
    respuesta = _cliente([R18]).post(
        "/api/v1/consultas",
        json={
            "medicamento": "IBUPROFENO",
            "sintomas": ["DOLOR_CABEZA", "FIEBRE"],
            "condiciones": [],
        },
    )

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "nivel": "ADVERTIR",
        "nivel_etiqueta": "Advertir",
        "sin_regla": False,
        "reglas_aplicadas": [
            {
                "codigo": "R18",
                "version": 1,
                "nivel": "ORIENTAR",
                "especificidad": 1,
                "mensajes": ["Mensaje de ejemplo R18."],
            }
        ],
        "salvaguarda_activada": True,
        "sintomas_no_cubiertos": [{"codigo": "FIEBRE", "nombre": "Fiebre"}],
        "mensajes_sistema": [
            {
                "tipo": "SINTOMA_NO_CUBIERTO",
                "texto": (
                    "«Fiebre» no tiene orientación específica con Ibuprofeno en la base de "
                    "conocimiento validada. Consulte a un médico o farmacéutico."
                ),
                "pendiente_aprobacion": True,
                "sintoma": "FIEBRE",
            }
        ],
        "persistida": True,
        "aviso": AVISO,
    }


def test_api_elimina_duplicados_y_condiciones_por_defecto() -> None:
    respuesta = _cliente([R01]).post(
        "/api/v1/consultas", json={"medicamento": "PARACETAMOL", "sintomas": ["DOLOR_CABEZA"] * 3}
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["salvaguarda_activada"] is False


def test_api_422_con_valores_rechazados() -> None:
    respuesta = _cliente().post(
        "/api/v1/consultas", json={"medicamento": "PARACETAMOL", "sintomas": ["SINTOMA_X"]}
    )

    assert respuesta.status_code == 422
    cuerpo = respuesta.json()
    assert cuerpo["valores_rechazados"] == ["SINTOMA_X"]
    assert cuerpo["detalle"]


@pytest.mark.parametrize(
    "cuerpo", [{"medicamento": "PARACETAMOL", "sintomas": []}, {"sintomas": ["FIEBRE"]}]
)
def test_api_422_de_validacion_usa_el_formato_del_contrato(cuerpo: dict[str, object]) -> None:
    respuesta = _cliente().post("/api/v1/consultas", json=cuerpo)

    assert respuesta.status_code == 422
    assert set(respuesta.json()) == {"detalle", "valores_rechazados"}
    assert respuesta.json()["valores_rechazados"] == []


def test_salud_disponible() -> None:
    respuesta = _cliente().get("/salud")

    assert respuesta.status_code == 200
    assert respuesta.json() == {"base_conocimiento": "disponible", "reglas": len(REGLAS_EJEMPLO)}


@pytest.mark.parametrize(
    "metodo, ruta, datos",
    [
        ("get", "/", None),
        ("post", "/consulta", {"medicamento": "PARACETAMOL", "sintomas": ["FIEBRE"]}),
    ],
)
def test_503_html_cuando_la_base_no_esta_disponible(
    metodo: str, ruta: str, datos: dict[str, object] | None
) -> None:
    cliente = _cliente(disponible=False)

    respuesta = cliente.get(ruta) if metodo == "get" else cliente.post(ruta, data=datos)

    assert respuesta.status_code == 503
    assert AVISO in respuesta.text
    assert "no está disponible" in _texto(respuesta.text)


def test_503_json_cuando_la_base_no_esta_disponible() -> None:
    cliente = _cliente(disponible=False)

    api = cliente.post(
        "/api/v1/consultas", json={"medicamento": "PARACETAMOL", "sintomas": ["FIEBRE"]}
    )
    salud = cliente.get("/salud")

    assert api.status_code == 503
    assert set(api.json()) == {"detalle"}
    assert salud.status_code == 503
    assert salud.json() == {"base_conocimiento": "no_disponible"}


def test_sin_regla_deriva_sin_reglas_aplicadas() -> None:
    respuesta = _cliente([]).post(
        "/api/v1/consultas", json={"medicamento": "IBUPROFENO", "sintomas": ["FIEBRE"]}
    )

    cuerpo = respuesta.json()
    assert cuerpo["nivel"] == "DERIVAR"
    assert cuerpo["nivel_etiqueta"] == "Derivar al médico"
    assert cuerpo["sin_regla"] is True
    assert cuerpo["reglas_aplicadas"] == []
