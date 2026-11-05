"""Niveles de orientación y estados de una regla."""

from enum import Enum


class Nivel(Enum):
    """Grado de orientación de un resultado, de menor a mayor severidad."""

    ORIENTAR = "ORIENTAR"
    ADVERTIR = "ADVERTIR"
    DERIVAR = "DERIVAR"

    @property
    def severidad(self) -> int:
        """Devuelve la posición del nivel en el orden DERIVAR > ADVERTIR > ORIENTAR."""
        return _SEVERIDAD[self]

    @property
    def etiqueta(self) -> str:
        """Devuelve el nombre del nivel tal como se muestra a la persona usuaria."""
        return _ETIQUETA[self]


_SEVERIDAD = {Nivel.ORIENTAR: 1, Nivel.ADVERTIR: 2, Nivel.DERIVAR: 3}
_ETIQUETA = {
    Nivel.ORIENTAR: "Orientar",
    Nivel.ADVERTIR: "Advertir",
    Nivel.DERIVAR: "Derivar al médico",
}


class EstadoRegla(Enum):
    """Estado de validación de una versión de regla por el médico especialista."""

    PENDIENTE = "pendiente"
    APROBADA = "aprobada"
    RECHAZADA = "rechazada"
