"""Rutas de la consulta de orientación: formulario HTML y API JSON (contracts/http.md)."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.templating import Jinja2Templates

from api.dependencias import get_base, get_evaluar_consulta, get_plantillas, get_vocabulario
from api.esquemas import (
    AVISO,
    ConsultaEntradaDTO,
    ErrorValidacionDTO,
    ResultadoDTO,
    a_resultado_dto,
)
from application.casos_uso.evaluar_consulta import EvaluarConsulta
from domain.base_conocimiento import BaseConocimiento
from domain.errores import VocabularioInvalido
from domain.vocabulario import Vocabulario

router = APIRouter(dependencies=[Depends(get_base)])

CABECERA_PERSISTIDA = "X-Consulta-Persistida"

Plantillas = Annotated[Jinja2Templates, Depends(get_plantillas)]
VocabularioDep = Annotated[Vocabulario, Depends(get_vocabulario)]
BaseDep = Annotated[BaseConocimiento, Depends(get_base)]
CasoDeUso = Annotated[EvaluarConsulta, Depends(get_evaluar_consulta)]


def _marcar_persistencia(respuesta: Response, persistida: bool) -> None:
    """Añade la marca interna de persistencia (FR-019); no se muestra como texto."""
    respuesta.headers[CABECERA_PERSISTIDA] = "true" if persistida else "false"


def _formulario(
    request: Request,
    plantillas: Jinja2Templates,
    vocabulario: Vocabulario,
    seleccion: dict[str, Any] | None = None,
    errores: tuple[str, ...] = (),
    status_code: int = 200,
) -> HTMLResponse:
    return plantillas.TemplateResponse(
        request,
        "formulario.html",
        {
            "aviso": AVISO,
            "vocabulario": vocabulario,
            "seleccion": seleccion or {"medicamento": None, "sintomas": [], "condiciones": []},
            "errores": errores,
        },
        status_code=status_code,
    )


def _enumerar(nombres: list[str]) -> str:
    """Une nombres en español: «A», «A y B», «A, B y C» («e» ante sonido /i/)."""
    if len(nombres) <= 1:
        return "".join(nombres)
    ultimo = nombres[-1]
    conjuncion = "e" if ultimo.lower().startswith(("i", "hi")) else "y"
    return f"{', '.join(nombres[:-1])} {conjuncion} {ultimo}"


@router.get("/", response_class=HTMLResponse)
def mostrar_portada(request: Request, plantillas: Plantillas, base: BaseDep) -> HTMLResponse:
    """Muestra la portada con cifras reales de la base de conocimiento cargada."""
    vocabulario = base.vocabulario
    return plantillas.TemplateResponse(
        request,
        "portada.html",
        {
            "aviso": AVISO,
            "num_reglas": len(base.reglas),
            "medicamentos": _enumerar([m.nombre for m in vocabulario.medicamentos]),
            "num_medicamentos": len(vocabulario.medicamentos),
            "num_sintomas": len(vocabulario.sintomas),
            "num_condiciones": len(vocabulario.condiciones),
        },
    )


@router.get("/consulta/paso/1", response_class=HTMLResponse)
def mostrar_formulario(
    request: Request, plantillas: Plantillas, vocabulario: VocabularioDep
) -> HTMLResponse:
    """Muestra el formulario de consulta generado a partir del vocabulario."""
    return _formulario(request, plantillas, vocabulario)


@router.post("/consulta", response_class=HTMLResponse)
def consultar_formulario(
    request: Request,
    plantillas: Plantillas,
    vocabulario: VocabularioDep,
    caso: CasoDeUso,
    medicamento: Annotated[str | None, Form()] = None,
    sintomas: Annotated[list[str] | None, Form()] = None,
    condiciones: Annotated[list[str] | None, Form()] = None,
) -> HTMLResponse:
    """Evalúa la consulta del formulario y muestra el resultado o los errores de validación."""
    try:
        resultado = caso.ejecutar(medicamento, sintomas or [], condiciones or [])
    except VocabularioInvalido as error:
        seleccion = {
            "medicamento": medicamento,
            "sintomas": sintomas or [],
            "condiciones": condiciones or [],
        }
        return _formulario(request, plantillas, vocabulario, seleccion, error.problemas, 422)
    respuesta = plantillas.TemplateResponse(
        request, "resultado.html", {"aviso": AVISO, "resultado": a_resultado_dto(resultado)}
    )
    _marcar_persistencia(respuesta, resultado.persistida)
    return respuesta


@router.post(
    "/api/v1/consultas",
    response_model=ResultadoDTO,
    responses={422: {"model": ErrorValidacionDTO}},
)
def consultar_api(
    entrada: ConsultaEntradaDTO, caso: CasoDeUso, respuesta: Response
) -> Response | ResultadoDTO:
    """Evalúa una consulta en JSON y devuelve el ResultadoDTO."""
    try:
        resultado = caso.ejecutar(entrada.medicamento, entrada.sintomas, entrada.condiciones)
    except VocabularioInvalido as error:
        cuerpo = ErrorValidacionDTO(
            detalle=" ".join(error.problemas) or "La consulta contiene valores no reconocidos.",
            valores_rechazados=list(error.valores_rechazados),
        )
        return JSONResponse(status_code=422, content=cuerpo.model_dump())
    _marcar_persistencia(respuesta, resultado.persistida)
    return a_resultado_dto(resultado)
