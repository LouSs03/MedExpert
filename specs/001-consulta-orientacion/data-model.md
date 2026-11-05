# Data Model: Consulta de orientación sobre automedicación

**Feature**: [spec.md](spec.md) | **Research**: [research.md](research.md) | rev. 2

Hay dos niveles: las **entidades de dominio** (`src/domain/`, Python puro sin dependencias
externas) y su **correspondencia con las tablas existentes**, que esta funcionalidad no crea ni
altera. Todas las entidades de dominio son inmutables (`@dataclass(frozen=True)` o `Enum`).

## Entidades de dominio

### Nivel (Enum)

| Valor | Etiqueta visible | Severidad |
|-------|------------------|-----------|
| `ORIENTAR` | Orientar | 1 |
| `ADVERTIR` | Advertir | 2 |
| `DERIVAR` | Derivar al médico | 3 |

- La severidad define el orden total que usa `ResolucionPorSeveridad` (FR-008) y el primer
  criterio de orden de FR-009.
- Los valores coinciden con los `CHECK` de `regla.nivel` y `consulta.nivel_resultado`.

### EstadoRegla (Enum)

`PENDIENTE` · `APROBADA` · `RECHAZADA`. Solo se cargan reglas en `APROBADA` (FR-006). Esta
funcionalidad nunca cambia estados (FR-017).

### Medicamento · Sintoma · Condicion (objetos de valor)

| Campo | Tipo | Regla |
|-------|------|-------|
| `id` | `int` | Identidad en la base (necesaria para persistir) y criterio de orden en pantalla |
| `codigo` | `str` | Único; cumple `^[A-Z][A-Z0-9_]*$` |
| `nombre` | `str` | Texto visible en el formulario y en el mensaje de salvaguarda |

### Vocabulario

Agrupa los tres catálogos cargados al arrancar: `medicamentos`, `sintomas` y `condiciones`, como
`tuple[...]` ordenadas por `id`.

- `validar(medicamento: str, sintomas: Iterable[str], condiciones: Iterable[str]) -> HechosConsulta`
  lanza `VocabularioInvalido` (con la lista de valores rechazados) si un código no existe, si no
  hay exactamente un medicamento o si no hay al menos un síntoma (FR-002 a FR-005).

### HechosConsulta

| Campo | Tipo | Regla |
|-------|------|-------|
| `medicamento` | `Medicamento` | Exactamente uno |
| `sintomas` | `frozenset[Sintoma]` | ≥ 1 |
| `condiciones` | `frozenset[Condicion]` | ≥ 0 |

Solo se construye a través de `Vocabulario.validar`, así que siempre es válido.

### Regla

| Campo | Tipo | Origen |
|-------|------|--------|
| `id` | `int` | `regla.id` (identifica una **versión** concreta) |
| `codigo` | `str` | `regla.codigo` (p. ej. `R07`) |
| `version` | `int` | `regla.version` |
| `medicamento` | `str` (código) | `medicamento.codigo` vía `regla.medicamento_id` |
| `sintomas` | `frozenset[str]` | `regla_sintoma` → `sintoma.codigo`; ≥ 1 |
| `condiciones` | `frozenset[str]` | `regla_condicion` → `condicion.codigo` |
| `sin_condiciones` | `bool` | `regla.sin_condiciones` |
| `especificidad` | `int` | `regla.especificidad` |
| `nivel` | `Nivel` | `regla.nivel` |
| `estado` | `EstadoRegla` | `regla.estado` |
| `mensajes` | `tuple[str, ...]` | `regla_mensaje.texto` ordenado por `orden`; ≥ 1 |

Semántica de disparo (FR-006): la regla se dispara si y solo si `hechos.medicamento.codigo ==
medicamento`, `sintomas ⊆ códigos(hechos.sintomas)`, `condiciones ⊆ códigos(hechos.condiciones)`
y, si `sin_condiciones`, `hechos.condiciones` está vacío. La evaluación la hace el motor CLIPS; el
dominio no la reimplementa, pero las pruebas usan esta definición como oráculo.

Invariantes, comprobados al cargar (si alguno falla, la base queda "no disponible", FR-018):

- `sin_condiciones = true` implica que `condiciones` está vacío.
- `especificidad = len(sintomas) + len(condiciones)`. Se cumple en los datos actuales; si en el
  futuro no se cumple, se registra un aviso y no se bloquea la carga.
- Todo código referenciado existe en el `Vocabulario`.
- No hay dos reglas con el mismo `codigo` en la base cargada (solo la versión más reciente).

### BaseConocimiento

`vocabulario: Vocabulario` y `reglas: tuple[Regla, ...]` (≥ 1). La produce
`CargarBaseConocimiento` y es inmutable durante toda la vida del proceso.

### ReglaDisparada

| Campo | Tipo |
|-------|------|
| `regla` | `Regla` |
| `orden` | `int` (1..n) |

Orden (FR-009, SC-010): `regla.nivel` por severidad descendente, luego `regla.especificidad`
descendente, luego `regla.codigo` ascendente.

### TipoMensajeSistema (Enum)

`COMBINACION_NO_CUBIERTA` (FR-011) · `SINTOMA_NO_CUBIERTO` (FR-020).

### MensajeSistema

| Campo | Tipo | Regla |
|-------|------|-------|
| `tipo` | `TipoMensajeSistema` | |
| `texto` | `str` | Generado a partir de una plantilla del dominio (ver abajo) |
| `pendiente_aprobacion` | `bool` | `SINTOMA_NO_CUBIERTO`: el valor de `ConfiguracionSalvaguarda`; `COMBINACION_NO_CUBIERTA`: siempre `False` |
| `sintoma` | `Sintoma \| None` | Solo para `SINTOMA_NO_CUBIERTO` |

Plantillas (constantes del dominio; son los **únicos** textos orientativos que no vienen de una
regla, Principios I y II):

- `COMBINACION_NO_CUBIERTA`: *"Esta combinación de medicamento, síntomas y condiciones no está
  cubierta por la base de conocimiento validada. Consulte con un médico."*
- `SINTOMA_NO_CUBIERTO`: *"«{sintoma.nombre}» no tiene orientación específica con
  {medicamento.nombre} en la base de conocimiento validada. Consulte a un médico o
  farmacéutico."* El texto literal debe copiarse a FR-020 antes de implementar (research P6).

### ConfiguracionSalvaguarda

| Campo | Tipo | Origen |
|-------|------|--------|
| `pendiente_aprobacion` | `bool` | Variable `SALVAGUARDA_PENDIENTE_APROBACION`, por defecto `True` (research D14) |

Solo controla la marca. No permite desactivar la salvaguarda ni cambiar su nivel mínimo ni su
texto.

### Resolucion

La devuelve `EstrategiaResolucionNivel.resolver(hechos, disparadas)`.

| Campo | Tipo | Regla |
|-------|------|-------|
| `nivel` | `Nivel` | Ver la tabla de decisión |
| `sin_regla` | `bool` | `True` si no se disparó ninguna regla |
| `reglas_disparadas` | `tuple[ReglaDisparada, ...]` | Ordenadas según FR-009 |
| `sintomas_no_cubiertos` | `tuple[Sintoma, ...]` | `hechos.sintomas − ⋃ regla.sintomas`, por `id`; vacío si `sin_regla` |

Tabla de decisión:

| Reglas disparadas | Síntomas no cubiertos | `nivel` | `sin_regla` |
|-------------------|-----------------------|---------|-------------|
| ninguna | — (no se evalúa) | `DERIVAR` | `True` |
| ≥ 1 | ninguno | máximo de severidad de las reglas | `False` |
| ≥ 1 | ≥ 1 | `max(máximo de las reglas, ADVERTIR)` | `False` |

### ResultadoEvaluacion

| Campo | Tipo | Regla |
|-------|------|-------|
| `nivel` | `Nivel` | De `Resolucion` |
| `sin_regla` | `bool` | De `Resolucion` |
| `reglas_disparadas` | `tuple[ReglaDisparada, ...]` | Vacía si `sin_regla` |
| `sintomas_no_cubiertos` | `tuple[Sintoma, ...]` | Vacía si `sin_regla` o si todo quedó cubierto |
| `mensajes_sistema` | `tuple[MensajeSistema, ...]` | `sin_regla` → exactamente un `COMBINACION_NO_CUBIERTA`; si no, un `SINTOMA_NO_CUBIERTO` por cada síntoma no cubierto (en su orden); nunca los dos tipos a la vez |
| `persistida` | `bool` | `False` si falló el registro (FR-019) |
| `consulta_id` | `UUID \| None` | `None` si no se persistió |

`salvaguarda_activada` se deriva: es `True` si `sintomas_no_cubiertos` no está vacío.

### Consulta

| Campo | Tipo |
|-------|------|
| `hechos` | `HechosConsulta` |
| `nivel` | `Nivel` (ya elevado por la salvaguarda si correspondía) |
| `sin_regla` | `bool` |
| `reglas_disparadas` | `tuple[ReglaDisparada, ...]` |

No hay ningún campo de datos personales (FR-015). La activación de la salvaguarda no se guarda:
se reconstruye a partir de `hechos` y de las versiones de `reglas_disparadas` (Assumptions de la
spec). El `id` y `creado_en` los asigna la base.

### Errores de dominio

- `VocabularioInvalido(valores_rechazados: tuple[str, ...])`
- `BaseConocimientoNoDisponible(motivo: str)` (el motivo nunca incluye la cadena de conexión)

## Correspondencia con las tablas existentes (solo lectura del esquema)

| Entidad | Tabla(s) | Operación en esta funcionalidad |
|---------|----------|---------------------------------|
| Medicamento, Sintoma, Condicion | `medicamento`, `sintoma`, `condicion` | SELECT al arrancar |
| Regla | `regla` + `regla_sintoma` + `regla_condicion` + `regla_mensaje` | SELECT al arrancar |
| Consulta | `consulta` (`medicamento_id`, `nivel_resultado`, `sin_regla`) | INSERT por consulta |
| Consulta.hechos | `consulta_sintoma`, `consulta_condicion` | INSERT por consulta |
| Consulta.reglas_disparadas | `consulta_regla_disparada` (`regla_id`, `orden`) | INSERT por consulta |
| MensajeSistema, ConfiguracionSalvaguarda | — | No se persisten |

- Las cinco inserciones de una consulta van en **una sola transacción**
  (`PostgresConsultaRepository`).
- `consulta.id` (`gen_random_uuid()`) y `consulta.creado_en` (`now()`) los genera la base.
- Reglas vigentes (`PostgresReglaRepository`):
  `SELECT DISTINCT ON (codigo) ... FROM regla WHERE estado = 'aprobada' ORDER BY codigo, version DESC`.
- Los modelos SQLModel (`table=True`) reflejan estas tablas en `infrastructure/db/modelos.py`.
  **Nunca** se llama a `create_all` ni a migraciones desde la aplicación.
- La base de pruebas (`TEST_DATABASE_URL`) tiene el mismo esquema y la misma base de conocimiento
  (FR-021).

## Transiciones de estado

Esta funcionalidad no tiene transiciones persistidas: las reglas son de solo lectura y una
consulta, una vez escrita, no cambia. La única "transición" es de configuración: cuando el médico
apruebe el texto de la salvaguarda, `SALVAGUARDA_PENDIENTE_APROBACION` pasa de `true` a `false`
(research D14).
