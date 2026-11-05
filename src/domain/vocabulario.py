"""Vocabulario cerrado de medicamentos, síntomas y condiciones, y los hechos de una consulta."""

import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from domain.errores import VocabularioInvalido

PATRON_CODIGO = re.compile(r"^[A-Z][A-Z0-9_]*$")


def validar_codigo(codigo: str) -> None:
    """Lanza ValueError si el código no cumple el formato `^[A-Z][A-Z0-9_]*$`."""
    if not PATRON_CODIGO.fullmatch(codigo):
        raise ValueError(f"Código con formato inválido: {codigo!r}")


@dataclass(frozen=True)
class _Termino:
    """Término del vocabulario identificado por un código único y con un nombre visible."""

    id: int
    codigo: str
    nombre: str

    def __post_init__(self) -> None:
        """Comprueba el formato del código."""
        validar_codigo(self.codigo)


@dataclass(frozen=True)
class Medicamento(_Termino):
    """Fármaco que la persona piensa tomar."""


@dataclass(frozen=True)
class Sintoma(_Termino):
    """Malestar declarado por la persona."""


@dataclass(frozen=True)
class Condicion(_Termino):
    """Circunstancia de la persona que puede modificar la orientación."""


@dataclass(frozen=True)
class HechosConsulta:
    """Hechos de entrada de una consulta: un medicamento, al menos un síntoma y sus condiciones."""

    medicamento: Medicamento
    sintomas: frozenset[Sintoma]
    condiciones: frozenset[Condicion]

    def __post_init__(self) -> None:
        """Comprueba que haya al menos un síntoma."""
        if not self.sintomas:
            raise ValueError("Una consulta necesita al menos un síntoma.")

    @property
    def codigos_sintomas(self) -> frozenset[str]:
        """Devuelve los códigos de los síntomas marcados."""
        return frozenset(s.codigo for s in self.sintomas)

    @property
    def codigos_condiciones(self) -> frozenset[str]:
        """Devuelve los códigos de las condiciones marcadas."""
        return frozenset(c.codigo for c in self.condiciones)


def _ordenar_unicos[T: _Termino](terminos: Sequence[T], catalogo: str) -> tuple[T, ...]:
    codigos = [t.codigo for t in terminos]
    if len(set(codigos)) != len(codigos):
        raise ValueError(f"Códigos duplicados en el catálogo de {catalogo}.")
    return tuple(sorted(terminos, key=lambda t: t.id))


@dataclass(frozen=True)
class Vocabulario:
    """Listas cerradas de medicamentos, síntomas y condiciones, ordenadas por identificador."""

    medicamentos: tuple[Medicamento, ...]
    sintomas: tuple[Sintoma, ...]
    condiciones: tuple[Condicion, ...]

    def __post_init__(self) -> None:
        """Ordena cada catálogo por identificador y rechaza códigos duplicados."""
        object.__setattr__(self, "medicamentos", _ordenar_unicos(self.medicamentos, "medicamentos"))
        object.__setattr__(self, "sintomas", _ordenar_unicos(self.sintomas, "síntomas"))
        object.__setattr__(self, "condiciones", _ordenar_unicos(self.condiciones, "condiciones"))

    def validar(
        self,
        medicamento: str | None,
        sintomas: Iterable[str],
        condiciones: Iterable[str],
    ) -> HechosConsulta:
        """Convierte los códigos recibidos en hechos válidos o lanza VocabularioInvalido."""
        por_codigo_med = {m.codigo: m for m in self.medicamentos}
        por_codigo_sin = {s.codigo: s for s in self.sintomas}
        por_codigo_con = {c.codigo: c for c in self.condiciones}
        rechazados: list[str] = []
        problemas: list[str] = []

        elegido: Medicamento | None = None
        if not medicamento:
            problemas.append("Debe elegir exactamente un medicamento.")
        elif medicamento in por_codigo_med:
            elegido = por_codigo_med[medicamento]
        else:
            rechazados.append(medicamento)

        sintomas_validos: set[Sintoma] = set()
        codigos_sintomas = list(dict.fromkeys(sintomas))
        for codigo in codigos_sintomas:
            if codigo in por_codigo_sin:
                sintomas_validos.add(por_codigo_sin[codigo])
            else:
                rechazados.append(codigo)
        if not codigos_sintomas:
            problemas.append("Debe marcar al menos un síntoma.")

        condiciones_validas: set[Condicion] = set()
        for codigo in dict.fromkeys(condiciones):
            if codigo in por_codigo_con:
                condiciones_validas.add(por_codigo_con[codigo])
            else:
                rechazados.append(codigo)

        if rechazados:
            problemas.append("La consulta contiene valores no reconocidos.")
        if problemas or elegido is None:
            raise VocabularioInvalido(tuple(rechazados), tuple(problemas))
        return HechosConsulta(elegido, frozenset(sintomas_validos), frozenset(condiciones_validas))
