"""DTOs de entrada y salida de la API (contracts/http.md).

Las entidades del dominio nunca se exponen directamente.
"""

from pydantic import BaseModel, Field, field_validator

from domain.consulta import ResultadoEvaluacion

AVISO = "Prototipo académico: no reemplaza la consulta médica o farmacéutica."


class ConsultaEntradaDTO(BaseModel):
    """Datos de una consulta: un medicamento, al menos un síntoma y cero o más condiciones."""

    medicamento: str
    sintomas: list[str] = Field(min_length=1)
    condiciones: list[str] = Field(default_factory=list)

    @field_validator("sintomas", "condiciones")
    @classmethod
    def _sin_duplicados(cls, valores: list[str]) -> list[str]:
        return list(dict.fromkeys(valores))


class SintomaDTO(BaseModel):
    """Síntoma con su código y su nombre visible."""

    codigo: str
    nombre: str


class ReglaAplicadaDTO(BaseModel):
    """Regla disparada con sus mensajes aprobados, en el orden de FR-009."""

    codigo: str
    version: int
    nivel: str
    especificidad: int
    mensajes: list[str]


class MensajeSistemaDTO(BaseModel):
    """Mensaje del sistema (no proviene de una regla validada)."""

    tipo: str
    texto: str
    pendiente_aprobacion: bool
    sintoma: str | None


class ResultadoDTO(BaseModel):
    """Resultado de una consulta tal como lo recibe la persona usuaria."""

    nivel: str
    nivel_etiqueta: str
    sin_regla: bool
    reglas_aplicadas: list[ReglaAplicadaDTO]
    salvaguarda_activada: bool
    sintomas_no_cubiertos: list[SintomaDTO]
    mensajes_sistema: list[MensajeSistemaDTO]
    persistida: bool
    aviso: str = AVISO


class ErrorValidacionDTO(BaseModel):
    """Error de una consulta que no se evaluó por datos no válidos (FR-005)."""

    detalle: str
    valores_rechazados: list[str]


def a_resultado_dto(resultado: ResultadoEvaluacion) -> ResultadoDTO:
    """Traduce el resultado del dominio al DTO de salida."""
    return ResultadoDTO(
        nivel=resultado.nivel.value,
        nivel_etiqueta=resultado.nivel.etiqueta,
        sin_regla=resultado.sin_regla,
        reglas_aplicadas=[
            ReglaAplicadaDTO(
                codigo=d.regla.codigo,
                version=d.regla.version,
                nivel=d.regla.nivel.value,
                especificidad=d.regla.especificidad,
                mensajes=list(d.regla.mensajes),
            )
            for d in resultado.reglas_disparadas
        ],
        salvaguarda_activada=resultado.salvaguarda_activada,
        sintomas_no_cubiertos=[
            SintomaDTO(codigo=s.codigo, nombre=s.nombre) for s in resultado.sintomas_no_cubiertos
        ],
        mensajes_sistema=[
            MensajeSistemaDTO(
                tipo=m.tipo.value,
                texto=m.texto,
                pendiente_aprobacion=m.pendiente_aprobacion,
                sintoma=m.sintoma.codigo if m.sintoma else None,
            )
            for m in resultado.mensajes_sistema
        ],
        persistida=resultado.persistida,
    )
