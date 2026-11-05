"""Aceptación de la base de conocimiento: un caso por regla aprobada (SC-001, Principio VIII).

Biblioteca indexada de casos de prueba (Buchanan y Shortliffe, 1984): se ejecuta completa en cada
cambio como regresión.
"""

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
import yaml
from sqlalchemy import Engine, text

from application.casos_uso.cargar_base_conocimiento import CargarBaseConocimiento
from application.casos_uso.evaluar_consulta import EvaluarConsulta
from domain.base_conocimiento import BaseConocimiento
from domain.mensajes_sistema import (
    TEXTO_COMBINACION_NO_CUBIERTA,
    ConfiguracionSalvaguarda,
    TipoMensajeSistema,
)
from domain.nivel import Nivel
from domain.resolucion_nivel import ResolucionPorSeveridad
from fakes.repositorios import ConsultaRepositoryEnMemoria
from infrastructure.db.postgres_regla_repository import PostgresReglaRepository
from infrastructure.inference.clips_motor_inferencia import ClipsMotorInferencia
from infrastructure.inference.fabrica_entorno import FabricaEntornoClips

pytestmark = pytest.mark.aceptacion

BIBLIOTECA: dict[str, Any] = yaml.safe_load(
    (Path(__file__).parent / "casos_reglas.yaml").read_text(encoding="utf-8")
)
CASOS: list[dict[str, Any]] = BIBLIOTECA["casos"]
NO_CUBIERTOS: list[dict[str, Any]] = BIBLIOTECA["no_cubiertos"]


@pytest.fixture(scope="module")
def base(engine_pruebas: Engine) -> BaseConocimiento:
    return CargarBaseConocimiento(PostgresReglaRepository(engine_pruebas)).ejecutar()


@pytest.fixture(scope="module")
def evaluar(base: BaseConocimiento) -> Iterator[EvaluarConsulta]:
    yield EvaluarConsulta(
        vocabulario=base.vocabulario,
        motor=ClipsMotorInferencia(FabricaEntornoClips(base.reglas)),
        estrategia=ResolucionPorSeveridad(),
        consultas=ConsultaRepositoryEnMemoria(),
        salvaguarda=ConfiguracionSalvaguarda(),
    )


def test_la_biblioteca_cubre_las_30_reglas(base: BaseConocimiento) -> None:
    assert sorted(c["codigo"] for c in CASOS) == sorted(r.codigo for r in base.reglas)


@pytest.mark.parametrize("caso", CASOS, ids=[c["codigo"] for c in CASOS])
def test_caso_de_aceptacion(
    caso: dict[str, Any], evaluar: EvaluarConsulta, engine_pruebas: Engine
) -> None:
    resultado = evaluar.ejecutar(caso["medicamento"], caso["sintomas"], caso["condiciones"])

    assert resultado.nivel is Nivel(caso["nivel_esperado"])
    assert [d.regla.codigo for d in resultado.reglas_disparadas] == caso["reglas_esperadas"]
    assert resultado.salvaguarda_activada is caso["salvaguarda"]

    propia = next(d.regla for d in resultado.reglas_disparadas if d.regla.codigo == caso["codigo"])
    with engine_pruebas.connect() as conexion:
        aprobados = (
            conexion.execute(
                text("select texto from regla_mensaje where regla_id = :id order by orden"),
                {"id": propia.id},
            )
            .scalars()
            .all()
        )
    assert aprobados
    assert list(propia.mensajes) == aprobados


@pytest.mark.parametrize("caso", NO_CUBIERTOS, ids=[c["id"] for c in NO_CUBIERTOS])
def test_combinacion_no_cubierta(caso: dict[str, Any], evaluar: EvaluarConsulta) -> None:
    resultado = evaluar.ejecutar(caso["medicamento"], caso["sintomas"], caso["condiciones"])

    assert resultado.nivel is Nivel(caso["nivel_esperado"])
    assert resultado.sin_regla is caso["sin_regla"]
    assert resultado.reglas_disparadas == ()
    (mensaje,) = resultado.mensajes_sistema
    assert mensaje.tipo is TipoMensajeSistema.COMBINACION_NO_CUBIERTA
    assert mensaje.texto == TEXTO_COMBINACION_NO_CUBIERTA
