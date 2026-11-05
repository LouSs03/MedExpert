"""Servidor real para las pruebas e2e, conectado SOLO a la base de pruebas (FR-021)."""

import os
import socket
import subprocess
import sys
import time
from collections.abc import Iterator
from pathlib import Path

import httpx
import pytest
from sqlalchemy.engine import URL

RAIZ = Path(__file__).resolve().parents[2]
ESPERA_MAXIMA_S = 60


def _puerto_libre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        puerto: int = s.getsockname()[1]
        return puerto


@pytest.fixture(scope="session")
def servidor(url_base_pruebas: URL) -> Iterator[str]:
    """Levanta la aplicación con DATABASE_URL = TEST_DATABASE_URL y devuelve su URL base."""
    puerto = _puerto_libre()
    entorno = os.environ.copy()
    # La URL viaja solo por el entorno del subproceso; nunca se imprime.
    entorno["DATABASE_URL"] = url_base_pruebas.render_as_string(hide_password=False)
    entorno["SALVAGUARDA_PENDIENTE_APROBACION"] = "true"
    proceso = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "api.main:create_app",
            "--factory",
            "--app-dir",
            "src",
            "--host",
            "127.0.0.1",
            "--port",
            str(puerto),
        ],
        cwd=RAIZ,
        env=entorno,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    base = f"http://127.0.0.1:{puerto}"
    try:
        limite = time.monotonic() + ESPERA_MAXIMA_S
        estado = None
        while time.monotonic() < limite:
            if proceso.poll() is not None:
                pytest.fail(
                    "El servidor terminó al arrancar (revise la configuración).", pytrace=False
                )
            try:
                estado = httpx.get(f"{base}/salud", timeout=2).status_code
                if estado == 200:
                    break
            except httpx.TransportError:
                pass
            time.sleep(0.5)
        if estado != 200:
            pytest.fail(
                f"El servidor no quedó disponible (último estado de /salud: {estado}).",
                pytrace=False,
            )
        yield base
    finally:
        proceso.terminate()
        try:
            proceso.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proceso.kill()
