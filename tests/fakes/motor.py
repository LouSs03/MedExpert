"""FakeMotorInferencia: motor de inferencia de prueba sin CLIPS (Principio V)."""

from collections.abc import Sequence

from domain.regla import Regla
from domain.vocabulario import HechosConsulta


class FakeMotorInferencia:
    """Devuelve siempre las reglas preconfiguradas y recuerda los hechos que recibió."""

    def __init__(self, disparadas: Sequence[Regla] = ()) -> None:
        self.disparadas = tuple(disparadas)
        self.llamadas: list[HechosConsulta] = []

    def evaluar(self, hechos: HechosConsulta) -> Sequence[Regla]:
        self.llamadas.append(hechos)
        return self.disparadas
