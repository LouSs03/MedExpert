"""Estrategia de resolución del nivel final, incluida la salvaguarda de cobertura (FR-020)."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from domain.nivel import Nivel
from domain.regla import Regla, ReglaDisparada
from domain.vocabulario import HechosConsulta, Sintoma


@dataclass(frozen=True)
class Resolucion:
    """Nivel final, reglas en orden de presentación y síntomas sin regla aplicable."""

    nivel: Nivel
    sin_regla: bool
    reglas_disparadas: tuple[ReglaDisparada, ...]
    sintomas_no_cubiertos: tuple[Sintoma, ...]


class EstrategiaResolucionNivel(Protocol):
    """Resuelve el nivel final de una consulta a partir de las reglas disparadas."""

    def resolver(self, hechos: HechosConsulta, disparadas: Sequence[Regla]) -> Resolucion:
        """Devuelve el nivel final, las reglas ordenadas y los síntomas no cubiertos."""
        ...


def _clave_orden(regla: Regla) -> tuple[int, int, str, int]:
    """Orden FR-009: nivel más severo, mayor especificidad, código ascendente."""
    return (-regla.nivel.severidad, -regla.especificidad, regla.codigo, regla.id)


class ResolucionPorSeveridad:
    """Aplica DERIVAR > ADVERTIR > ORIENTAR y la salvaguarda de cobertura, que no es opcional."""

    def resolver(self, hechos: HechosConsulta, disparadas: Sequence[Regla]) -> Resolucion:
        """Devuelve la resolución según la tabla de decisión del modelo de datos."""
        if not disparadas:
            return Resolucion(Nivel.DERIVAR, True, (), ())

        unicas = {regla.id: regla for regla in disparadas}.values()
        ordenadas = sorted(unicas, key=_clave_orden)
        nivel = max((r.nivel for r in ordenadas), key=lambda n: n.severidad)

        cubiertos = frozenset().union(*(r.sintomas for r in ordenadas))
        no_cubiertos = tuple(
            sorted((s for s in hechos.sintomas if s.codigo not in cubiertos), key=lambda s: s.id)
        )
        if no_cubiertos and nivel.severidad < Nivel.ADVERTIR.severidad:
            nivel = Nivel.ADVERTIR

        return Resolucion(
            nivel=nivel,
            sin_regla=False,
            reglas_disparadas=tuple(
                ReglaDisparada(regla=r, orden=i) for i, r in enumerate(ordenadas, 1)
            ),
            sintomas_no_cubiertos=no_cubiertos,
        )
