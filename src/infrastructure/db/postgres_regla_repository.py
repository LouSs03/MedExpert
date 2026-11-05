"""Adaptador de ReglaRepository sobre PostgreSQL (vía SQLModel; independiente del proveedor)."""

from collections import defaultdict
from collections.abc import Sequence

from sqlalchemy import Connection, Engine, text
from sqlmodel import Session, col, select

from domain.nivel import EstadoRegla, Nivel
from domain.regla import Regla
from domain.vocabulario import Condicion, Medicamento, Sintoma, Vocabulario
from infrastructure.db.modelos import (
    CondicionTabla,
    MedicamentoTabla,
    ReglaCondicionTabla,
    ReglaMensajeTabla,
    ReglaSintomaTabla,
    SintomaTabla,
)

SQL_REGLAS_VIGENTES = text(
    """
    select distinct on (r.codigo)
           r.id, r.codigo, r.version, m.codigo as medicamento, r.nivel,
           r.sin_condiciones, r.especificidad, r.estado
    from regla r
    join medicamento m on m.id = r.medicamento_id
    where r.estado = 'aprobada'
    order by r.codigo, r.version desc
    """
)


class PostgresReglaRepository:
    """Lee el vocabulario y las reglas aprobadas vigentes; nunca escribe (FR-017).

    Acepta un Engine o una Connection: con una Connection, las lecturas ocurren dentro de su
    transacción (lo usan las pruebas que insertan datos y luego los deshacen).
    """

    def __init__(self, origen: Engine | Connection) -> None:
        self._origen = origen

    def obtener_vocabulario(self) -> Vocabulario:
        """Devuelve los catálogos de medicamentos, síntomas y condiciones ordenados por id."""
        with Session(self._origen) as sesion:
            medicamentos = sesion.exec(select(MedicamentoTabla).order_by(col(MedicamentoTabla.id)))
            sintomas = sesion.exec(select(SintomaTabla).order_by(col(SintomaTabla.id)))
            condiciones = sesion.exec(select(CondicionTabla).order_by(col(CondicionTabla.id)))
            return Vocabulario(
                medicamentos=tuple(Medicamento(m.id, m.codigo, m.nombre) for m in medicamentos),
                sintomas=tuple(Sintoma(s.id, s.codigo, s.nombre) for s in sintomas),
                condiciones=tuple(Condicion(c.id, c.codigo, c.nombre) for c in condiciones),
            )

    def listar_reglas_aprobadas_vigentes(self) -> Sequence[Regla]:
        """Devuelve la versión aprobada más reciente de cada regla, con sus hechos y mensajes."""
        with Session(self._origen) as sesion:
            filas = sesion.execute(SQL_REGLAS_VIGENTES).mappings().all()
            ids = [f["id"] for f in filas]
            if not ids:
                return []

            sintomas: dict[int, set[str]] = defaultdict(set)
            for regla_id, codigo in sesion.exec(
                select(ReglaSintomaTabla.regla_id, SintomaTabla.codigo)
                .join(SintomaTabla, col(SintomaTabla.id) == col(ReglaSintomaTabla.sintoma_id))
                .where(col(ReglaSintomaTabla.regla_id).in_(ids))
            ):
                sintomas[regla_id].add(codigo)

            condiciones: dict[int, set[str]] = defaultdict(set)
            for regla_id, codigo in sesion.exec(
                select(ReglaCondicionTabla.regla_id, CondicionTabla.codigo)
                .join(
                    CondicionTabla, col(CondicionTabla.id) == col(ReglaCondicionTabla.condicion_id)
                )
                .where(col(ReglaCondicionTabla.regla_id).in_(ids))
            ):
                condiciones[regla_id].add(codigo)

            mensajes: dict[int, list[str]] = defaultdict(list)
            for regla_id, texto in sesion.exec(
                select(ReglaMensajeTabla.regla_id, ReglaMensajeTabla.texto)
                .where(col(ReglaMensajeTabla.regla_id).in_(ids))
                .order_by(col(ReglaMensajeTabla.regla_id), col(ReglaMensajeTabla.orden))
            ):
                mensajes[regla_id].append(texto)

        return [
            Regla(
                id=f["id"],
                codigo=f["codigo"],
                version=f["version"],
                medicamento=f["medicamento"],
                sintomas=frozenset(sintomas[f["id"]]),
                condiciones=frozenset(condiciones[f["id"]]),
                sin_condiciones=f["sin_condiciones"],
                especificidad=f["especificidad"],
                nivel=Nivel(f["nivel"]),
                estado=EstadoRegla(f["estado"]),
                mensajes=tuple(mensajes[f["id"]]),
            )
            for f in filas
        ]
