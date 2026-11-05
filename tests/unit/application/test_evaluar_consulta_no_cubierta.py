"""Respuesta segura cuando no se dispara ninguna regla (US2, FR-011, FR-012)."""

import pytest

from application.casos_uso.evaluar_consulta import EvaluarConsulta
from domain.mensajes_sistema import (
    TEXTO_COMBINACION_NO_CUBIERTA,
    ConfiguracionSalvaguarda,
    TipoMensajeSistema,
)
from domain.nivel import Nivel
from domain.resolucion_nivel import ResolucionPorSeveridad
from fakes.motor import FakeMotorInferencia
from fakes.reglas_ejemplo import VOCABULARIO
from fakes.repositorios import ConsultaRepositoryEnMemoria


def _evaluar(pendiente: bool = True) -> tuple[EvaluarConsulta, ConsultaRepositoryEnMemoria]:
    consultas = ConsultaRepositoryEnMemoria()
    caso = EvaluarConsulta(
        vocabulario=VOCABULARIO,
        motor=FakeMotorInferencia([]),
        estrategia=ResolucionPorSeveridad(),
        consultas=consultas,
        salvaguarda=ConfiguracionSalvaguarda(pendiente_aprobacion=pendiente),
    )
    return caso, consultas


@pytest.mark.parametrize("pendiente", [True, False])
@pytest.mark.parametrize(
    "medicamento, sintomas, condiciones",
    [
        ("IBUPROFENO", ["FIEBRE"], []),
        ("PARACETAMOL", ["DOLOR_CABEZA", "DOLOR_DENTAL"], ["USO_ASPIRINA"]),
    ],
)
def test_sin_regla_deriva_con_un_unico_mensaje_de_combinacion_no_cubierta(
    medicamento: str, sintomas: list[str], condiciones: list[str], pendiente: bool
) -> None:
    caso, _ = _evaluar(pendiente)

    resultado = caso.ejecutar(medicamento, sintomas, condiciones)

    assert resultado.nivel is Nivel.DERIVAR
    assert resultado.sin_regla is True
    assert resultado.reglas_disparadas == ()
    assert resultado.sintomas_no_cubiertos == ()
    assert resultado.salvaguarda_activada is False
    (mensaje,) = resultado.mensajes_sistema
    assert mensaje.tipo is TipoMensajeSistema.COMBINACION_NO_CUBIERTA
    assert mensaje.texto == TEXTO_COMBINACION_NO_CUBIERTA
    assert mensaje.pendiente_aprobacion is False
    assert mensaje.sintoma is None


def test_sin_regla_nunca_genera_mensajes_de_sintoma_no_cubierto() -> None:
    caso, _ = _evaluar()

    resultado = caso.ejecutar("IBUPROFENO", ["FIEBRE", "DOLOR_DENTAL", "DOLOR_ABDOMINAL"], [])

    assert [m.tipo for m in resultado.mensajes_sistema] == [
        TipoMensajeSistema.COMBINACION_NO_CUBIERTA
    ]


def test_sin_regla_tambien_se_registra() -> None:
    caso, consultas = _evaluar()

    resultado = caso.ejecutar("IBUPROFENO", ["FIEBRE"], [])

    ((identificador, consulta),) = consultas.guardadas
    assert resultado.consulta_id == identificador
    assert consulta.sin_regla is True
    assert consulta.nivel is Nivel.DERIVAR
    assert consulta.reglas_disparadas == ()
