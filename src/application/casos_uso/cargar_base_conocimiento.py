"""Caso de uso: cargar y validar la base de conocimiento al arrancar (Principio II, FR-018)."""

import logging

from application.ports.regla_repository import ReglaRepository
from domain.base_conocimiento import BaseConocimiento
from domain.errores import BaseConocimientoNoDisponible
from domain.nivel import EstadoRegla
from domain.regla import Regla
from domain.vocabulario import Vocabulario

logger = logging.getLogger(__name__)


class CargarBaseConocimiento:
    """Obtiene el vocabulario y las reglas aprobadas vigentes y comprueba su coherencia."""

    def __init__(self, repositorio: ReglaRepository) -> None:
        self._repositorio = repositorio

    def ejecutar(self) -> BaseConocimiento:
        """Devuelve la base de conocimiento o lanza BaseConocimientoNoDisponible."""
        try:
            vocabulario = self._repositorio.obtener_vocabulario()
            reglas = tuple(self._repositorio.listar_reglas_aprobadas_vigentes())
        except BaseConocimientoNoDisponible:
            raise
        except Exception as error:
            # `from None`: el error original puede contener la cadena de conexión.
            raise BaseConocimientoNoDisponible(
                f"No se pudo leer la base de conocimiento ({type(error).__name__})."
            ) from None

        if not reglas:
            raise BaseConocimientoNoDisponible(
                "No hay reglas aprobadas en la base de conocimiento."
            )
        _verificar_coherencia(vocabulario, reglas)
        return BaseConocimiento(vocabulario=vocabulario, reglas=reglas)


def _verificar_coherencia(vocabulario: Vocabulario, reglas: tuple[Regla, ...]) -> None:
    medicamentos = {m.codigo for m in vocabulario.medicamentos}
    sintomas = {s.codigo for s in vocabulario.sintomas}
    condiciones = {c.codigo for c in vocabulario.condiciones}
    vistos: set[str] = set()
    for regla in reglas:
        if regla.codigo in vistos:
            raise BaseConocimientoNoDisponible(f"La regla {regla.codigo} aparece más de una vez.")
        vistos.add(regla.codigo)
        if regla.estado is not EstadoRegla.APROBADA:
            raise BaseConocimientoNoDisponible(f"La regla {regla.codigo} no está aprobada.")
        desconocidos = (
            ({regla.medicamento} - medicamentos)
            | (regla.sintomas - sintomas)
            | (regla.condiciones - condiciones)
        )
        if desconocidos:
            raise BaseConocimientoNoDisponible(
                f"La regla {regla.codigo} usa códigos fuera del vocabulario: "
                f"{', '.join(sorted(desconocidos))}."
            )
        if regla.especificidad != len(regla.sintomas) + len(regla.condiciones):
            logger.warning(
                "La especificidad de %s (%d) no coincide con su número de síntomas y condiciones.",
                regla.codigo,
                regla.especificidad,
            )
