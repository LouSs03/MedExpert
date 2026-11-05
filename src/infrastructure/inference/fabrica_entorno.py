"""Fábrica de entornos CLIPS limpios, uno por consulta (Principio V, patrón Factory)."""

from collections.abc import Mapping, Sequence
from types import MappingProxyType

import clips

from domain.regla import Regla
from infrastructure.inference.traductor_reglas import TraductorReglasClips


class FabricaEntornoClips:
    """Guarda los constructos de la base cargada y crea un entorno nuevo en cada llamada."""

    def __init__(
        self, reglas: Sequence[Regla], traductor: TraductorReglasClips | None = None
    ) -> None:
        traductor = traductor or TraductorReglasClips()
        self._constructos: tuple[str, ...] = (
            *traductor.plantillas(),
            *(traductor.traducir(r) for r in reglas),
        )
        self._reglas_por_id: Mapping[int, Regla] = MappingProxyType({r.id: r for r in reglas})

    @property
    def reglas_por_id(self) -> Mapping[int, Regla]:
        """Devuelve las reglas cargadas indexadas por su identificador (solo lectura)."""
        return self._reglas_por_id

    def crear(self) -> clips.Environment:
        """Devuelve un entorno CLIPS nuevo con las plantillas y todas las reglas construidas."""
        entorno = clips.Environment()
        for constructo in self._constructos:
            entorno.build(constructo)  # clipspy acepta un solo constructo por llamada
        return entorno
