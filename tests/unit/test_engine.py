"""El engine fija un tiempo límite de conexión: si la base no responde, el arranque no se cuelga
y la aplicación sirve 503 (FR-018)."""

from typing import Any

import pytest

from infrastructure.db import engine as modulo_engine


def test_crear_engine_fija_tiempo_limite_de_conexion(monkeypatch: pytest.MonkeyPatch) -> None:
    capturado: dict[str, Any] = {}

    def falso_create_engine(url: object, **kwargs: Any) -> str:
        capturado.update(kwargs)
        return "engine"

    monkeypatch.setattr(modulo_engine, "create_engine", falso_create_engine)

    modulo_engine.crear_engine("postgresql+psycopg://u:x@host/db")

    assert capturado["connect_args"]["connect_timeout"] == modulo_engine.TIEMPO_LIMITE_CONEXION_S
    assert 0 < modulo_engine.TIEMPO_LIMITE_CONEXION_S <= 15
    assert capturado["pool_pre_ping"] is True
    assert capturado["hide_parameters"] is True
