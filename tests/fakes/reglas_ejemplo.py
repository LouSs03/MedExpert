"""Vocabulario completo (FR-001) y reglas de ejemplo equivalentes a R01, R02, R07, R10, R11 y R18.

Los códigos, niveles, `sin_condiciones` y especificidad son los de la base real (research.md).
Los textos de los mensajes son de ejemplo: las pruebas que necesitan los mensajes aprobados usan la
base de pruebas, no este módulo.
"""

from domain.nivel import EstadoRegla, Nivel
from domain.regla import Regla
from domain.vocabulario import Condicion, Medicamento, Sintoma, Vocabulario

PARACETAMOL = Medicamento(1, "PARACETAMOL", "Paracetamol")
IBUPROFENO = Medicamento(2, "IBUPROFENO", "Ibuprofeno")

DOLOR_CABEZA = Sintoma(1, "DOLOR_CABEZA", "Dolor de cabeza")
FIEBRE = Sintoma(2, "FIEBRE", "Fiebre")
MOLESTIAS_RESPIRATORIAS = Sintoma(
    3, "MOLESTIAS_RESPIRATORIAS", "Molestias respiratorias (resfrío, tos, garganta)"
)
DOLOR_MUSCULAR = Sintoma(4, "DOLOR_MUSCULAR", "Dolor muscular o de espalda")
DOLOR_ABDOMINAL = Sintoma(5, "DOLOR_ABDOMINAL", "Dolor abdominal o gástrico")
DOLOR_DENTAL = Sintoma(6, "DOLOR_DENTAL", "Dolor dental")

EMBARAZO = Condicion(1, "EMBARAZO", "Embarazo")
DIABETES = Condicion(2, "DIABETES", "Diabetes")
HIPERTENSION = Condicion(3, "HIPERTENSION", "Hipertensión")
ADULTO_MAYOR = Condicion(4, "ADULTO_MAYOR", "Adulto mayor (60 años o más)")
OTRO_TRATAMIENTO = Condicion(5, "OTRO_TRATAMIENTO", "Uso de otro tratamiento")
USO_ANTIGRIPAL = Condicion(6, "USO_ANTIGRIPAL", "Uso de antigripal")
USO_ASPIRINA = Condicion(7, "USO_ASPIRINA", "Uso de aspirina")

VOCABULARIO = Vocabulario(
    medicamentos=(PARACETAMOL, IBUPROFENO),
    sintomas=(
        DOLOR_CABEZA,
        FIEBRE,
        MOLESTIAS_RESPIRATORIAS,
        DOLOR_MUSCULAR,
        DOLOR_ABDOMINAL,
        DOLOR_DENTAL,
    ),
    condiciones=(
        EMBARAZO,
        DIABETES,
        HIPERTENSION,
        ADULTO_MAYOR,
        OTRO_TRATAMIENTO,
        USO_ANTIGRIPAL,
        USO_ASPIRINA,
    ),
)


def regla(
    numero: int,
    medicamento: str,
    nivel: Nivel,
    sintomas: tuple[str, ...],
    condiciones: tuple[str, ...] = (),
    mensajes: tuple[str, ...] | None = None,
) -> Regla:
    """Construye una regla aprobada de prueba con `id` igual al número de su código."""
    return Regla(
        id=numero,
        codigo=f"R{numero:02d}",
        version=1,
        medicamento=medicamento,
        sintomas=frozenset(sintomas),
        condiciones=frozenset(condiciones),
        sin_condiciones=not condiciones,
        especificidad=len(sintomas) + len(condiciones),
        nivel=nivel,
        estado=EstadoRegla.APROBADA,
        mensajes=mensajes or (f"Mensaje de ejemplo R{numero:02d}.",),
    )


R01 = regla(1, "PARACETAMOL", Nivel.ORIENTAR, ("DOLOR_CABEZA",))
R02 = regla(2, "PARACETAMOL", Nivel.ORIENTAR, ("FIEBRE",))
R07 = regla(
    7,
    "PARACETAMOL",
    Nivel.ORIENTAR,
    ("DOLOR_CABEZA", "FIEBRE"),
    mensajes=("Mensaje de ejemplo R07 (1).", "Mensaje de ejemplo R07 (2)."),
)
R10 = regla(10, "PARACETAMOL", Nivel.ADVERTIR, ("DOLOR_CABEZA",), ("EMBARAZO",))
R11 = regla(11, "PARACETAMOL", Nivel.DERIVAR, ("FIEBRE",), ("EMBARAZO",))
R18 = regla(18, "IBUPROFENO", Nivel.ORIENTAR, ("DOLOR_CABEZA",))

REGLAS_EJEMPLO: tuple[Regla, ...] = (R01, R02, R07, R10, R11, R18)
