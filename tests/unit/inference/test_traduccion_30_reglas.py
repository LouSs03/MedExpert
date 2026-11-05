"""Traducción exacta y disparo de cada una de las 30 reglas (Principio VIII, unitarias; sin base).

Las reglas se reconstruyen a partir de la biblioteca de casos (casos_reglas.yaml) y el texto
esperado es el del Apéndice B de tasks.md (defrules_esperados.clp).
"""

import re
from pathlib import Path
from typing import Any

import clips
import pytest
import yaml

from domain.nivel import EstadoRegla, Nivel
from domain.regla import Regla
from infrastructure.inference.traductor_reglas import TraductorReglasClips

RAIZ_TESTS = Path(__file__).resolve().parents[2]
CASOS: list[dict[str, Any]] = yaml.safe_load(
    (RAIZ_TESTS / "integration" / "aceptacion" / "casos_reglas.yaml").read_text(encoding="utf-8")
)["casos"]
ESPERADOS: dict[str, str] = {
    re.match(r"\(defrule (R\d\d)-v\d+", bloque).group(1): bloque.strip()  # type: ignore[union-attr]
    for bloque in (Path(__file__).parent / "defrules_esperados.clp")
    .read_text(encoding="utf-8")
    .strip()
    .split("\n\n")
}
TRADUCTOR = TraductorReglasClips()


def _regla(caso: dict[str, Any]) -> Regla:
    return Regla(
        id=caso["regla_id"],
        codigo=caso["codigo"],
        version=1,
        medicamento=caso["medicamento"],
        sintomas=frozenset(caso["sintomas"]),
        condiciones=frozenset(caso["condiciones"]),
        sin_condiciones=not caso["condiciones"],
        especificidad=len(caso["sintomas"]) + len(caso["condiciones"]),
        nivel=Nivel(caso["nivel_esperado"]),
        estado=EstadoRegla.APROBADA,
        mensajes=("Mensaje de prueba.",),
    )


def test_hay_30_casos_y_30_defrules() -> None:
    assert len(CASOS) == 30
    assert sorted(ESPERADOS) == [c["codigo"] for c in CASOS]


@pytest.mark.parametrize("caso", CASOS, ids=[c["codigo"] for c in CASOS])
def test_traduccion_exacta_y_disparo(caso: dict[str, Any]) -> None:
    regla = _regla(caso)
    texto = TRADUCTOR.traducir(regla)

    assert texto == ESPERADOS[caso["codigo"]]

    entorno = clips.Environment()
    for plantilla in TRADUCTOR.plantillas():
        entorno.build(plantilla)
    entorno.build(texto)
    entorno.assert_string(f"(medicamento (codigo {caso['medicamento']}))")
    for sintoma in caso["sintomas"]:
        entorno.assert_string(f"(sintoma (codigo {sintoma}))")
    for condicion in caso["condiciones"]:
        entorno.assert_string(f"(condicion (codigo {condicion}))")
    entorno.run(1000)

    disparos = [f["regla-id"] for f in entorno.facts() if f.template.name == "disparo"]
    assert disparos == [caso["regla_id"]]
