"""Estado de la base de conocimiento."""

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from api.dependencias import get_base_opcional
from domain.base_conocimiento import BaseConocimiento

router = APIRouter()


@router.get("/salud")
def salud(
    base: Annotated[BaseConocimiento | None, Depends(get_base_opcional)],
) -> JSONResponse:
    """Indica si la base de conocimiento está disponible y cuántas reglas tiene cargadas."""
    if base is None:
        return JSONResponse(status_code=503, content={"base_conocimiento": "no_disponible"})
    return JSONResponse(content={"base_conocimiento": "disponible", "reglas": len(base.reglas)})
