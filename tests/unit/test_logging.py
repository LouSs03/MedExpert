import io
import logging
from collections.abc import Iterator

import pytest

from infrastructure.config import cargar_configuracion
from infrastructure.logging import REDACTADO, FiltroSecretos, configurar_logging

URL = "postgresql+psycopg://u:clave@host:5432/db"
SECRETO_TEST = "otra-clave-secreta-de-pruebas"


@pytest.fixture
def capturado() -> Iterator[tuple[logging.Logger, io.StringIO, logging.Handler]]:
    salida = io.StringIO()
    manejador = logging.StreamHandler(salida)
    manejador.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    logger = logging.getLogger("prueba.secretos")
    logger.handlers = [manejador]
    logger.propagate = False
    logger.setLevel(logging.DEBUG)
    yield logger, salida, manejador
    logger.handlers = []


def test_redacta_url_en_el_mensaje(
    capturado: tuple[logging.Logger, io.StringIO, logging.Handler],
) -> None:
    logger, salida, manejador = capturado
    manejador.addFilter(FiltroSecretos())

    logger.error("No se pudo conectar a %s", URL)

    texto = salida.getvalue()
    assert REDACTADO in texto
    assert "clave" not in texto


def test_redacta_url_en_el_texto_de_la_excepcion(
    capturado: tuple[logging.Logger, io.StringIO, logging.Handler],
) -> None:
    logger, salida, manejador = capturado
    manejador.addFilter(FiltroSecretos())

    try:
        raise RuntimeError(f"fallo simulado {URL}")
    except RuntimeError:
        logger.error("No se pudo persistir la consulta", exc_info=True)

    texto = salida.getvalue()
    assert "RuntimeError" in texto
    assert REDACTADO in texto
    assert "clave" not in texto


def test_redacta_valores_exactos_configurados(
    capturado: tuple[logging.Logger, io.StringIO, logging.Handler],
) -> None:
    logger, salida, manejador = capturado
    manejador.addFilter(FiltroSecretos(secretos=(SECRETO_TEST,)))

    logger.warning("valor %s y mensaje con %s", SECRETO_TEST, SECRETO_TEST)

    texto = salida.getvalue()
    assert SECRETO_TEST not in texto
    assert texto.count(REDACTADO) == 2


def test_no_altera_mensajes_sin_secretos(
    capturado: tuple[logging.Logger, io.StringIO, logging.Handler],
) -> None:
    logger, salida, manejador = capturado
    manejador.addFilter(FiltroSecretos())

    logger.info("Base de conocimiento cargada: %d reglas", 30)

    assert salida.getvalue().strip() == "INFO Base de conocimiento cargada: 30 reglas"


def test_configurar_logging_instala_el_filtro_en_los_manejadores_raiz() -> None:
    salida = io.StringIO()
    manejador = logging.StreamHandler(salida)
    raiz = logging.getLogger()
    raiz.addHandler(manejador)
    try:
        config = cargar_configuracion(
            {"DATABASE_URL": URL, "TEST_DATABASE_URL": f"postgresql://u:{SECRETO_TEST}@h/db"}
        )
        configurar_logging(config)

        logging.getLogger("prueba.hijo").error(
            "fallo con %s y %s", URL, f"postgresql://u:{SECRETO_TEST}@h/db"
        )

        texto = salida.getvalue()
        assert "clave" not in texto
        assert SECRETO_TEST not in texto
        assert REDACTADO in texto
    finally:
        raiz.removeHandler(manejador)
        for h in raiz.handlers:
            for f in list(h.filters):
                if isinstance(f, FiltroSecretos):
                    h.removeFilter(f)
