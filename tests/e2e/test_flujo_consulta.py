"""Flujo completo en navegador: formulario, envío, resultado y explicación (Principio VIII, e2e).

Escenarios 1, 2, 3, 6, 8 y 9 de quickstart.md, contra la base de pruebas.
"""

import re
import time

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e

AVISO = "Prototipo académico: no reemplaza la consulta médica o farmacéutica."


def _hasta_el_paso_3(
    page: Page, servidor: str, medicamento: str, sintomas: list[str], condiciones: list[str]
) -> None:
    """Recorre los pasos 1 a 3 marcando las opciones; queda listo para enviar la consulta."""
    page.goto(f"{servidor}/consulta/paso/1")
    expect(page.locator("#aviso")).to_have_text(AVISO)
    page.click(f'button[data-valor="{medicamento}"]')
    page.click("button.avanzar")
    expect(page.locator("#aviso")).to_have_text(AVISO)
    for sintoma in sintomas:
        page.click(f'button[data-valor="{sintoma}"]')
    page.click("button.avanzar")
    expect(page.locator("#aviso")).to_have_text(AVISO)
    for condicion in condiciones:
        page.click(f'button[data-valor="{condicion}"]')
    if not condiciones:
        page.click("button[data-ninguna]")


def _consultar(
    page: Page, servidor: str, medicamento: str, sintomas: list[str], condiciones: list[str]
) -> None:
    _hasta_el_paso_3(page, servidor, medicamento, sintomas, condiciones)
    page.click("button.avanzar")
    expect(page.locator("#resultado")).to_be_visible()
    expect(page.locator("#aviso")).to_have_text(AVISO)


@pytest.mark.parametrize(
    "medicamento, sintomas, condiciones, nivel, etiqueta, regla",
    [
        ("PARACETAMOL", ["DOLOR_CABEZA"], [], "ORIENTAR", "Orientar", "R01"),
        ("PARACETAMOL", ["DOLOR_CABEZA"], ["EMBARAZO"], "ADVERTIR", "Advertir", "R10"),
        ("PARACETAMOL", ["FIEBRE"], ["EMBARAZO"], "DERIVAR", "Derivar al médico", "R11"),
    ],
    ids=["escenario-1-orientar", "escenario-2-advertir", "escenario-3-derivar"],
)
def test_un_caso_por_nivel(
    page: Page,
    servidor: str,
    medicamento: str,
    sintomas: list[str],
    condiciones: list[str],
    nivel: str,
    etiqueta: str,
    regla: str,
) -> None:
    _consultar(page, servidor, medicamento, sintomas, condiciones)

    expect(page.locator("#resultado")).to_have_attribute("data-nivel", nivel)
    expect(page.locator("#nivel")).to_have_text(etiqueta)
    expect(page.locator(f'.regla[data-regla="{regla}"] li').first).to_be_visible()
    expect(page.locator("#explicacion")).to_contain_text(f"Reglas aplicadas: {regla}")
    expect(page.locator("#mensajes-sistema")).to_have_count(0)


def test_escenario_6_salvaguarda_de_cobertura(page: Page, servidor: str) -> None:
    _consultar(page, servidor, "IBUPROFENO", ["DOLOR_CABEZA", "FIEBRE"], [])

    expect(page.locator("#resultado")).to_have_attribute("data-nivel", "ADVERTIR")
    expect(page.locator("#resultado")).to_have_attribute("data-salvaguarda", "true")
    expect(page.locator("#nivel")).to_have_text("Advertir")
    expect(page.locator('.regla[data-regla="R18"] li').first).to_be_visible()
    sistema = page.locator("#mensajes-sistema")
    expect(sistema).to_contain_text("Mensaje del sistema (no proviene de una regla validada)")
    expect(sistema).to_contain_text("«Fiebre» no tiene orientación específica con Ibuprofeno")
    expect(sistema.locator(".distintivo-pendiente")).to_have_text("Pendiente de aprobación médica")
    expect(page.locator("#explicacion")).to_contain_text("Reglas aplicadas: R18")
    expect(page.locator("#explicacion")).to_contain_text(
        "Salvaguarda del sistema (pendiente de aprobación médica): "
        "síntomas sin regla aplicable: Fiebre"
    )


@pytest.mark.parametrize(
    "medicamento, sintomas, condiciones",
    [
        ("IBUPROFENO", ["FIEBRE"], []),
        ("PARACETAMOL", ["DOLOR_CABEZA"], ["USO_ASPIRINA"]),
    ],
    ids=["escenario-8-ibuprofeno-fiebre", "escenario-9-paracetamol-cabeza-aspirina"],
)
def test_combinacion_no_cubierta(
    page: Page, servidor: str, medicamento: str, sintomas: list[str], condiciones: list[str]
) -> None:
    _consultar(page, servidor, medicamento, sintomas, condiciones)

    expect(page.locator("#resultado")).to_have_attribute("data-nivel", "DERIVAR")
    expect(page.locator("#nivel")).to_have_text("Derivar al médico")
    expect(page.locator(".regla")).to_have_count(0)
    sistema = page.locator("#mensajes-sistema")
    expect(sistema).to_contain_text(
        "Esta combinación de medicamento, síntomas y condiciones no está cubierta por la base "
        "de conocimiento validada. Consulte con un médico."
    )
    expect(sistema.locator(".distintivo-pendiente")).to_have_count(0)
    expect(page.locator("#explicacion")).to_contain_text("Ninguna regla aplicada")
    expect(page.locator("#explicacion")).not_to_contain_text("Salvaguarda del sistema")


def test_escenario_6_responde_en_menos_de_2_segundos(page: Page, servidor: str) -> None:
    """SC-005: del envío de la consulta a la aparición de #resultado, menos de 2 s."""
    _hasta_el_paso_3(page, servidor, "IBUPROFENO", ["DOLOR_CABEZA", "FIEBRE"], [])

    inicio = time.perf_counter()
    page.click("button.avanzar")
    page.wait_for_selector("#resultado", state="visible")
    transcurrido = time.perf_counter() - inicio

    assert transcurrido < 2.0, f"{transcurrido:.2f} s"


def test_paso_3_ninguna_es_excluyente_y_controla_el_avance(page: Page, servidor: str) -> None:
    """Al marcar «ninguna» se limpian las condiciones y viceversa; sin elegir, no se avanza."""
    page.goto(f"{servidor}/consulta/paso/3?medicamento=PARACETAMOL&sintomas=FIEBRE")
    avanzar = page.locator("button.avanzar")
    ninguna = page.locator("button[data-ninguna]")
    embarazo = page.locator('button[data-valor="EMBARAZO"]')
    diabetes = page.locator('button[data-valor="DIABETES"]')

    expect(avanzar).to_have_attribute("aria-disabled", "true")
    avanzar.click(
        force=True
    )  # Playwright lo considera deshabilitado; se fuerza para probar el bloqueo.
    expect(page).to_have_url(f"{servidor}/consulta/paso/3?medicamento=PARACETAMOL&sintomas=FIEBRE")

    embarazo.click()
    diabetes.click()
    expect(embarazo).to_have_attribute("aria-pressed", "true")
    expect(avanzar).to_have_attribute("aria-disabled", "false")

    ninguna.click()
    expect(ninguna).to_have_attribute("aria-pressed", "true")
    expect(embarazo).to_have_attribute("aria-pressed", "false")
    expect(diabetes).to_have_attribute("aria-pressed", "false")
    expect(avanzar).to_have_attribute("aria-disabled", "false")

    embarazo.click()
    expect(ninguna).to_have_attribute("aria-pressed", "false")

    embarazo.click()
    expect(avanzar).to_have_attribute("aria-disabled", "true")
    expect(avanzar).to_have_attribute("aria-label", re.compile("Marque al menos una condición"))


def test_volver_conserva_lo_elegido(page: Page, servidor: str) -> None:
    _hasta_el_paso_3(page, servidor, "IBUPROFENO", ["DOLOR_CABEZA", "FIEBRE"], ["DIABETES"])
    page.click("a.volver")

    expect(page.locator("#titulo-paso")).to_have_text("Seleccione el síntoma a tratar")
    expect(page.locator('button[data-valor="DOLOR_CABEZA"]')).to_have_attribute(
        "aria-pressed", "true"
    )
    expect(page.locator('button[data-valor="FIEBRE"]')).to_have_attribute("aria-pressed", "true")
    expect(page.locator(".chip")).to_have_text(["Ibuprofeno"])

    page.click("a.volver")
    expect(page.locator('button[data-valor="IBUPROFENO"]')).to_have_attribute(
        "aria-pressed", "true"
    )
