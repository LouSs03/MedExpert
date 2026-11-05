"""Fixtures compartidas y guarda de la base de pruebas (FR-021, SC-011).

Las pruebas que usan la base nunca tocan la base real: solo `TEST_DATABASE_URL`, que debe ser
distinta de `DATABASE_URL`. Ningún mensaje de este módulo muestra las URL.
"""

import os
from collections.abc import Iterator

import pytest
from dotenv import load_dotenv
from sqlalchemy import Engine
from sqlalchemy.engine import URL, make_url
from sqlmodel import Session

from infrastructure.db.engine import crear_engine

# Antes de cualquier guarda: así DATABASE_URL y TEST_DATABASE_URL de `.env` son visibles.
load_dotenv(override=False)

GUIA = "Vea docs/base-de-pruebas.md."


def interpretar_url(valor: str) -> URL | None:
    """Devuelve la URL interpretada, o None si no tiene un formato válido (sin mostrarla)."""
    try:
        return make_url(valor)
    except Exception:
        return None


def misma_base(a: URL, b: URL) -> bool:
    """Indica si dos URL apuntan al mismo host, puerto y base de datos."""
    return (
        (a.host or "").lower() == (b.host or "").lower()
        and (a.port or 5432) == (b.port or 5432)
        and (a.database or "") == (b.database or "")
    )


def para_sqlalchemy(url: URL) -> URL:
    """Devuelve la URL con el driver psycopg que usa la aplicación."""
    return url.set(drivername="postgresql+psycopg")


@pytest.fixture(scope="session")
def url_base_pruebas() -> URL:
    """URL de la base de pruebas, verificada como distinta de la base real.

    Es un objeto `URL` y no un texto: su `repr` oculta la contraseña, así que no se filtra en los
    informes de pytest cuando falla una prueba.
    """
    real = os.environ.get("DATABASE_URL", "").strip()
    prueba = os.environ.get("TEST_DATABASE_URL", "").strip()
    if not prueba:
        pytest.fail(f"Falta TEST_DATABASE_URL. {GUIA}", pytrace=False)
    if not real:
        pytest.fail(
            "Falta DATABASE_URL: sin ella no se puede verificar que la base de pruebas sea "
            f"distinta de la real. {GUIA}",
            pytrace=False,
        )

    url_real = interpretar_url(real)
    url_prueba = interpretar_url(prueba)
    if url_real is None or url_prueba is None:
        cual = "DATABASE_URL" if url_real is None else "TEST_DATABASE_URL"
        pytest.fail(f"{cual} no tiene un formato de URL válido. {GUIA}", pytrace=False)
    if not url_prueba.drivername.startswith("postgresql"):
        pytest.fail(f"TEST_DATABASE_URL debe ser una URL de PostgreSQL. {GUIA}", pytrace=False)
    if misma_base(url_real, url_prueba):
        pytest.exit(
            "TEST_DATABASE_URL apunta a la misma base que DATABASE_URL: se aborta para no "
            "tocar la base real (FR-021).",
            returncode=3,
        )
    return para_sqlalchemy(url_prueba)


@pytest.fixture(scope="session")
def engine_pruebas(url_base_pruebas: URL) -> Iterator[Engine]:
    """Engine conectado a la base de pruebas."""
    engine = crear_engine(url_base_pruebas)
    yield engine
    engine.dispose()


@pytest.fixture
def sesion_rollback(engine_pruebas: Engine) -> Iterator[Session]:
    """Sesión dentro de una transacción externa que se deshace al terminar la prueba."""
    conexion = engine_pruebas.connect()
    transaccion = conexion.begin()
    sesion = Session(bind=conexion, join_transaction_mode="create_savepoint")
    try:
        yield sesion
    finally:
        sesion.close()
        transaccion.rollback()
        conexion.close()
