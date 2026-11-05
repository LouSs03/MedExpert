from domain.mensajes_sistema import (
    ConfiguracionSalvaguarda,
    TipoMensajeSistema,
    mensaje_combinacion_no_cubierta,
    mensaje_sintoma_no_cubierto,
)
from fakes.reglas_ejemplo import DOLOR_DENTAL, FIEBRE, IBUPROFENO, PARACETAMOL


def test_combinacion_no_cubierta_texto_literal_y_sin_pendiente() -> None:
    mensaje = mensaje_combinacion_no_cubierta()

    assert mensaje.tipo is TipoMensajeSistema.COMBINACION_NO_CUBIERTA
    assert mensaje.texto == (
        "Esta combinación de medicamento, síntomas y condiciones no está cubierta por la base "
        "de conocimiento validada. Consulte con un médico."
    )
    assert mensaje.pendiente_aprobacion is False
    assert mensaje.sintoma is None


def test_sintoma_no_cubierto_texto_literal_fr020() -> None:
    mensaje = mensaje_sintoma_no_cubierto(FIEBRE, IBUPROFENO, ConfiguracionSalvaguarda())

    assert mensaje.tipo is TipoMensajeSistema.SINTOMA_NO_CUBIERTO
    assert mensaje.texto == (
        "«Fiebre» no tiene orientación específica con Ibuprofeno en la base de conocimiento "
        "validada. Consulte a un médico o farmacéutico."
    )
    assert mensaje.sintoma == FIEBRE


def test_sintoma_no_cubierto_usa_los_nombres_visibles() -> None:
    mensaje = mensaje_sintoma_no_cubierto(DOLOR_DENTAL, PARACETAMOL, ConfiguracionSalvaguarda())

    assert mensaje.texto.startswith(
        "«Dolor dental» no tiene orientación específica con Paracetamol"
    )


def test_pendiente_por_defecto_es_true() -> None:
    assert ConfiguracionSalvaguarda().pendiente_aprobacion is True


def test_pendiente_sigue_la_configuracion() -> None:
    pendiente = mensaje_sintoma_no_cubierto(
        FIEBRE, IBUPROFENO, ConfiguracionSalvaguarda(pendiente_aprobacion=True)
    )
    aprobado = mensaje_sintoma_no_cubierto(
        FIEBRE, IBUPROFENO, ConfiguracionSalvaguarda(pendiente_aprobacion=False)
    )

    assert pendiente.pendiente_aprobacion is True
    assert aprobado.pendiente_aprobacion is False
    assert pendiente.texto == aprobado.texto
