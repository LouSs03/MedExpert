"""Modelos SQLModel que reflejan el esquema existente de la base de datos.

El esquema lo administra la base (no la aplicación): aquí nunca se llama a `create_all` ni a
migraciones. Los nombres llevan el sufijo `Tabla` para no confundirlos con las entidades del
dominio.

Las columnas con valor por defecto en el servidor (`consulta.id`, `creado_en`) deben omitirse al
insertar, para que las genere la base.
"""

import uuid
from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    SmallInteger,
    Text,
    UniqueConstraint,
    Uuid,
    text,
)
from sqlmodel import Field, SQLModel


class MedicamentoTabla(SQLModel, table=True):
    """Tabla `medicamento`."""

    __tablename__ = "medicamento"

    id: int = Field(
        primary_key=True, sa_type=SmallInteger, sa_column_kwargs={"autoincrement": False}
    )
    codigo: str = Field(sa_type=Text, unique=True)
    nombre: str = Field(sa_type=Text)


class SintomaTabla(SQLModel, table=True):
    """Tabla `sintoma`."""

    __tablename__ = "sintoma"

    id: int = Field(
        primary_key=True, sa_type=SmallInteger, sa_column_kwargs={"autoincrement": False}
    )
    codigo: str = Field(sa_type=Text, unique=True)
    nombre: str = Field(sa_type=Text)


class CondicionTabla(SQLModel, table=True):
    """Tabla `condicion`."""

    __tablename__ = "condicion"

    id: int = Field(
        primary_key=True, sa_type=SmallInteger, sa_column_kwargs={"autoincrement": False}
    )
    codigo: str = Field(sa_type=Text, unique=True)
    nombre: str = Field(sa_type=Text)
    descripcion: str | None = Field(default=None, sa_type=Text)


class ReglaTabla(SQLModel, table=True):
    """Tabla `regla`: una fila por versión de regla."""

    __tablename__ = "regla"
    __table_args__ = (
        CheckConstraint(
            "nivel = ANY (ARRAY['ORIENTAR', 'ADVERTIR', 'DERIVAR'])", name="regla_nivel_check"
        ),
        CheckConstraint(
            "estado = ANY (ARRAY['pendiente', 'aprobada', 'rechazada'])", name="regla_estado_check"
        ),
        UniqueConstraint("codigo", "version", name="regla_codigo_version_key"),
    )

    id: int = Field(primary_key=True, sa_column_kwargs={"autoincrement": False})
    codigo: str = Field(sa_type=Text)
    version: int = Field(sa_type=SmallInteger)
    medicamento_id: int = Field(foreign_key="medicamento.id", sa_type=SmallInteger)
    nivel: str = Field(sa_type=Text)
    sin_condiciones: bool
    especificidad: int = Field(sa_type=SmallInteger)
    estado: str = Field(sa_type=Text)
    aprobada_por: str | None = Field(default=None, sa_type=Text)
    fecha_aprobacion: date | None = Field(default=None, sa_type=Date)
    fuente: str | None = Field(default=None, sa_type=Text)
    creado_en: datetime | None = Field(
        default=None,
        nullable=False,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"server_default": text("now()")},
    )


class ReglaSintomaTabla(SQLModel, table=True):
    """Tabla `regla_sintoma`: síntomas requeridos por cada versión de regla."""

    __tablename__ = "regla_sintoma"

    regla_id: int = Field(primary_key=True, foreign_key="regla.id", ondelete="CASCADE")
    sintoma_id: int = Field(primary_key=True, foreign_key="sintoma.id", sa_type=SmallInteger)


class ReglaCondicionTabla(SQLModel, table=True):
    """Tabla `regla_condicion`: condiciones requeridas por cada versión de regla."""

    __tablename__ = "regla_condicion"

    regla_id: int = Field(primary_key=True, foreign_key="regla.id", ondelete="CASCADE")
    condicion_id: int = Field(primary_key=True, foreign_key="condicion.id", sa_type=SmallInteger)


class ReglaMensajeTabla(SQLModel, table=True):
    """Tabla `regla_mensaje`: mensajes ordenados de cada versión de regla."""

    __tablename__ = "regla_mensaje"
    __table_args__ = (
        UniqueConstraint("regla_id", "orden", name="regla_mensaje_regla_id_orden_key"),
    )

    id: int = Field(primary_key=True, sa_column_kwargs={"autoincrement": False})
    regla_id: int = Field(foreign_key="regla.id", ondelete="CASCADE")
    orden: int = Field(sa_type=SmallInteger)
    texto: str = Field(sa_type=Text)


class ConsultaTabla(SQLModel, table=True):
    """Tabla `consulta`: registro anónimo de cada consulta respondida."""

    __tablename__ = "consulta"
    __table_args__ = (
        CheckConstraint(
            "nivel_resultado = ANY (ARRAY['ORIENTAR', 'ADVERTIR', 'DERIVAR'])",
            name="consulta_nivel_resultado_check",
        ),
    )

    id: uuid.UUID | None = Field(
        default=None,
        primary_key=True,
        sa_type=Uuid,
        sa_column_kwargs={"server_default": text("gen_random_uuid()")},
    )
    creado_en: datetime | None = Field(
        default=None,
        nullable=False,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"server_default": text("now()")},
    )
    medicamento_id: int = Field(foreign_key="medicamento.id", sa_type=SmallInteger)
    nivel_resultado: str | None = Field(default=None, sa_type=Text)
    sin_regla: bool = Field(default=False, sa_column_kwargs={"server_default": text("false")})


class ConsultaSintomaTabla(SQLModel, table=True):
    """Tabla `consulta_sintoma`."""

    __tablename__ = "consulta_sintoma"

    consulta_id: uuid.UUID = Field(
        primary_key=True, foreign_key="consulta.id", ondelete="CASCADE", sa_type=Uuid
    )
    sintoma_id: int = Field(primary_key=True, foreign_key="sintoma.id", sa_type=SmallInteger)


class ConsultaCondicionTabla(SQLModel, table=True):
    """Tabla `consulta_condicion`."""

    __tablename__ = "consulta_condicion"

    consulta_id: uuid.UUID = Field(
        primary_key=True, foreign_key="consulta.id", ondelete="CASCADE", sa_type=Uuid
    )
    condicion_id: int = Field(primary_key=True, foreign_key="condicion.id", sa_type=SmallInteger)


class ConsultaReglaDisparadaTabla(SQLModel, table=True):
    """Tabla `consulta_regla_disparada`: reglas (versión exacta) en orden de presentación."""

    __tablename__ = "consulta_regla_disparada"

    consulta_id: uuid.UUID = Field(
        primary_key=True, foreign_key="consulta.id", ondelete="CASCADE", sa_type=Uuid
    )
    regla_id: int = Field(primary_key=True, foreign_key="regla.id")
    orden: int = Field(sa_type=SmallInteger)
