import pytest

from domain.mensajes_sistema import ConfiguracionSalvaguarda
from infrastructure.config import ConfiguracionInvalida, cargar_configuracion

URL_PSYCOPG = "postgresql+psycopg://usuario:clave@host:5432/postgres"
URL_LIBPQ = "postgresql://usuario:clave@host:5432/postgres"


def test_acepta_esquema_postgresql_psycopg() -> None:
    config = cargar_configuracion({"DATABASE_URL": URL_PSYCOPG})

    assert config.database_url == URL_PSYCOPG


def test_normaliza_postgresql_a_postgresql_psycopg() -> None:
    config = cargar_configuracion({"DATABASE_URL": URL_LIBPQ})

    assert config.database_url == URL_PSYCOPG


@pytest.mark.parametrize(
    "valor",
    [
        "DATABASE_URL=postgresql+psycopg://usuario:clave@host:5432/postgres",
        "postgresql++psycopg://usuario:clave@host:5432/postgres",
        "mysql://usuario:clave@host:3306/db",
        "postgres://usuario:clave@host:5432/postgres",
    ],
)
def test_rechaza_otros_esquemas_sin_mostrar_la_url(valor: str) -> None:
    with pytest.raises(ConfiguracionInvalida) as error:
        cargar_configuracion({"DATABASE_URL": valor})

    texto = str(error.value)
    assert valor not in texto
    assert "clave" not in texto


def test_falta_database_url() -> None:
    with pytest.raises(ConfiguracionInvalida):
        cargar_configuracion({})


def test_salvaguarda_pendiente_por_defecto() -> None:
    config = cargar_configuracion({"DATABASE_URL": URL_PSYCOPG})

    assert config.salvaguarda == ConfiguracionSalvaguarda(pendiente_aprobacion=True)


@pytest.mark.parametrize(
    "valor, esperado",
    [("true", True), ("TRUE", True), (" True ", True), ("false", False), ("False", False)],
)
def test_salvaguarda_acepta_true_y_false_sin_distinguir_mayusculas(
    valor: str, esperado: bool
) -> None:
    config = cargar_configuracion(
        {"DATABASE_URL": URL_PSYCOPG, "SALVAGUARDA_PENDIENTE_APROBACION": valor}
    )

    assert config.salvaguarda.pendiente_aprobacion is esperado


@pytest.mark.parametrize("valor", ["quizas", "1", "si", ""])
def test_salvaguarda_rechaza_otros_valores(valor: str) -> None:
    with pytest.raises(ConfiguracionInvalida):
        cargar_configuracion(
            {"DATABASE_URL": URL_PSYCOPG, "SALVAGUARDA_PENDIENTE_APROBACION": valor}
        )


def test_repr_no_muestra_la_url() -> None:
    config = cargar_configuracion(
        {"DATABASE_URL": URL_PSYCOPG, "TEST_DATABASE_URL": "postgresql://u:otra@h/db"}
    )

    assert "clave" not in repr(config)
    assert "otra" not in repr(config)


def test_secretos_incluyen_ambas_urls() -> None:
    config = cargar_configuracion(
        {"DATABASE_URL": URL_LIBPQ, "TEST_DATABASE_URL": "postgresql://u:otra@h/db"}
    )

    assert URL_LIBPQ in config.secretos
    assert URL_PSYCOPG in config.secretos
    assert "postgresql://u:otra@h/db" in config.secretos
