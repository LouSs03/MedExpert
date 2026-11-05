"""PostgresConsultaRepository contra la base de pruebas, dentro de una transacción deshecha."""

import dataclasses
from typing import Any

import pytest
from sqlalchemy import text
from sqlmodel import Session

from application.casos_uso.cargar_base_conocimiento import CargarBaseConocimiento
from application.casos_uso.evaluar_consulta import EvaluarConsulta
from domain.base_conocimiento import BaseConocimiento
from domain.consulta import Consulta
from domain.mensajes_sistema import ConfiguracionSalvaguarda
from domain.regla import ReglaDisparada
from domain.resolucion_nivel import ResolucionPorSeveridad
from fakes.repositorios import ConsultaRepositoryEnMemoria
from infrastructure.db.postgres_consulta_repository import PostgresConsultaRepository
from infrastructure.db.postgres_regla_repository import PostgresReglaRepository
from infrastructure.inference.clips_motor_inferencia import ClipsMotorInferencia
from infrastructure.inference.fabrica_entorno import FabricaEntornoClips

pytestmark = pytest.mark.integration


def _base(sesion: Session) -> BaseConocimiento:
    return CargarBaseConocimiento(PostgresReglaRepository(sesion.connection())).ejecutar()


def _evaluar(sesion: Session, base: BaseConocimiento, consultas: Any) -> EvaluarConsulta:
    return EvaluarConsulta(
        vocabulario=base.vocabulario,
        motor=ClipsMotorInferencia(FabricaEntornoClips(base.reglas)),
        estrategia=ResolucionPorSeveridad(),
        consultas=consultas,
        salvaguarda=ConfiguracionSalvaguarda(),
    )


def _filas(sesion: Session, sql: str, consulta_id: object) -> list[tuple[Any, ...]]:
    return [tuple(f) for f in sesion.execute(text(sql), {"id": consulta_id}).all()]


@pytest.mark.parametrize(
    "medicamento, sintomas, condiciones",
    [
        ("IBUPROFENO", ["DOLOR_CABEZA", "FIEBRE"], []),
        ("PARACETAMOL", ["DOLOR_CABEZA", "FIEBRE"], ["EMBARAZO", "HIPERTENSION"]),
        ("IBUPROFENO", ["FIEBRE"], []),
    ],
    ids=["escenario-6-salvaguarda", "varias-reglas", "sin-regla"],
)
def test_guarda_la_consulta_completa(
    sesion_rollback: Session, medicamento: str, sintomas: list[str], condiciones: list[str]
) -> None:
    base = _base(sesion_rollback)
    resultado = _evaluar(
        sesion_rollback, base, PostgresConsultaRepository(sesion_rollback)
    ).ejecutar(medicamento, sintomas, condiciones)

    assert resultado.persistida is True
    consulta_id = resultado.consulta_id
    vocabulario = base.vocabulario

    (cabecera,) = _filas(
        sesion_rollback,
        "select medicamento_id, nivel_resultado, sin_regla, creado_en is not null "
        "from consulta where id = :id",
        consulta_id,
    )
    medicamento_id = next(m.id for m in vocabulario.medicamentos if m.codigo == medicamento)
    assert cabecera == (medicamento_id, resultado.nivel.value, resultado.sin_regla, True)

    sintomas_guardados = _filas(
        sesion_rollback,
        "select sintoma_id from consulta_sintoma where consulta_id = :id order by 1",
        consulta_id,
    )
    assert [f[0] for f in sintomas_guardados] == sorted(
        s.id for s in vocabulario.sintomas if s.codigo in sintomas
    )
    condiciones_guardadas = _filas(
        sesion_rollback,
        "select condicion_id from consulta_condicion where consulta_id = :id order by 1",
        consulta_id,
    )
    assert [f[0] for f in condiciones_guardadas] == sorted(
        c.id for c in vocabulario.condiciones if c.codigo in condiciones
    )
    disparadas = _filas(
        sesion_rollback,
        "select regla_id, orden from consulta_regla_disparada where consulta_id = :id "
        "order by orden",
        consulta_id,
    )
    assert disparadas == [(d.regla.id, d.orden) for d in resultado.reglas_disparadas]


def test_escenario_6_guarda_el_nivel_ya_elevado(sesion_rollback: Session) -> None:
    base = _base(sesion_rollback)
    resultado = _evaluar(
        sesion_rollback, base, PostgresConsultaRepository(sesion_rollback)
    ).ejecutar("IBUPROFENO", ["DOLOR_CABEZA", "FIEBRE"], [])

    (fila,) = _filas(
        sesion_rollback,
        "select nivel_resultado, sin_regla from consulta where id = :id",
        resultado.consulta_id,
    )
    assert fila == ("ADVERTIR", False)


def test_guardado_atomico_si_falla_una_tabla_hija(sesion_rollback: Session) -> None:
    base = _base(sesion_rollback)
    memoria = ConsultaRepositoryEnMemoria()
    _evaluar(sesion_rollback, base, memoria).ejecutar("PARACETAMOL", ["DOLOR_CABEZA"], [])
    ((_, consulta),) = memoria.guardadas
    regla_inexistente = dataclasses.replace(consulta.reglas_disparadas[0].regla, id=2_000_000_000)
    rota = Consulta(
        hechos=consulta.hechos,
        nivel=consulta.nivel,
        sin_regla=consulta.sin_regla,
        reglas_disparadas=(ReglaDisparada(regla=regla_inexistente, orden=1),),
    )
    antes = sesion_rollback.execute(text("select count(*) from consulta")).scalar_one()

    with pytest.raises(Exception) as error:
        PostgresConsultaRepository(sesion_rollback).guardar(rota)

    assert "IntegrityError" in type(error.value).__name__
    despues = sesion_rollback.execute(text("select count(*) from consulta")).scalar_one()
    assert despues == antes
