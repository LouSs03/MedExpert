"""Mensajes del sistema autorizados por los Principios I y II de la constitución.

Son los únicos textos orientativos que no provienen de una regla aprobada. Su texto literal está
fijado en la especificación (FR-011 y FR-020).
"""

from dataclasses import dataclass
from enum import Enum

from domain.vocabulario import Medicamento, Sintoma

TEXTO_COMBINACION_NO_CUBIERTA = (
    "Esta combinación de medicamento, síntomas y condiciones no está cubierta por la base de "
    "conocimiento validada. Consulte con un médico."
)
PLANTILLA_SINTOMA_NO_CUBIERTO = (
    "«{sintoma}» no tiene orientación específica con {medicamento} en la base de conocimiento "
    "validada. Consulte a un médico o farmacéutico."
)


class TipoMensajeSistema(Enum):
    """Tipos de mensaje del sistema."""

    COMBINACION_NO_CUBIERTA = "COMBINACION_NO_CUBIERTA"
    SINTOMA_NO_CUBIERTO = "SINTOMA_NO_CUBIERTO"


@dataclass(frozen=True)
class ConfiguracionSalvaguarda:
    """Indica si el texto de la salvaguarda sigue pendiente de aprobación del médico."""

    pendiente_aprobacion: bool = True


@dataclass(frozen=True)
class MensajeSistema:
    """Mensaje que solo remite a un profesional y no proviene de ninguna regla."""

    tipo: TipoMensajeSistema
    texto: str
    pendiente_aprobacion: bool
    sintoma: Sintoma | None = None


def mensaje_combinacion_no_cubierta() -> MensajeSistema:
    """Devuelve el mensaje que se muestra cuando no se dispara ninguna regla (FR-011)."""
    return MensajeSistema(
        tipo=TipoMensajeSistema.COMBINACION_NO_CUBIERTA,
        texto=TEXTO_COMBINACION_NO_CUBIERTA,
        pendiente_aprobacion=False,
    )


def mensaje_sintoma_no_cubierto(
    sintoma: Sintoma, medicamento: Medicamento, configuracion: ConfiguracionSalvaguarda
) -> MensajeSistema:
    """Devuelve el mensaje de salvaguarda para un síntoma sin regla aplicable (FR-020)."""
    return MensajeSistema(
        tipo=TipoMensajeSistema.SINTOMA_NO_CUBIERTO,
        texto=PLANTILLA_SINTOMA_NO_CUBIERTO.format(
            sintoma=sintoma.nombre, medicamento=medicamento.nombre
        ),
        pendiente_aprobacion=configuracion.pendiente_aprobacion,
        sintoma=sintoma,
    )
