"""Puerto de acceso de solo lectura a la base de conocimiento."""

from collections.abc import Sequence
from typing import Protocol

from domain.regla import Regla
from domain.vocabulario import Vocabulario


class ReglaRepository(Protocol):
    """Fuente del vocabulario y de las reglas aprobadas vigentes."""

    def obtener_vocabulario(self) -> Vocabulario:
        """Devuelve los catálogos de medicamentos, síntomas y condiciones."""
        ...

    def listar_reglas_aprobadas_vigentes(self) -> Sequence[Regla]:
        """Devuelve la versión más reciente en estado aprobada de cada regla."""
        ...
