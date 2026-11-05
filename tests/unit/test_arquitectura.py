"""Regla de dependencia de la arquitectura hexagonal (Principios IV y V de la constitución)."""

import ast
import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
STDLIB = frozenset(sys.stdlib_module_names)
CAPAS = ("domain", "application", "infrastructure", "api")
LIBRERIAS_BD = frozenset({"sqlmodel", "sqlalchemy", "psycopg"})


def _imports(fuente: str) -> list[str]:
    """Devuelve los nombres completos de los módulos importados de forma absoluta."""
    nombres: list[str] = []
    for nodo in ast.walk(ast.parse(fuente)):
        if isinstance(nodo, ast.Import):
            nombres.extend(alias.name for alias in nodo.names)
        elif isinstance(nodo, ast.ImportFrom) and nodo.level == 0 and nodo.module:
            nombres.append(nodo.module)
    return nombres


def violaciones(ruta_relativa: str, fuente: str) -> list[str]:
    """Devuelve las violaciones de la regla de dependencia de un archivo de `src/`."""
    partes = Path(ruta_relativa).with_suffix("").parts
    capa = partes[0]
    subcapa = "/".join(partes[:2])
    encontradas: list[str] = []
    for modulo in _imports(fuente):
        raiz = modulo.split(".")[0]
        if capa == "domain" and raiz not in STDLIB and raiz != "domain":
            encontradas.append(f"{ruta_relativa}: domain importa {modulo}")
        if capa == "application" and raiz not in STDLIB and raiz not in {"domain", "application"}:
            encontradas.append(f"{ruta_relativa}: application importa {modulo}")
        if raiz == "clips" and subcapa != "infrastructure/inference":
            encontradas.append(f"{ruta_relativa}: clips fuera de infrastructure/inference")
        if raiz in LIBRERIAS_BD and subcapa != "infrastructure/db":
            encontradas.append(f"{ruta_relativa}: {raiz} fuera de infrastructure/db")
        if capa == "infrastructure" and raiz == "api":
            encontradas.append(f"{ruta_relativa}: infrastructure importa api")
        if subcapa == "api/routers" and raiz == "infrastructure":
            encontradas.append(f"{ruta_relativa}: un router importa infrastructure")
    return encontradas


def _archivos_src() -> list[Path]:
    return sorted(p for p in SRC.rglob("*.py") if p.relative_to(SRC).parts[0] in CAPAS)


def test_existen_las_cuatro_capas() -> None:
    for capa in CAPAS:
        assert (SRC / capa / "__init__.py").is_file(), capa


def test_src_respeta_la_regla_de_dependencia() -> None:
    archivos = _archivos_src()
    assert archivos, "no se encontraron módulos en src/"
    encontradas = [
        v
        for archivo in archivos
        for v in violaciones(
            archivo.relative_to(SRC).as_posix(), archivo.read_text(encoding="utf-8")
        )
    ]
    assert encontradas == []


@pytest.mark.parametrize(
    "ruta, fuente",
    [
        ("domain/x.py", "import fastapi"),
        ("domain/x.py", "from application.ports import y"),
        ("domain/x.py", "from sqlmodel import Field"),
        ("application/x.py", "from infrastructure.db import engine"),
        ("application/x.py", "import pydantic"),
        ("api/main.py", "import clips"),
        ("infrastructure/db/x.py", "import clips"),
        ("infrastructure/inference/x.py", "from sqlalchemy import text"),
        ("api/esquemas.py", "import psycopg"),
        ("infrastructure/config.py", "from api.main import create_app"),
        ("api/routers/consulta.py", "from infrastructure.db.engine import crear_engine"),
    ],
)
def test_detecta_cada_tipo_de_violacion(ruta: str, fuente: str) -> None:
    assert violaciones(ruta, fuente)


@pytest.mark.parametrize(
    "ruta, fuente",
    [
        ("domain/x.py", "from dataclasses import dataclass\nfrom domain.nivel import Nivel"),
        ("application/x.py", "import logging\nfrom domain.regla import Regla"),
        ("infrastructure/inference/x.py", "import clips\nfrom domain.regla import Regla"),
        ("infrastructure/db/x.py", "from sqlmodel import Session"),
        ("api/dependencias.py", "from infrastructure.db.engine import get_session"),
        ("api/routers/consulta.py", "from application.casos_uso import evaluar_consulta"),
    ],
)
def test_admite_las_dependencias_permitidas(ruta: str, fuente: str) -> None:
    assert violaciones(ruta, fuente) == []
