"""Rutas de la consulta: portada, tres pasos, resultado HTML y API JSON (contracts/http.md)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Form, Path, Query, Request
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
from api.pasos import ERRORES_POR_PASO, Estado, contexto_paso, paso_con_error
from api.resultado import contexto_resultado
from application.casos_uso.evaluar_consulta import EvaluarConsulta
from domain.base_conocimiento import BaseConocimiento
from domain.errores import VocabularioInvalido
from domain.vocabulario import Vocabulario

router = APIRouter(dependencies=[Depends(get_base)])

CABECERA_PERSISTIDA = "X-Consulta-Persistida"

Plantillas = Annotated[Jinja2Templates, Depends(get_plantillas)]
VocabularioDep = Annotated[Vocabulario, Depends(get_vocabulario)]
BaseDep = Annotated[BaseConocimiento, Depends(get_base)]
ListaQuery = Annotated[list[str] | None, Query()]
CasoDeUso = Annotated[EvaluarConsulta, Depends(get_evaluar_consulta)]


def _marcar_persistencia(respuesta: Response, persistida: bool) -> None:
    """Añade la marca interna de persistencia (FR-019); no se muestra como texto."""
    respuesta.headers[CABECERA_PERSISTIDA] = "true" if persistida else "false"


def _paso(
    request: Request,
    plantillas: Jinja2Templates,
    paso: int,
    vocabulario: Vocabulario,
    estado: Estado,
    errores: tuple[str, ...] = (),
    status_code: int = 200,
) -> HTMLResponse:
    return plantillas.TemplateResponse(
        request,
        "paso.html",
        {"aviso": AVISO, **contexto_paso(paso, vocabulario, estado, errores)},
        status_code=status_code,
    )


def _paso_o_error(
    request: Request,
    plantillas: Jinja2Templates,
    paso: int,
    vocabulario: Vocabulario,
    estado: Estado,
) -> HTMLResponse:
    """Muestra el paso pedido o, si falta algo de un paso anterior, ese paso con el error."""
    invalido = paso_con_error(vocabulario, estado, hasta=paso)
    if invalido is not None:
        errores = (ERRORES_POR_PASO[invalido],)
        return _paso(request, plantillas, invalido, vocabulario, estado, errores, 422)
    return _paso(request, plantillas, paso, vocabulario, estado)


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


@router.get("/consulta/paso/{paso}", response_class=HTMLResponse)
def mostrar_paso(
    request: Request,
    plantillas: Plantillas,
    vocabulario: VocabularioDep,
    paso: Annotated[int, Path(ge=1, le=3)],
    medicamento: str | None = None,
    sintomas: ListaQuery = None,
    condiciones: ListaQuery = None,
    ninguna: bool = False,
) -> HTMLResponse:
    """Muestra el paso 1 (medicamento), 2 (síntomas) o 3 (condiciones) con el estado de la URL."""
    estado = Estado.desde(medicamento, sintomas, condiciones, ninguna)
    return _paso_o_error(request, plantillas, paso, vocabulario, estado)


@router.post("/consulta", response_class=HTMLResponse)
def consultar_formulario(
    request: Request,
    plantillas: Plantillas,
    base: BaseDep,
    caso: CasoDeUso,
    medicamento: Annotated[str | None, Form()] = None,
    sintomas: Annotated[list[str] | None, Form()] = None,
    condiciones: Annotated[list[str] | None, Form()] = None,
    ninguna: Annotated[bool, Form()] = False,
) -> HTMLResponse:
    """Evalúa la consulta del formulario y muestra el resultado o los errores de validación."""
    try:
        resultado = caso.ejecutar(medicamento, sintomas or [], condiciones or [])
    except VocabularioInvalido as error:
        estado = Estado.desde(medicamento, sintomas, condiciones, ninguna)
        paso = paso_con_error(base.vocabulario, estado, hasta=4) or 3
        return _paso(request, plantillas, paso, base.vocabulario, estado, error.problemas, 422)
    contexto = contexto_resultado(
        a_resultado_dto(resultado),
        base.vocabulario,
        medicamento,
        sintomas or [],
        condiciones or [],
        ninguna,
        reglas_en_base=len(base.reglas),
    )
    respuesta = plantillas.TemplateResponse(request, "resultado.html", {"aviso": AVISO, **contexto})
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
