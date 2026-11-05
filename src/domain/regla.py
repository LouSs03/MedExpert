"""Reglas validadas por el médico especialista."""

from dataclasses import dataclass

from domain.nivel import EstadoRegla, Nivel
from domain.vocabulario import validar_codigo


@dataclass(frozen=True)
class Regla:
    """Versión concreta de una regla de la base de conocimiento."""

    id: int
    codigo: str
    version: int
    medicamento: str
    sintomas: frozenset[str]
    condiciones: frozenset[str]
    sin_condiciones: bool
    especificidad: int
    nivel: Nivel
    estado: EstadoRegla
    mensajes: tuple[str, ...]

    def __post_init__(self) -> None:
        """Comprueba los invariantes de la regla y lanza ValueError si alguno falla."""
        for codigo in (self.codigo, self.medicamento, *self.sintomas, *self.condiciones):
            validar_codigo(codigo)
        if not self.sintomas:
            raise ValueError(f"La regla {self.codigo} no tiene síntomas.")
        if not self.mensajes:
            raise ValueError(f"La regla {self.codigo} no tiene mensajes.")
        if self.sin_condiciones and self.condiciones:
            raise ValueError(f"La regla {self.codigo} es 'sin condiciones' pero tiene condiciones.")


@dataclass(frozen=True)
class ReglaDisparada:
    """Regla que se disparó en una consulta, con su posición en el orden de presentación."""

    regla: Regla
    orden: int
