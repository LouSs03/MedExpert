from domain.nivel import EstadoRegla, Nivel


def test_severidad_ordena_orientar_advertir_derivar() -> None:
    assert Nivel.ORIENTAR.severidad == 1
    assert Nivel.ADVERTIR.severidad == 2
    assert Nivel.DERIVAR.severidad == 3
    assert Nivel.ORIENTAR.severidad < Nivel.ADVERTIR.severidad < Nivel.DERIVAR.severidad


def test_valores_coinciden_con_la_base() -> None:
    assert [n.value for n in Nivel] == ["ORIENTAR", "ADVERTIR", "DERIVAR"]


def test_etiquetas_visibles() -> None:
    assert Nivel.ORIENTAR.etiqueta == "Orientar"
    assert Nivel.ADVERTIR.etiqueta == "Advertir"
    assert Nivel.DERIVAR.etiqueta == "Derivar al médico"


def test_estados_de_regla() -> None:
    assert {e.name for e in EstadoRegla} == {"PENDIENTE", "APROBADA", "RECHAZADA"}
    assert EstadoRegla("aprobada") is EstadoRegla.APROBADA
