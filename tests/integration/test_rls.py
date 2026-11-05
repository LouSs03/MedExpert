"""RLS activo en todas las tablas de public (Principio X), verificado en la base de pruebas.

La base de pruebas se crea con `pg_dump --schema-only` de la real (docs/base-de-pruebas.md) y
conserva su RLS; FR-021 impide ejecutar esta prueba contra la base real.
"""

import pytest
from sqlalchemy import Engine, text

pytestmark = pytest.mark.integration


def test_rls_activo_en_todas_las_tablas_de_public(engine_pruebas: Engine) -> None:
    with engine_pruebas.connect() as conexion:
        tablas = dict(
            conexion.execute(
                text(
                    "select c.relname, c.relrowsecurity from pg_class c "
                    "join pg_namespace n on n.oid = c.relnamespace "
                    "where n.nspname = 'public' and c.relkind = 'r'"
                )
            ).all()
        )

    assert len(tablas) == 11
    assert [nombre for nombre, rls in tablas.items() if not rls] == []
