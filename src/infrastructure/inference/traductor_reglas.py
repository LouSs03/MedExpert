"""Traducción de reglas del dominio a constructos CLIPS (contracts/traduccion-clips.md)."""

from domain.regla import Regla
from domain.vocabulario import PATRON_CODIGO

PLANTILLAS: tuple[str, ...] = (
    "(deftemplate medicamento (slot codigo))",
    "(deftemplate sintoma (slot codigo))",
    "(deftemplate condicion (slot codigo))",
    "(deftemplate disparo (slot regla-id))",
)


def _codigo_seguro(codigo: object) -> str:
    """Devuelve el código si es seguro interpolarlo en CLIPS; si no, lanza ValueError."""
    if not isinstance(codigo, str) or not PATRON_CODIGO.fullmatch(codigo):
        raise ValueError(f"Código no admitido en un constructo CLIPS: {codigo!r}")
    return codigo


class TraductorReglasClips:
    """Convierte cada Regla en un `defrule` que afirma un hecho `disparo` con su identificador."""

    def plantillas(self) -> tuple[str, ...]:
        """Devuelve los `deftemplate` de medicamento, síntoma, condición y disparo."""
        return PLANTILLAS

    def traducir(self, regla: Regla) -> str:
        """Devuelve el texto del `defrule` de la regla; lanza ValueError si no es seguro."""
        if not isinstance(regla.id, int) or isinstance(regla.id, bool):
            raise ValueError(f"El identificador de la regla debe ser un entero: {regla.id!r}")
        if not isinstance(regla.version, int) or isinstance(regla.version, bool):
            raise ValueError(f"La versión de la regla debe ser un entero: {regla.version!r}")
        nombre = f"{_codigo_seguro(regla.codigo)}-v{regla.version}"
        lineas = [
            f"(defrule {nombre}",
            f"  (medicamento (codigo {_codigo_seguro(regla.medicamento)}))",
        ]
        lineas += [f"  (sintoma (codigo {_codigo_seguro(s)}))" for s in sorted(regla.sintomas)]
        lineas += [f"  (condicion (codigo {_codigo_seguro(c)}))" for c in sorted(regla.condiciones)]
        if regla.sin_condiciones:
            lineas.append("  (not (condicion))")
        lineas += ["  =>", f"  (assert (disparo (regla-id {regla.id}))))"]
        return "\n".join(lineas)
