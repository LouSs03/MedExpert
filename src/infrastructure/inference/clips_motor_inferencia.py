"""Motor de inferencia con CLIPS (encadenamiento hacia adelante; adaptador de MotorInferencia)."""

from collections.abc import Sequence

from domain.regla import Regla
from domain.vocabulario import HechosConsulta
from infrastructure.inference.fabrica_entorno import FabricaEntornoClips

LIMITE_DISPAROS = 1000


class ClipsMotorInferencia:
    """Evalúa cada consulta en un entorno CLIPS propio que se descarta al terminar (FR-016)."""

    def __init__(self, fabrica: FabricaEntornoClips) -> None:
        self._fabrica = fabrica

    def evaluar(self, hechos: HechosConsulta) -> Sequence[Regla]:
        """Devuelve las reglas cargadas cuyas condiciones satisfacen los hechos."""
        entorno = self._fabrica.crear()
        entorno.assert_string(f"(medicamento (codigo {hechos.medicamento.codigo}))")
        for sintoma in sorted(hechos.codigos_sintomas):
            entorno.assert_string(f"(sintoma (codigo {sintoma}))")
        for condicion in sorted(hechos.codigos_condiciones):
            entorno.assert_string(f"(condicion (codigo {condicion}))")
        entorno.run(LIMITE_DISPAROS)

        reglas = self._fabrica.reglas_por_id
        return [
            reglas[int(hecho["regla-id"])]
            for hecho in entorno.facts()
            if hecho.template.name == "disparo"
        ]
