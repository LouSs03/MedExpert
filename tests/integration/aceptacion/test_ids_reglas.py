"""El `regla_id` de la biblioteca de casos (y del Apéndice B) coincide con la base de pruebas."""

from pathlib import Path
from typing import Any

import pytest
import yaml
from sqlalchemy import Engine

from infrastructure.db.postgres_regla_repository import PostgresReglaRepository

pytestmark = pytest.mark.integration

CASOS: list[dict[str, Any]] = yaml.safe_load(
    (Path(__file__).parent / "casos_reglas.yaml").read_text(encoding="utf-8")
)["casos"]


def test_ids_de_la_biblioteca_coinciden_con_las_reglas_cargadas(engine_pruebas: Engine) -> None:
    cargadas = {
        r.codigo: r.id
        for r in PostgresReglaRepository(engine_pruebas).listar_reglas_aprobadas_vigentes()
    }

    assert {c["codigo"]: c["regla_id"] for c in CASOS} == cargadas, (
        "casos_reglas.yaml y el Apéndice B ya no reflejan la base: regenerarlos"
    )
