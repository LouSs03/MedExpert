"""Repositorios en memoria que implementan ReglaRepository y ConsultaRepository."""

from collections.abc import Sequence
from uuid import UUID, uuid4

from domain.consulta import Consulta
from domain.regla import Regla
from domain.vocabulario import Vocabulario

MENSAJE_FALLO_SIMULADO = "fallo simulado postgresql://usuario:secreto@host/db"


class ReglaRepositoryEnMemoria:
    """Devuelve un vocabulario y unas reglas fijados al construirlo, o falla si se indica."""

    def __init__(
        self,
        vocabulario: Vocabulario,
        reglas: Sequence[Regla],
        error: Exception | None = None,
    ) -> None:
        self.vocabulario = vocabulario
        self.reglas = tuple(reglas)
        self.error = error

    def obtener_vocabulario(self) -> Vocabulario:
        if self.error is not None:
            raise self.error
        return self.vocabulario

    def listar_reglas_aprobadas_vigentes(self) -> Sequence[Regla]:
        if self.error is not None:
            raise self.error
        return self.reglas


class ConsultaRepositoryEnMemoria:
    """Guarda las consultas en una lista o, con `fallar=True`, simula un fallo técnico."""

    def __init__(self, fallar: bool = False) -> None:
        self.fallar = fallar
        self.guardadas: list[tuple[UUID, Consulta]] = []

    def guardar(self, consulta: Consulta) -> UUID:
        if self.fallar:
            raise RuntimeError(MENSAJE_FALLO_SIMULADO)
        identificador = uuid4()
        self.guardadas.append((identificador, consulta))
        return identificador
