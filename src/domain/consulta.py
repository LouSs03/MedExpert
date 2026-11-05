"""Consulta registrada y resultado mostrado a la persona usuaria."""

from dataclasses import dataclass
from uuid import UUID

from domain.mensajes_sistema import MensajeSistema
from domain.nivel import Nivel
from domain.regla import ReglaDisparada
from domain.vocabulario import HechosConsulta, Sintoma


@dataclass(frozen=True)
class Consulta:
    """Registro anónimo de una evaluación: hechos, nivel resuelto y reglas disparadas."""

    hechos: HechosConsulta
    nivel: Nivel
    sin_regla: bool
    reglas_disparadas: tuple[ReglaDisparada, ...]


@dataclass(frozen=True)
class ResultadoEvaluacion:
    """Lo que se muestra a la persona: nivel, reglas, mensajes del sistema y estado del registro."""

    nivel: Nivel
    sin_regla: bool
    reglas_disparadas: tuple[ReglaDisparada, ...]
    sintomas_no_cubiertos: tuple[Sintoma, ...]
    mensajes_sistema: tuple[MensajeSistema, ...]
    persistida: bool
    consulta_id: UUID | None

    @property
    def salvaguarda_activada(self) -> bool:
        """Indica si algún síntoma marcado quedó sin regla aplicable."""
        return bool(self.sintomas_no_cubiertos)
