"""Composición de la aplicación (raíz de composición).

Se arranca con `uvicorn api.main:create_app --factory --app-dir src`: no hay objeto `app` a nivel de
módulo, y el estado se asigna una sola vez en el ciclo de vida.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from api.dependencias import ServicioNoDisponible
from api.esquemas import AVISO, ErrorValidacionDTO
from api.routers import consulta, salud
from application.casos_uso.cargar_base_conocimiento import CargarBaseConocimiento
from domain.errores import BaseConocimientoNoDisponible
from domain.resolucion_nivel import ResolucionPorSeveridad
from infrastructure.config import cargar_configuracion
from infrastructure.db.engine import crear_engine
from infrastructure.db.postgres_regla_repository import PostgresReglaRepository
from infrastructure.inference.clips_motor_inferencia import ClipsMotorInferencia
from infrastructure.inference.fabrica_entorno import FabricaEntornoClips
from infrastructure.logging import configurar_logging

DIRECTORIO = Path(__file__).resolve().parent
logger = logging.getLogger(__name__)


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI) -> AsyncIterator[None]:
    """Carga configuración y base de conocimiento al arrancar; libera el engine al cerrar."""
    configuracion = cargar_configuracion()
    configurar_logging(configuracion)
    engine = crear_engine(configuracion.database_url)
    app.state.engine = engine
    app.state.salvaguarda = configuracion.salvaguarda
    app.state.estrategia = ResolucionPorSeveridad()
    try:
        base = CargarBaseConocimiento(PostgresReglaRepository(engine)).ejecutar()
        app.state.motor = ClipsMotorInferencia(FabricaEntornoClips(base.reglas))
        app.state.base = base
        logger.info("Base de conocimiento cargada: %d reglas aprobadas.", len(base.reglas))
    except (BaseConocimientoNoDisponible, ValueError) as error:
        motivo = error.motivo if isinstance(error, BaseConocimientoNoDisponible) else str(error)
        logger.error("Base de conocimiento no disponible: %s", motivo)
        app.state.base = None
    try:
        yield
    finally:
        engine.dispose()


def _es_api(request: Request) -> bool:
    return request.url.path.startswith("/api/") or request.url.path == "/salud"


async def _manejar_no_disponible(request: Request, _error: Exception) -> Response:
    if _es_api(request):
        return JSONResponse(
            status_code=503,
            content={"detalle": "La base de conocimiento no está disponible."},
        )
    plantillas: Jinja2Templates = request.app.state.plantillas
    return plantillas.TemplateResponse(
        request, "no_disponible.html", {"aviso": AVISO}, status_code=503
    )


async def _manejar_validacion(request: Request, error: Exception) -> Response:
    if not _es_api(request):
        assert isinstance(error, RequestValidationError)
        return await request_validation_exception_handler(request, error)
    cuerpo = ErrorValidacionDTO(
        detalle="La consulta no es válida: revise el medicamento y los síntomas.",
        valores_rechazados=[],
    )
    return JSONResponse(status_code=422, content=cuerpo.model_dump())


def create_app() -> FastAPI:
    """Crea la aplicación FastAPI con sus rutas, plantillas y manejadores de error."""
    app = FastAPI(title="MedExpert", lifespan=ciclo_de_vida)
    app.state.base = None
    app.state.plantillas = Jinja2Templates(directory=DIRECTORIO / "plantillas")
    app.mount("/estaticos", StaticFiles(directory=DIRECTORIO / "estaticos"), name="estaticos")
    app.mount("/static", StaticFiles(directory=DIRECTORIO / "static"), name="static")
    app.include_router(consulta.router)
    app.include_router(salud.router)
    app.add_exception_handler(ServicioNoDisponible, _manejar_no_disponible)
    app.add_exception_handler(RequestValidationError, _manejar_validacion)
    return app
