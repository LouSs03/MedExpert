"""Puerto de registro de consultas."""

from typing import Protocol
from uuid import UUID

from domain.consulta import Consulta


class ConsultaRepository(Protocol):
    """Destino del registro anónimo de cada consulta respondida."""

    def guardar(self, consulta: Consulta) -> UUID:
        """Persiste la consulta completa de forma atómica y devuelve su identificador."""
        ...
