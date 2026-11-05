"""Flujo completo en navegador: formulario, envío, resultado y explicación (Principio VIII, e2e).

Escenarios 1, 2, 3, 6, 8 y 9 de quickstart.md, contra la base de pruebas.
"""

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e

AVISO = "Prototipo académico: no reemplaza la consulta médica o farmacéutica."


def _consultar(
    page: Page, servidor: str, medicamento: str, sintomas: list[str], condiciones: list[str]
) -> None:
    page.goto(servidor)
    expect(page.locator("#aviso")).to_have_text(AVISO)
    page.check(f'input[name="medicamento"][value="{medicamento}"]')
    for sintoma in sintomas:
        page.check(f'input[name="sintomas"][value="{sintoma}"]')
    for condicion in condiciones:
        page.check(f'input[name="condiciones"][value="{condicion}"]')
    page.click('button[type="submit"]')
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
