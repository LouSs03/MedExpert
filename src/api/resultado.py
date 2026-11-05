"""Presentación de la pantalla de resultado.

Todo lo que se muestra aquí se calcula a partir del resultado real de la consulta. Los textos de
las recomendaciones salen de regla_mensaje (vía el DTO); este módulo no escribe texto clínico: solo
etiquetas de interfaz que explican qué significa cada nivel.
"""

from typing import Any

from api.esquemas import ResultadoDTO
from domain.vocabulario import Vocabulario

SEVERIDAD = {"ORIENTAR": 1, "ADVERTIR": 2, "DERIVAR": 3}
ETIQUETA_NIVEL = {"ORIENTAR": "Orientar", "ADVERTIR": "Advertir", "DERIVAR": "Derivar al médico"}

# (complemento del título, párrafo breve). Explican el nivel; no son recomendaciones.
ENCABEZADOS = {
    "ORIENTAR": (
        "lee las recomendaciones",
        "Las reglas aplicadas permiten orientarte en este caso. Lee las recomendaciones antes de "
        "tomar el medicamento.",
    ),
    "ADVERTIR": (
        "consulta antes de usar",
        "Las reglas aplicadas piden precaución en este caso. Lee las recomendaciones y consulta a "
        "un médico o farmacéutico antes de usar el medicamento.",
    ),
    "DERIVAR": (
        "acude a un profesional",
        "Las reglas aplicadas indican que este caso debe evaluarlo un médico.",
    ),
}
ENCABEZADO_SIN_REGLA = (
    "caso no cubierto",
    "Ninguna regla validada cubre esta combinación, así que el sistema no da una orientación "
    "propia y te remite a un médico.",
)


def _chips_consulta(
    vocabulario: Vocabulario,
    medicamento: str | None,
    sintomas: list[str],
    condiciones: list[str],
    ninguna: bool,
) -> list[str]:
    """Nombres visibles de lo consultado, en el orden del vocabulario."""
    chips = [m.nombre for m in vocabulario.medicamentos if m.codigo == medicamento]
    chips += [s.nombre for s in vocabulario.sintomas if s.codigo in sintomas]
    chips += [c.nombre for c in vocabulario.condiciones if c.codigo in condiciones]
    if not condiciones and ninguna:
        chips.append("Sin condiciones")
    return chips


def contexto_resultado(
    dto: ResultadoDTO,
    vocabulario: Vocabulario,
    medicamento: str | None,
    sintomas: list[str],
    condiciones: list[str],
    ninguna: bool,
    reglas_en_base: int,
) -> dict[str, Any]:
    """Contexto de resultado.html con métricas reales y la explicación del nivel."""
    codigos = [r.codigo for r in dto.reglas_aplicadas]
    complemento, parrafo = ENCABEZADO_SIN_REGLA if dto.sin_regla else ENCABEZADOS[dto.nivel]

    nivel_reglas = (
        max((r.nivel for r in dto.reglas_aplicadas), key=SEVERIDAD.__getitem__)
        if dto.reglas_aplicadas
        else None
    )
    subio_por_salvaguarda = (
        dto.salvaguarda_activada
        and nivel_reglas is not None
        and SEVERIDAD[dto.nivel] > SEVERIDAD[nivel_reglas]
    )

    consultados = [s.codigo for s in vocabulario.sintomas if s.codigo in sintomas]
    # Sin ninguna regla, ningún síntoma marcado tiene orientación específica.
    sin_orientacion = len(consultados) if dto.sin_regla else len(dto.sintomas_no_cubiertos)

    if len(codigos) == 1:
        regla_valor, regla_etiqueta = codigos[0], "Regla aplicada"
    elif codigos:
        regla_valor, regla_etiqueta = str(len(codigos)), "Reglas aplicadas"
    else:
        regla_valor, regla_etiqueta = "0", "Reglas aplicadas"

    return {
        "resultado": dto,
        "titulo_complemento": complemento,
        "parrafo": parrafo,
        "consultado": _chips_consulta(vocabulario, medicamento, sintomas, condiciones, ninguna),
        "nivel_reglas": ETIQUETA_NIVEL[nivel_reglas] if nivel_reglas else None,
        "subio_por_salvaguarda": subio_por_salvaguarda,
        "pendiente": any(m.pendiente_aprobacion for m in dto.mensajes_sistema),
        "metricas": [
            {"valor": regla_valor, "etiqueta": regla_etiqueta},
            {"valor": str(sin_orientacion), "etiqueta": "Síntomas sin orientación específica"},
            {"valor": str(reglas_en_base), "etiqueta": "Reglas revisadas en la base"},
        ],
    }
