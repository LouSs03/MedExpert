"""PostgresReglaRepository contra la base de pruebas (Principio VIII, integración)."""

import pytest
from sqlalchemy import Engine, text
from sqlmodel import Session

from domain.nivel import EstadoRegla
from infrastructure.db.postgres_regla_repository import PostgresReglaRepository

pytestmark = pytest.mark.integration

MEDICAMENTOS = ["PARACETAMOL", "IBUPROFENO"]
SINTOMAS = [
    "DOLOR_CABEZA",
    "FIEBRE",
    "MOLESTIAS_RESPIRATORIAS",
    "DOLOR_MUSCULAR",
    "DOLOR_ABDOMINAL",
    "DOLOR_DENTAL",
]
CONDICIONES = [
    "EMBARAZO",
    "DIABETES",
    "HIPERTENSION",
    "ADULTO_MAYOR",
    "OTRO_TRATAMIENTO",
    "USO_ANTIGRIPAL",
    "USO_ASPIRINA",
]


def test_vocabulario_coincide_exactamente_con_fr001(engine_pruebas: Engine) -> None:
    vocabulario = PostgresReglaRepository(engine_pruebas).obtener_vocabulario()

    assert [m.codigo for m in vocabulario.medicamentos] == MEDICAMENTOS
    assert [s.codigo for s in vocabulario.sintomas] == SINTOMAS
    assert [c.codigo for c in vocabulario.condiciones] == CONDICIONES
    assert vocabulario.condiciones[3].nombre == "Adulto mayor (60 años o más)"


def test_30_reglas_aprobadas_en_su_version_mas_reciente(engine_pruebas: Engine) -> None:
    reglas = PostgresReglaRepository(engine_pruebas).listar_reglas_aprobadas_vigentes()

    assert sorted(r.codigo for r in reglas) == [f"R{n:02d}" for n in range(1, 31)]
    assert all(r.estado is EstadoRegla.APROBADA for r in reglas)
    with engine_pruebas.connect() as conexion:
        maximas = dict(
            conexion.execute(
                text(
                    "select codigo, max(version) from regla "
                    "where estado = 'aprobada' group by codigo"
                )
            ).all()
        )
    assert {r.codigo: r.version for r in reglas} == maximas


def test_mensajes_respetan_el_orden(engine_pruebas: Engine) -> None:
    reglas = PostgresReglaRepository(engine_pruebas).listar_reglas_aprobadas_vigentes()

    with engine_pruebas.connect() as conexion:
        for regla in reglas:
            esperados = (
                conexion.execute(
                    text("select texto from regla_mensaje where regla_id = :id order by orden"),
                    {"id": regla.id},
                )
                .scalars()
                .all()
            )
            assert list(regla.mensajes) == esperados, regla.codigo


def test_sintomas_condiciones_y_sin_condiciones(engine_pruebas: Engine) -> None:
    reglas = {
        r.codigo: r
        for r in PostgresReglaRepository(engine_pruebas).listar_reglas_aprobadas_vigentes()
    }

    assert reglas["R07"].sintomas == frozenset({"DOLOR_CABEZA", "FIEBRE"})
    assert reglas["R07"].sin_condiciones is True
    assert reglas["R28"].condiciones == frozenset({"HIPERTENSION", "ADULTO_MAYOR"})
    assert reglas["R28"].sin_condiciones is False


def _insertar_version_2_de_r01(sesion: Session, estado: str) -> int:
    """Inserta R01 v2 con el estado dado y devuelve el id que le asigna la base (identidad)."""
    nuevo_id: int = sesion.execute(
        text(
            "insert into regla (codigo, version, medicamento_id, nivel, sin_condiciones, "
            "especificidad, estado) values ('R01', 2, 1, 'ADVERTIR', true, 1, :estado) "
            "returning id"
        ),
        {"estado": estado},
    ).scalar_one()
    sesion.execute(
        text("insert into regla_sintoma (regla_id, sintoma_id) values (:id, 1)"), {"id": nuevo_id}
    )
    sesion.execute(
        text(
            "insert into regla_mensaje (regla_id, orden, texto) "
            "values (:id, 1, 'Versión 2 de prueba.')"
        ),
        {"id": nuevo_id},
    )
    return nuevo_id


def test_version_2_pendiente_no_reemplaza_a_la_aprobada(sesion_rollback: Session) -> None:
    _insertar_version_2_de_r01(sesion_rollback, "pendiente")

    reglas = PostgresReglaRepository(
        sesion_rollback.connection()
    ).listar_reglas_aprobadas_vigentes()

    r01 = next(r for r in reglas if r.codigo == "R01")
    assert r01.version == 1
    assert len(reglas) == 30


def test_version_2_aprobada_reemplaza_a_la_1(sesion_rollback: Session) -> None:
    nuevo_id = _insertar_version_2_de_r01(sesion_rollback, "aprobada")

    reglas = PostgresReglaRepository(
        sesion_rollback.connection()
    ).listar_reglas_aprobadas_vigentes()

    r01 = next(r for r in reglas if r.codigo == "R01")
    assert (r01.version, r01.id, r01.mensajes) == (2, nuevo_id, ("Versión 2 de prueba.",))
    assert len(reglas) == 30
