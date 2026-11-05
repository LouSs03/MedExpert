"""Conexión a PostgreSQL mediante SQLModel/SQLAlchemy."""

from collections.abc import Iterator

from sqlalchemy import URL, Engine
from sqlmodel import Session, create_engine

Sesion = Session
"""Tipo de la sesión de base de datos, para anotar dependencias fuera de `infrastructure/db`."""


TIEMPO_LIMITE_CONEXION_S = 10
"""Segundos máximos por intento de conexión: sin límite, una base que no responde colgaría el
arranque en lugar de servir 503 (FR-018)."""


def crear_engine(database_url: str | URL) -> Engine:
    """Crea el engine de la base de datos.

    Nunca registra la URL ni los parámetros de las consultas.
    """
    return create_engine(
        database_url,
        pool_pre_ping=True,
        hide_parameters=True,
        echo=False,
        connect_args={"connect_timeout": TIEMPO_LIMITE_CONEXION_S},
    )


def get_session(engine: Engine) -> Iterator[Session]:
    """Entrega una sesión de base de datos y la cierra al terminar."""
    with Session(engine) as sesion:
        yield sesion
