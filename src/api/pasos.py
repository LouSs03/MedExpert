"""Presentación de la consulta en tres pasos (medicamento, síntomas, condiciones).

El estado entre pasos viaja en la URL (pasos 1 y 2, formularios GET) o en campos ocultos (paso 3,
POST /consulta): no hay sesión en el servidor y solo se registra la consulta al final. La validación
autoritativa sigue siendo la del dominio (Vocabulario.validar); aquí solo se decide qué pantalla
mostrar.
"""

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

from domain.vocabulario import Vocabulario

# Solo nombres de presentación: no están en el vocabulario, se muestran deshabilitados y nunca se
# envían. No hay reglas para ellos.
MEDICAMENTOS_PROXIMAMENTE = ("Naproxeno", "Diclofenaco", "Aspirina", "Azitromicina")
SINTOMAS_PROXIMAMENTE = ("Malestar general",)

ERROR_MEDICAMENTO = "Debe elegir exactamente un medicamento."
ERROR_SINTOMAS = "Debe marcar al menos un síntoma."
ERROR_CONDICIONES = "La consulta contiene condiciones no reconocidas."


@dataclass(frozen=True)
class Estado:
    """Lo elegido hasta ahora, tal como llega en la URL o en el formulario."""

    medicamento: str | None = None
    sintomas: tuple[str, ...] = ()
    condiciones: tuple[str, ...] = ()
    ninguna: bool = False

    @classmethod
    def desde(
        cls,
        medicamento: str | None,
        sintomas: list[str] | None,
        condiciones: list[str] | None,
        ninguna: bool = False,
    ) -> "Estado":
        """Normaliza la entrada: sin vacíos ni duplicados, en el orden recibido."""
        condiciones_limpias = tuple(dict.fromkeys(c for c in condiciones or [] if c))
        return cls(
            medicamento=medicamento or None,
            sintomas=tuple(dict.fromkeys(s for s in sintomas or [] if s)),
            condiciones=condiciones_limpias,
            ninguna=ninguna and not condiciones_limpias,
        )

    def campos(self, *excluir: str) -> list[tuple[str, str]]:
        """Pares (nombre, valor) del estado, sin los campos excluidos."""
        pares: list[tuple[str, str]] = []
        if self.medicamento and "medicamento" not in excluir:
            pares.append(("medicamento", self.medicamento))
        if "sintomas" not in excluir:
            pares += [("sintomas", s) for s in self.sintomas]
        if "condiciones" not in excluir:
            pares += [("condiciones", c) for c in self.condiciones]
        if self.ninguna and "ninguna" not in excluir:
            pares.append(("ninguna", "1"))
        return pares

    def url(self, paso: int) -> str:
        """URL del paso indicado con todo el estado en la consulta."""
        consulta = urlencode(self.campos())
        return f"/consulta/paso/{paso}" + (f"?{consulta}" if consulta else "")


def paso_con_error(vocabulario: Vocabulario, estado: Estado, hasta: int) -> int | None:
    """Primer paso (anterior a `hasta`) cuyos datos no son válidos, o None si todos lo son."""
    medicamentos = {m.codigo for m in vocabulario.medicamentos}
    sintomas = {s.codigo for s in vocabulario.sintomas}
    condiciones = {c.codigo for c in vocabulario.condiciones}
    if hasta > 1 and estado.medicamento not in medicamentos:
        return 1
    if hasta > 2 and (not estado.sintomas or not set(estado.sintomas) <= sintomas):
        return 2
    if hasta > 3 and not set(estado.condiciones) <= condiciones:
        return 3
    return None


ERRORES_POR_PASO = {1: ERROR_MEDICAMENTO, 2: ERROR_SINTOMAS, 3: ERROR_CONDICIONES}


def _chips(vocabulario: Vocabulario, estado: Estado, paso: int) -> list[str]:
    """Lo ya elegido en los otros pasos, con sus nombres visibles."""
    nombres = {
        **{m.codigo: m.nombre for m in vocabulario.medicamentos},
        **{s.codigo: s.nombre for s in vocabulario.sintomas},
        **{c.codigo: c.nombre for c in vocabulario.condiciones},
    }
    chips: list[str] = []
    if paso != 1 and estado.medicamento in nombres:
        chips.append(nombres[estado.medicamento])
    if paso != 2:
        chips += [nombres[s] for s in estado.sintomas if s in nombres]
    if paso != 3:
        chips += [nombres[c] for c in estado.condiciones if c in nombres]
        if estado.ninguna:
            chips.append("Sin condiciones")
    return chips


def contexto_paso(
    paso: int, vocabulario: Vocabulario, estado: Estado, errores: tuple[str, ...] = ()
) -> dict[str, Any]:
    """Contexto de la plantilla paso.html para el paso 1, 2 o 3."""
    if paso == 1:
        opciones = [
            {"valor": m.codigo, "nombre": m.nombre, "elegida": m.codigo == estado.medicamento}
            for m in vocabulario.medicamentos
        ] + [{"valor": None, "nombre": n, "bloqueada": True} for n in MEDICAMENTOS_PROXIMAMENTE]
        especifico: dict[str, Any] = {
            "titulo": "Seleccione el medicamento que desea tomar",
            "subtitulo": "Elija uno.",
            "imagen": "img/blister.jpg",
            "campo": "medicamento",
            "modo": "unica",
            "columnas": 2,
            "accion": "/consulta/paso/2",
            "metodo": "get",
            "ocultos": estado.campos("medicamento"),
            "url_volver": None,
            "aria_inactivo": "Elija un medicamento para continuar",
            "aria_activo": "Continuar al paso 2: síntomas",
            "nota": (
                "Por ahora solo hay reglas validadas por un médico para paracetamol e ibuprofeno. "
                "Los demás medicamentos aparecen como «Próximamente» porque aún no tienen reglas."
            ),
        }
    elif paso == 2:
        opciones = [
            {"valor": s.codigo, "nombre": s.nombre, "elegida": s.codigo in estado.sintomas}
            for s in vocabulario.sintomas
        ] + [{"valor": None, "nombre": n, "bloqueada": True} for n in SINTOMAS_PROXIMAMENTE]
        especifico = {
            "titulo": "Seleccione el síntoma a tratar",
            "subtitulo": (
                "Marca al menos uno. Puedes elegir varios y volver a tocar para quitarlos."
            ),
            "imagen": "img/cuidado.jpg",
            "campo": "sintomas",
            "modo": "multiple",
            "columnas": 3,
            "accion": "/consulta/paso/3",
            "metodo": "get",
            "ocultos": estado.campos("sintomas"),
            "url_volver": estado.url(1),
            "aria_inactivo": "Marque al menos un síntoma para continuar",
            "aria_activo": "Continuar al paso 3: condiciones",
        }
    else:
        opciones = [
            {"valor": c.codigo, "nombre": c.nombre, "elegida": c.codigo in estado.condiciones}
            for c in vocabulario.condiciones
        ]
        especifico = {
            "titulo": "Elija algunas condiciones, si las tiene",
            "subtitulo": "Marca todas las que te apliquen, o indica que no tienes ninguna.",
            "imagen": "img/ficha.jpg",
            "campo": "condiciones",
            "modo": "multiple",
            "columnas": 3,
            "accion": "/consulta",
            "metodo": "post",
            "ocultos": estado.campos("condiciones", "ninguna"),
            "url_volver": estado.url(2),
            "aria_inactivo": (
                "Marque al menos una condición o elija «No tengo ninguna de estas condiciones» "
                "para ver el resultado"
            ),
            "aria_activo": "Ver el resultado",
            "ninguna": estado.ninguna,
        }
    return {
        "paso": paso,
        "opciones": opciones,
        "chips": _chips(vocabulario, estado, paso),
        "errores": errores,
        **especifico,
    }
