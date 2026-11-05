"""Redacción de secretos en los logs (Principio X de la constitución)."""

import logging
import re
from collections.abc import Iterable

from infrastructure.config import Configuracion

REDACTADO = "<redacted>"
PATRON_URL_POSTGRES = re.compile(r"postgres(?:ql)?(?:\+\w+)*://\S+", re.IGNORECASE)
LOGGERS_EXTRA = ("uvicorn", "uvicorn.error", "uvicorn.access")


class FiltroSecretos(logging.Filter):
    """Reemplaza URLs de PostgreSQL y secretos configurados por `<redacted>` en cada registro."""

    def __init__(self, secretos: Iterable[str] = ()) -> None:
        super().__init__()
        self._secretos = tuple(sorted({s for s in secretos if s}, key=len, reverse=True))

    def redactar(self, texto: str) -> str:
        """Devuelve el texto sin secretos configurados ni URLs de PostgreSQL."""
        for secreto in self._secretos:
            texto = texto.replace(secreto, REDACTADO)
        return PATRON_URL_POSTGRES.sub(REDACTADO, texto)

    def filter(self, record: logging.LogRecord) -> bool:
        """Sanea mensaje, argumentos, traza de la excepción y pila; nunca descarta el registro."""
        record.msg = self.redactar(record.getMessage())
        record.args = None
        if record.exc_info:
            if not record.exc_text:
                record.exc_text = logging.Formatter().formatException(record.exc_info)
            record.exc_text = self.redactar(record.exc_text)
        if record.stack_info:
            record.stack_info = self.redactar(record.stack_info)
        return True


def configurar_logging(config: Configuracion, nivel: int = logging.INFO) -> FiltroSecretos:
    """Instala el filtro de secretos en los manejadores del logger raíz y de uvicorn."""
    raiz = logging.getLogger()
    if not raiz.handlers:
        logging.basicConfig(level=nivel)
    filtro = FiltroSecretos(config.secretos)
    loggers = [raiz, *(logging.getLogger(nombre) for nombre in LOGGERS_EXTRA)]
    for logger in loggers:
        for manejador in logger.handlers:
            if not any(isinstance(f, FiltroSecretos) for f in manejador.filters):
                manejador.addFilter(filtro)
    return filtro
