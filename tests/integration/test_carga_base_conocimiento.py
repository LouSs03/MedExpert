"""Carga completa de la base de conocimiento en el motor (Principio VIII, integración)."""

import pytest
from sqlalchemy import Engine

from application.casos_uso.cargar_base_conocimiento import CargarBaseConocimiento
from infrastructure.db.postgres_regla_repository import PostgresReglaRepository
from infrastructure.inference.fabrica_entorno import FabricaEntornoClips

pytestmark = pytest.mark.integration


def test_carga_las_30_reglas_y_las_construye_en_clips(engine_pruebas: Engine) -> None:
    base = CargarBaseConocimiento(PostgresReglaRepository(engine_pruebas)).ejecutar()

    assert len(base.reglas) == 30
    entorno = FabricaEntornoClips(base.reglas).crear()
    assert sorted(r.name for r in entorno.rules()) == sorted(
        f"{r.codigo}-v{r.version}" for r in base.reglas
    )
