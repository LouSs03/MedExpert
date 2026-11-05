"""Adaptador de ConsultaRepository sobre PostgreSQL (vía SQLModel; independiente del proveedor)."""

from uuid import UUID

from sqlalchemy import insert
from sqlmodel import Session, col

from domain.consulta import Consulta
from infrastructure.db.modelos import (
    ConsultaCondicionTabla,
    ConsultaReglaDisparadaTabla,
    ConsultaSintomaTabla,
    ConsultaTabla,
)


class PostgresConsultaRepository:
    """Registra cada consulta (sin datos personales) en una sola transacción."""

    def __init__(self, sesion: Session) -> None:
        self._sesion = sesion

    def guardar(self, consulta: Consulta) -> UUID:
        """Inserta la consulta y sus hechos y reglas disparadas; devuelve el id generado."""
        try:
            consulta_id: UUID = self._sesion.execute(
                insert(ConsultaTabla)
                .values(
                    medicamento_id=consulta.hechos.medicamento.id,
                    nivel_resultado=consulta.nivel.value,
                    sin_regla=consulta.sin_regla,
                )
                .returning(col(ConsultaTabla.id))
            ).scalar_one()

            sintomas = [
                {"consulta_id": consulta_id, "sintoma_id": s.id} for s in consulta.hechos.sintomas
            ]
            condiciones = [
                {"consulta_id": consulta_id, "condicion_id": c.id}
                for c in consulta.hechos.condiciones
            ]
            disparadas = [
                {"consulta_id": consulta_id, "regla_id": d.regla.id, "orden": d.orden}
                for d in consulta.reglas_disparadas
            ]
            self._sesion.execute(insert(ConsultaSintomaTabla), sintomas)
            if condiciones:
                self._sesion.execute(insert(ConsultaCondicionTabla), condiciones)
            if disparadas:
                self._sesion.execute(insert(ConsultaReglaDisparadaTabla), disparadas)
            self._sesion.commit()
        except Exception:
            self._sesion.rollback()
            raise
        return consulta_id
