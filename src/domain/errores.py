"""Errores del dominio."""


class VocabularioInvalido(Exception):
    """La consulta contiene valores fuera de las listas cerradas o le faltan datos obligatorios."""

    def __init__(
        self, valores_rechazados: tuple[str, ...], problemas: tuple[str, ...] = ()
    ) -> None:
        self.valores_rechazados = valores_rechazados
        self.problemas = problemas
        super().__init__("; ".join(problemas) or "La consulta contiene valores no reconocidos.")


class BaseConocimientoNoDisponible(Exception):
    """La base de conocimiento no pudo cargarse o no contiene reglas aprobadas.

    El motivo describe la causa en términos del dominio y nunca incluye una cadena de conexión.
    """

    def __init__(self, motivo: str) -> None:
        self.motivo = motivo
        super().__init__(motivo)
