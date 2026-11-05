"""Puerto del motor de inferencia."""

from collections.abc import Sequence
from typing import Protocol

from domain.regla import Regla
from domain.vocabulario import HechosConsulta


class MotorInferencia(Protocol):
    """Evalúa los hechos de una consulta contra la base de conocimiento cargada."""

    def evaluar(self, hechos: HechosConsulta) -> Sequence[Regla]:
        """Devuelve las reglas de la base cargada cuyas condiciones satisfacen los hechos."""
        ...
