"""Proveedores para `Depends` (Principio V).

Los routers nunca instancian repositorios ni el motor: los reciben de aquí.
"""

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Request
from fastapi.templating import Jinja2Templates

from application.casos_uso.evaluar_consulta import EvaluarConsulta
from domain.base_conocimiento import BaseConocimiento
from domain.vocabulario import Vocabulario
from infrastructure.db.engine import Sesion, get_session
from infrastructure.db.postgres_consulta_repository import PostgresConsultaRepository


class ServicioNoDisponible(Exception):
    """La base de conocimiento no está cargada: no se ofrecen evaluaciones (FR-018)."""


def get_base_opcional(request: Request) -> BaseConocimiento | None:
    """Devuelve la base de conocimiento cargada al arrancar, o None si no está disponible."""
    base: BaseConocimiento | None = getattr(request.app.state, "base", None)
    return base


def get_base(
    base: Annotated[BaseConocimiento | None, Depends(get_base_opcional)],
) -> BaseConocimiento:
    """Devuelve la base de conocimiento o lanza ServicioNoDisponible."""
    if base is None:
        raise ServicioNoDisponible
    return base


def get_vocabulario(base: Annotated[BaseConocimiento, Depends(get_base)]) -> Vocabulario:
    """Devuelve el vocabulario cerrado de la base cargada."""
    return base.vocabulario


def get_plantillas(request: Request) -> Jinja2Templates:
    """Devuelve el motor de plantillas configurado en la aplicación."""
    plantillas: Jinja2Templates = request.app.state.plantillas
    return plantillas


def get_sesion(request: Request) -> Iterator[Sesion]:
    """Entrega una sesión de base de datos por petición."""
    yield from get_session(request.app.state.engine)


def get_evaluar_consulta(
    request: Request,
    base: Annotated[BaseConocimiento, Depends(get_base)],
    sesion: Annotated[Sesion, Depends(get_sesion)],
) -> EvaluarConsulta:
    """Arma el caso de uso EvaluarConsulta con los componentes creados al arrancar."""
    estado = request.app.state
    return EvaluarConsulta(
        vocabulario=base.vocabulario,
        motor=estado.motor,
        estrategia=estado.estrategia,
        consultas=PostgresConsultaRepository(sesion),
        salvaguarda=estado.salvaguarda,
    )
