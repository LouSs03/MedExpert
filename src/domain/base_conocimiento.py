"""Base de conocimiento cargada al arrancar."""

from dataclasses import dataclass

from domain.regla import Regla
from domain.vocabulario import Vocabulario


@dataclass(frozen=True)
class BaseConocimiento:
    """Vocabulario y reglas aprobadas vigentes; inmutable durante toda la vida del proceso."""

    vocabulario: Vocabulario
    reglas: tuple[Regla, ...]

    def __post_init__(self) -> None:
        """Comprueba que la base tenga al menos una regla."""
        if not self.reglas:
            raise ValueError("La base de conocimiento necesita al menos una regla.")
