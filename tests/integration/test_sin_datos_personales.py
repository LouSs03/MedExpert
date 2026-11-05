"""El registro de consultas no tiene columnas para datos personales (FR-015, SC-006)."""

import pytest
from sqlalchemy import Engine, text

pytestmark = pytest.mark.integration

TABLAS = ("consulta", "consulta_sintoma", "consulta_condicion", "consulta_regla_disparada")
PERMITIDAS = {
    "id",
    "creado_en",
    "medicamento_id",
    "nivel_resultado",
    "sin_regla",
    "consulta_id",
    "sintoma_id",
    "condicion_id",
    "regla_id",
    "orden",
}


def test_columnas_del_registro_son_exactamente_las_permitidas(engine_pruebas: Engine) -> None:
    with engine_pruebas.connect() as conexion:
        columnas = set(
            conexion.execute(
                text(
                    "select column_name from information_schema.columns "
                    "where table_schema = 'public' and table_name = any(:tablas)"
                ),
                {"tablas": list(TABLAS)},
            ).scalars()
        )

    assert columnas == PERMITIDAS
