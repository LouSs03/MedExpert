import pytest

from application.casos_uso.evaluar_consulta import EvaluarConsulta
from domain.errores import VocabularioInvalido
from domain.mensajes_sistema import ConfiguracionSalvaguarda, TipoMensajeSistema
from domain.nivel import Nivel
from domain.regla import Regla
from domain.resolucion_nivel import ResolucionPorSeveridad
from fakes.motor import FakeMotorInferencia
from fakes.reglas_ejemplo import FIEBRE, R01, R02, R07, R10, R11, R18, VOCABULARIO
from fakes.repositorios import ConsultaRepositoryEnMemoria


def _caso(
    disparadas: list[Regla], pendiente: bool = True
) -> tuple[EvaluarConsulta, FakeMotorInferencia, ConsultaRepositoryEnMemoria]:
    motor = FakeMotorInferencia(disparadas)
    consultas = ConsultaRepositoryEnMemoria()
    caso = EvaluarConsulta(
        vocabulario=VOCABULARIO,
        motor=motor,
        estrategia=ResolucionPorSeveridad(),
        consultas=consultas,
        salvaguarda=ConfiguracionSalvaguarda(pendiente_aprobacion=pendiente),
    )
    return caso, motor, consultas


def test_combinacion_cubierta() -> None:
    caso, motor, consultas = _caso([R02, R01, R07])

    resultado = caso.ejecutar("PARACETAMOL", ["DOLOR_CABEZA", "FIEBRE"], [])

    assert resultado.nivel is Nivel.ORIENTAR
    assert resultado.sin_regla is False
    assert [d.regla.codigo for d in resultado.reglas_disparadas] == ["R07", "R01", "R02"]
    assert resultado.mensajes_sistema == ()
    assert resultado.salvaguarda_activada is False
    assert resultado.persistida is True
    assert resultado.consulta_id == consultas.guardadas[0][0]
    assert motor.llamadas[0].codigos_sintomas == {"DOLOR_CABEZA", "FIEBRE"}


def test_nivel_mas_severo_entre_varias_reglas() -> None:
    caso, _, _ = _caso([R10, R11])

    resultado = caso.ejecutar("PARACETAMOL", ["DOLOR_CABEZA", "FIEBRE"], ["EMBARAZO"])

    assert resultado.nivel is Nivel.DERIVAR
    assert [d.regla.codigo for d in resultado.reglas_disparadas] == ["R11", "R10"]


@pytest.mark.parametrize("pendiente", [True, False])
def test_salvaguarda_eleva_a_advertir_con_mensaje_por_sintoma(pendiente: bool) -> None:
    caso, _, _ = _caso([R18], pendiente=pendiente)

    resultado = caso.ejecutar("IBUPROFENO", ["DOLOR_CABEZA", "FIEBRE", "DOLOR_DENTAL"], [])

    assert resultado.nivel is Nivel.ADVERTIR
    assert resultado.salvaguarda_activada is True
    assert [s.codigo for s in resultado.sintomas_no_cubiertos] == ["FIEBRE", "DOLOR_DENTAL"]
    assert [m.tipo for m in resultado.mensajes_sistema] == [
        TipoMensajeSistema.SINTOMA_NO_CUBIERTO,
        TipoMensajeSistema.SINTOMA_NO_CUBIERTO,
    ]
    assert [m.sintoma for m in resultado.mensajes_sistema] == list(resultado.sintomas_no_cubiertos)
    assert all(m.pendiente_aprobacion is pendiente for m in resultado.mensajes_sistema)
    assert resultado.mensajes_sistema[0].texto.startswith(
        "«Fiebre» no tiene orientación específica con Ibuprofeno"
    )


def test_consulta_registrada_con_el_nivel_ya_elevado() -> None:
    caso, _, consultas = _caso([R18])

    caso.ejecutar("IBUPROFENO", ["DOLOR_CABEZA", "FIEBRE"], [])

    ((_, consulta),) = consultas.guardadas
    assert consulta.nivel is Nivel.ADVERTIR
    assert consulta.sin_regla is False
    assert consulta.hechos.sintomas == frozenset({VOCABULARIO.sintomas[0], FIEBRE})
    assert [(d.regla.codigo, d.orden) for d in consulta.reglas_disparadas] == [("R18", 1)]


def test_vocabulario_invalido_no_llama_al_motor_ni_al_repositorio() -> None:
    caso, motor, consultas = _caso([R01])

    with pytest.raises(VocabularioInvalido) as error:
        caso.ejecutar("PARACETAMOL", ["SINTOMA_X"], [])

    assert error.value.valores_rechazados == ("SINTOMA_X",)
    assert motor.llamadas == []
    assert consultas.guardadas == []
