"""Consultas simultáneas (SC-008) y orden estable (SC-010): motor real y base de pruebas."""

from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import Engine

from api.esquemas import ResultadoDTO, a_resultado_dto
from application.casos_uso.cargar_base_conocimiento import CargarBaseConocimiento
from application.casos_uso.evaluar_consulta import EvaluarConsulta
from domain.base_conocimiento import BaseConocimiento
from domain.mensajes_sistema import ConfiguracionSalvaguarda
from domain.resolucion_nivel import ResolucionPorSeveridad
from fakes.repositorios import ConsultaRepositoryEnMemoria
from infrastructure.db.postgres_regla_repository import PostgresReglaRepository
from infrastructure.inference.clips_motor_inferencia import ClipsMotorInferencia
from infrastructure.inference.fabrica_entorno import FabricaEntornoClips

pytestmark = [pytest.mark.integration, pytest.mark.lento]

DatosConsulta = tuple[str, list[str], list[str]]

CONSULTAS: list[DatosConsulta] = [
    ("PARACETAMOL", ["DOLOR_CABEZA"], []),
    ("PARACETAMOL", ["DOLOR_CABEZA"], ["EMBARAZO"]),
    ("PARACETAMOL", ["FIEBRE"], ["EMBARAZO"]),
    ("PARACETAMOL", ["FIEBRE", "DOLOR_ABDOMINAL"], []),
    ("PARACETAMOL", ["DOLOR_CABEZA", "FIEBRE"], []),
    ("IBUPROFENO", ["DOLOR_CABEZA", "FIEBRE"], []),
    ("PARACETAMOL", ["FIEBRE", "DOLOR_DENTAL"], ["EMBARAZO"]),
    ("IBUPROFENO", ["FIEBRE"], []),
    ("PARACETAMOL", ["DOLOR_CABEZA"], ["USO_ASPIRINA"]),
    ("IBUPROFENO", ["DOLOR_MUSCULAR"], ["HIPERTENSION", "ADULTO_MAYOR"]),
    ("IBUPROFENO", ["DOLOR_MUSCULAR"], ["DIABETES", "HIPERTENSION"]),
    ("IBUPROFENO", ["DOLOR_DENTAL"], ["ADULTO_MAYOR", "OTRO_TRATAMIENTO"]),
    ("PARACETAMOL", ["DOLOR_MUSCULAR"], ["ADULTO_MAYOR", "USO_ASPIRINA"]),
    ("PARACETAMOL", ["FIEBRE", "MOLESTIAS_RESPIRATORIAS"], ["USO_ANTIGRIPAL"]),
    ("IBUPROFENO", ["FIEBRE", "MOLESTIAS_RESPIRATORIAS"], ["USO_ASPIRINA"]),
    ("IBUPROFENO", ["DOLOR_ABDOMINAL"], []),
    ("IBUPROFENO", ["DOLOR_DENTAL"], ["DIABETES"]),
    ("PARACETAMOL", ["DOLOR_CABEZA"], ["HIPERTENSION"]),
    ("IBUPROFENO", ["FIEBRE", "DOLOR_MUSCULAR"], []),
    ("PARACETAMOL", ["DOLOR_MUSCULAR", "DOLOR_DENTAL", "FIEBRE"], []),
]


@pytest.fixture(scope="module")
def base(engine_pruebas: Engine) -> BaseConocimiento:
    return CargarBaseConocimiento(PostgresReglaRepository(engine_pruebas)).ejecutar()


@pytest.fixture(scope="module")
def motor(base: BaseConocimiento) -> ClipsMotorInferencia:
    return ClipsMotorInferencia(FabricaEntornoClips(base.reglas))


def _evaluar(
    base: BaseConocimiento, motor: ClipsMotorInferencia, consulta: DatosConsulta
) -> ResultadoDTO:
    caso = EvaluarConsulta(
        vocabulario=base.vocabulario,
        motor=motor,
        estrategia=ResolucionPorSeveridad(),
        consultas=ConsultaRepositoryEnMemoria(),
        salvaguarda=ConfiguracionSalvaguarda(),
    )
    return a_resultado_dto(caso.ejecutar(*consulta))


def test_veinte_consultas_simultaneas_igual_que_en_secuencia(
    base: BaseConocimiento, motor: ClipsMotorInferencia
) -> None:
    assert len(CONSULTAS) == 20
    secuencial = [_evaluar(base, motor, c) for c in CONSULTAS]

    with ThreadPoolExecutor(max_workers=20) as grupo:
        concurrente = list(grupo.map(lambda c: _evaluar(base, motor, c), CONSULTAS))

    assert concurrente == secuencial


@pytest.mark.parametrize("consulta", CONSULTAS[:6], ids=lambda c: f"{c[0]}-{'+'.join(c[1])}")
def test_diez_repeticiones_dan_el_mismo_orden(
    base: BaseConocimiento,
    motor: ClipsMotorInferencia,
    consulta: DatosConsulta,
) -> None:
    resultados = [_evaluar(base, motor, consulta) for _ in range(10)]

    assert all(r == resultados[0] for r in resultados)
