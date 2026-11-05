"""Configuración de la aplicación leída de variables de entorno (Principio X)."""

import os
from collections.abc import Mapping
from dataclasses import dataclass, field

from dotenv import load_dotenv

from domain.mensajes_sistema import ConfiguracionSalvaguarda

ESQUEMA_SQLALCHEMY = "postgresql+psycopg://"
ESQUEMA_LIBPQ = "postgresql://"
VARIABLES_SECRETAS = ("DATABASE_URL", "TEST_DATABASE_URL")


class ConfiguracionInvalida(Exception):
    """La configuración es incompleta o tiene un formato no admitido.

    El mensaje nunca muestra secretos.
    """


@dataclass(frozen=True)
class Configuracion:
    """Valores de configuración validados.

    La URL y los secretos no aparecen en `repr`, para que nunca terminen en un log por accidente.
    """

    database_url: str = field(repr=False)
    salvaguarda: ConfiguracionSalvaguarda
    secretos: tuple[str, ...] = field(default=(), repr=False)


def _normalizar_url(valor: str) -> str:
    if valor.startswith(ESQUEMA_SQLALCHEMY):
        return valor
    if valor.startswith(ESQUEMA_LIBPQ):
        return ESQUEMA_SQLALCHEMY + valor[len(ESQUEMA_LIBPQ) :]
    raise ConfiguracionInvalida(
        "DATABASE_URL debe empezar por 'postgresql+psycopg://' o 'postgresql://' "
        "(revise que el nombre de la variable no esté repetido dentro del valor)."
    )


def _leer_salvaguarda(entorno: Mapping[str, str]) -> ConfiguracionSalvaguarda:
    valor = entorno.get("SALVAGUARDA_PENDIENTE_APROBACION", "true").strip().lower()
    if valor not in {"true", "false"}:
        raise ConfiguracionInvalida(
            "SALVAGUARDA_PENDIENTE_APROBACION solo admite los valores 'true' o 'false'."
        )
    return ConfiguracionSalvaguarda(pendiente_aprobacion=valor == "true")


def cargar_configuracion(entorno: Mapping[str, str] | None = None) -> Configuracion:
    """Lee y valida la configuración; lanza ConfiguracionInvalida sin revelar secretos.

    Sin argumento, carga `.env` si existe (sin sobrescribir variables ya definidas) y usa
    `os.environ`; con un `entorno` explícito, solo usa ese diccionario.
    """
    if entorno is None:
        load_dotenv(override=False)
        entorno = os.environ

    crudo = entorno.get("DATABASE_URL", "").strip()
    if not crudo:
        raise ConfiguracionInvalida("Falta la variable de entorno DATABASE_URL.")
    url = _normalizar_url(crudo)

    secretos = {crudo, url}
    for nombre in VARIABLES_SECRETAS:
        valor = entorno.get(nombre, "").strip()
        if valor:
            secretos.add(valor)

    return Configuracion(
        database_url=url,
        salvaguarda=_leer_salvaguarda(entorno),
        secretos=tuple(sorted(secretos, key=len, reverse=True)),
    )
