# Research: Consulta de orientación sobre automedicación

**Feature**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md) | **Fecha**: 2026-11-04 (rev. 2)

Fuentes: la spec (con las clarificaciones de la sesión 2026-11-04), la constitución v1.1.0 y una
inspección de **solo lectura** de la base de datos (catálogo, restricciones, RLS y contenido de
las reglas). No se imprimieron credenciales ni nombres de aprobadores. Los escenarios citados se
comprobaron con un prototipo desechable sobre las reglas reales.

**Cambios de la rev. 2**: se incorpora la salvaguarda de cobertura (FR-020, D14), D2 pasa a ser un
requisito de la spec (FR-009), la base de pruebas pasa a ser obligatoria (FR-021, D12), se
resuelve la versión de Python (D13), los adaptadores de persistencia pasan a llamarse
`Postgres*Repository` (D7, D15) y se cierran P1, P2 y P4.

## Hallazgos sobre la base de datos existente

| Tabla | Filas | Contenido |
|-------|-------|-----------|
| `medicamento` | 2 | `PARACETAMOL`, `IBUPROFENO` |
| `sintoma` | 6 | `DOLOR_CABEZA`, `FIEBRE`, `MOLESTIAS_RESPIRATORIAS`, `DOLOR_MUSCULAR`, `DOLOR_ABDOMINAL`, `DOLOR_DENTAL` |
| `condicion` | 7 | `EMBARAZO`, `DIABETES`, `HIPERTENSION`, `ADULTO_MAYOR`, `OTRO_TRATAMIENTO`, `USO_ANTIGRIPAL`, `USO_ASPIRINA` |
| `regla` | 30 | R01–R30, todas en versión 1 y estado `aprobada`; R01–R15 son de paracetamol y R16–R30 de ibuprofeno |
| `regla_sintoma` / `regla_condicion` | 38 / 19 | Hechos requeridos por cada regla |
| `regla_mensaje` | 55 | Mensajes ordenados (`orden`) de cada regla |
| `consulta` y sus tablas hijas | 0 | Registro de consultas, vacío |

- Las 11 tablas tienen RLS activo y **ninguna política**. El rol de la aplicación (propietario de
  las tablas, conectado por el pooler en modo sesión, puerto 5432) no está sujeto a RLS. Los roles
  `anon` y `authenticated` de la API pública no ven nada. Esto cumple el Principio X.
- El texto se guarda en UTF-8 correctamente (verificado a nivel de bytes).
- `especificidad` = nº de síntomas + nº de condiciones en las 30 reglas.
- `regla.aprobada_por` y `regla.fecha_aprobacion` son NULL en las 30 reglas (ver P5).

## Decisiones

### D1. Semántica de disparo de una regla (FR-006)

- **Decision**: una regla se dispara si y solo si (a) el medicamento de la consulta es el de la
  regla, (b) **todos** sus síntomas están marcados, (c) **todas** sus condiciones están marcadas y
  (d) si `sin_condiciones = true`, no hay **ninguna** condición marcada. Los hechos de más no
  impiden el disparo, salvo por (d).
- **Rationale**: decisión registrada en la spec (Clarifications) y coherente con el esquema.
- **Alternatives considered**: coincidencia exacta; reglas sin ausencias. Ambas rechazadas en la
  clarificación.

### D2. Orden de reglas, mensajes y códigos (FR-009, SC-010)

- **Decision**: se muestran **todas** las reglas disparadas, ordenadas por nivel de la regla (más
  severo primero), luego `especificidad` descendente y luego `codigo` ascendente. El orden lo
  calcula la estrategia de resolución en el dominio, no la agenda de CLIPS, así que es
  determinista. Se usa el mismo orden en la pantalla, en el DTO y en
  `consulta_regla_disparada.orden`.
- **Rationale**: requisito FR-009. SC-010 se verifica repitiendo la misma consulta N veces y
  comparando la salida.
- **Alternatives considered**: usar `salience` en CLIPS. Se descarta porque el orden de disparo
  no es contractual y empata entre reglas con la misma salience.

### D3. Resolución del nivel con salvaguarda (Strategy; FR-008, FR-011, FR-020)

- **Decision**: protocolo `EstrategiaResolucionNivel` en `domain/` con la implementación por
  defecto `ResolucionPorSeveridad`. Recibe los hechos y las reglas disparadas y devuelve una
  `Resolucion`:
  1. Sin reglas disparadas: `nivel = DERIVAR`, `sin_regla = True`, sin síntomas no cubiertos. Se
     aplica FR-011 y **no** se evalúa la salvaguarda.
  2. Con reglas: `nivel` = el máximo de severidad entre ellas;
     `sintomas_no_cubiertos = hechos.sintomas − ⋃ regla.sintomas` (ordenados por `id` del
     síntoma).
  3. Si hay síntomas no cubiertos: `nivel = max(nivel, ADVERTIR)`. Nunca rebaja: si el nivel ya
     es DERIVAR, se mantiene.
- **Rationale**: el Principio V exige que la resolución del nivel sea una estrategia sustituible.
  La salvaguarda modifica el nivel, así que forma parte de esa misma estrategia y no de
  condicionales en el caso de uso. La salvaguarda **no** es desactivable: lo configurable es solo
  la marca de "pendiente de aprobación" (D14).
- **Verificación sobre las reglas reales** (las 16.128 combinaciones posibles): la salvaguarda no
  se activa en ninguno de los 30 casos de aceptación, y hace subir de Orientar a Advertir 657 de
  las 731 combinaciones que antes daban Orientar.
- **Alternatives considered**: un decorador `SalvaguardaCobertura` alrededor de la estrategia,
  más piezas para una sola regla de negocio; calcularla en el caso de uso, prohibido por el
  Principio V.

### D4. Traducción de reglas a CLIPS y aislamiento por consulta (Factory)

- **Decision**: `TraductorReglasClips` convierte cada `Regla` en un `defrule`, usando
  `deftemplate` para los hechos de medicamento, síntoma y condición y un hecho `disparo` en el
  lado derecho. `sin_condiciones` se traduce como `(not (condicion))`. Los códigos se validan con
  `^[A-Z][A-Z0-9_]*$` antes de interpolarlos. `FabricaEntornoClips` guarda una tupla inmutable de
  constructos, generada una sola vez al arrancar, y crea un `clips.Environment` **nuevo por cada
  consulta**, construyendo los constructos uno por uno (clipspy no acepta varios por llamada).
  Detalle en [contracts/traduccion-clips.md](contracts/traduccion-clips.md).
- **Rationale**: garantiza FR-016 sin bloqueos. Medido en el prototipo: unos 7,4 ms por consulta.
- **Alternatives considered**: un entorno compartido con `(reset)` (estado global mutable,
  prohibido); un pool de entornos (complejidad innecesaria).

### D5. Ciclo de vida de la base de conocimiento (FR-018)

- **Decision**: en el `lifespan` de FastAPI se ejecuta `CargarBaseConocimiento`, que obtiene el
  vocabulario y las reglas vigentes (filtra `estado = 'aprobada'` y después toma la versión más
  reciente de cada `codigo`). Devuelve una `BaseConocimiento` inmutable que se guarda una sola vez
  en `app.state`. Si falla o devuelve 0 reglas, se guarda el estado "no disponible" y todas las
  pantallas responden 503. Recargar requiere reiniciar.
- **Rationale**: cumple el Principio II sin variables globales de módulo.
- **Alternatives considered**: cargar en cada consulta (lento e inconsistente entre consultas
  simultáneas); recarga en caliente (fuera de alcance).

### D6. Vocabulario cargado desde la base

- **Decision**: los catálogos se cargan con las reglas y forman el `Vocabulario` del dominio. El
  formulario se genera a partir de él, y la validación (FR-005) rechaza cualquier código ajeno. Una
  prueba de integración verifica que coincide exactamente con FR-001.
- **Rationale**: una sola fuente de verdad (Principio II). Además, el mensaje de la salvaguarda
  usa los nombres visibles del vocabulario (`sintoma.nombre`, `medicamento.nombre`).

### D7. Persistencia de la consulta y fallo de registro (FR-014, FR-019)

- **Decision**: puerto `ConsultaRepository` con el adaptador `PostgresConsultaRepository`
  (`infrastructure/db/postgres_consulta_repository.py`), que inserta `consulta` y sus tablas hijas
  en **una sola transacción**. `consulta.nivel_resultado` guarda el nivel **ya elevado** por la
  salvaguarda; `consulta_regla_disparada.regla_id` apunta a la versión concreta y `orden` sigue
  D2. La activación de la salvaguarda no tiene columna propia: se reconstruye a partir de los
  síntomas y las versiones de las reglas registradas (supuesto de la spec). Si la inserción falla:
  `logger.error` saneado y `persistida = False`.
- **Rationale**: clarificación de FR-019; esquema existente sin cambios.
- **Alternatives considered**: añadir columnas `sintomas_no_cubiertos` o `salvaguarda`. Se
  descarta porque la funcionalidad no altera el esquema (FR-017 y Assumptions).

### D8. Saneamiento de logs (Principio X)

- **Decision**: un `logging.Filter` en `infrastructure/logging.py` reemplaza URLs `postgres*://`
  y los valores de `DATABASE_URL` y `TEST_DATABASE_URL` por `<redacted>`. Una prueba unitaria
  fuerza un error con la URL dentro y verifica que no aparece en el log.

### D9. Configuración y conexión

- **Decision**: `infrastructure/config.py` lee `DATABASE_URL` (con `python-dotenv` solo en
  desarrollo). Exige el esquema `postgresql+psycopg://` y acepta `postgresql://` normalizándolo a
  ese. Cualquier otro valor hace fallar el arranque con un mensaje que **no** muestra la URL. El
  motor usa `pool_pre_ping=True`. También lee `SALVAGUARDA_PENDIENTE_APROBACION` (D14).
- **Nota**: el `.env` actual sigue con el prefijo `DATABASE_URL=` duplicado dentro del valor; las
  otras dos erratas no se pueden comprobar hasta corregir esta (P3).

### D10. Interfaz: formulario Jinja2 más API JSON

- **Decision**: rutas HTML (`GET /`, `POST /consulta`) y una API JSON (`POST /api/v1/consultas`)
  que comparten DTOs y caso de uso. `base.html` contiene el aviso de prototipo académico (FR-013).
  La marca de consulta no persistida es `persistida: false` en el JSON,
  `data-consulta-persistida="false"` en el HTML y la cabecera `X-Consulta-Persistida`. Los
  mensajes del sistema se presentan en un bloque separado de los mensajes de las reglas
  ([contracts/http.md](contracts/http.md)).

### D11. Herramientas, layout y límites de arquitectura

- **Decision**:
  - `pyproject.toml` como fuente única: dependencias, `requires-python = ">=3.12"`, ruff
    (`target-version = "py312"`, `line-length = 100`), mypy (`strict` en `domain` y
    `application`, `python_version = "3.12"`) y pytest (`pythonpath = ["src"]`, marcadores
    `integration`, `aceptacion`, `e2e`). `requirements.txt` se regenera en UTF-8 desde
    `pyproject.toml`; el actual está en UTF-16.
  - Nueva dependencia `python-multipart`, que FastAPI necesita para los formularios.
  - `tests/unit/test_arquitectura.py` recorre los imports con `ast` y falla ante cualquier
    violación de la regla de dependencia.
  - Cobertura con `--cov=domain --cov=application --cov-fail-under=80`.

### D12. Base de datos de pruebas (FR-021, SC-011)

- **Decision**: las suites `integration`, `aceptacion` y `e2e` usan **solo** `TEST_DATABASE_URL`,
  una base separada con el mismo esquema y la misma base de conocimiento, sin consultas reales.
  Un fixture de sesión en `tests/conftest.py`:
  1. Falla (no se salta) si `TEST_DATABASE_URL` no está definida.
  2. Aborta toda la sesión si `TEST_DATABASE_URL` apunta al mismo host, puerto y base que
     `DATABASE_URL` (comparación sobre la URL ya interpretada, sin imprimirla).
  3. Para e2e, levanta el servidor con `DATABASE_URL = TEST_DATABASE_URL` en el entorno del
     subproceso, de modo que la aplicación real nunca vea la base de producción.
  Las pruebas de repositorio, además, usan sesiones con rollback.
- **SC-011**: la garantía es estructural (puntos 1 a 3) y además se comprueba a mano con
  [quickstart.md](quickstart.md): conteo de `consulta` en la base real antes y después de la
  suite. Las pruebas no leen la base real ni siquiera para contar.
- **Alternatives considered**: base real con rollback, que no sirve para e2e; SQLite, que no es
  "PostgreSQL real".

### D13. Versión de Python (resuelta)

- **Decision**: la constitución v1.1.0 admite "Python 3.12 o superior (verificado con 3.13)" y
  exige fijar la versión en el despliegue. El código y las herramientas apuntan a 3.12 como mínimo
  (`requires-python`, `target-version`, `python_version` de mypy). La ejecución de referencia y el
  despliegue se fijan en **3.13**, con un `.python-version` en la raíz que coincide con el venv
  actual (3.13.13).
- **Rationale**: compatible hacia abajo con 3.12 y verificado en el entorno real.

### D14. Mensaje de salvaguarda y marca "pendiente de aprobación" (FR-020; Principio I (a)–(d))

- **Decision**:
  - El dominio define `MensajeSistema(tipo, texto, pendiente_aprobacion, sintoma)` con dos tipos:
    `COMBINACION_NO_CUBIERTA` (FR-011) y `SINTOMA_NO_CUBIERTO` (FR-020).
  - Texto propuesto para `SINTOMA_NO_CUBIERTO`, uno por cada síntoma no cubierto, en el orden de
    D3, que nombra el síntoma y el medicamento con sus nombres del vocabulario:
    > «{Síntoma}» no tiene orientación específica con {Medicamento} en la base de conocimiento
    > validada. Consulte a un médico o farmacéutico.
    Solo remite a un profesional: no menciona dosis, otros medicamentos ni recomendaciones
    (condición (a)).
  - La marca `pendiente_aprobacion` del mensaje `SINTOMA_NO_CUBIERTO` se toma de la variable de
    entorno `SALVAGUARDA_PENDIENTE_APROBACION` (valores `true`/`false`, por defecto `true`;
    cualquier otro valor hace fallar el arranque). `infrastructure/config.py` la lee y se inyecta
    en `EvaluarConsulta` como `ConfiguracionSalvaguarda`. Con `true`, el resultado muestra la
    etiqueta "Mensaje del sistema — pendiente de aprobación médica" (condición (c)). Cambiarla a
    `false` solo está permitido después de que el médico apruebe el texto, y se documenta en el
    commit que cambia la configuración de despliegue.
  - `COMBINACION_NO_CUBIERTA` tiene `pendiente_aprobacion = False`, porque lo autoriza
    directamente el Principio I.
  - La configuración solo afecta a la marca. La salvaguarda, su nivel mínimo y su texto no son
    configurables.
- **Rationale**: cumple el Principio I (a), (c) y (d) y el pedido de que la marca sea
  configurable sin tocar el código.
- **Pendiente (b)**: el Principio I (b) exige que el **texto** esté definido en la
  especificación. FR-020 describe su contenido, pero no el texto literal. Antes de implementar hay
  que copiar el texto de arriba (o el que se elija) en FR-020 (ver P6).

### D15. Nombre de los adaptadores de persistencia

- **Decision**: `PostgresReglaRepository` (`infrastructure/db/postgres_regla_repository.py`) y
  `PostgresConsultaRepository` (`infrastructure/db/postgres_consulta_repository.py`).
- **Rationale**: los adaptadores dependen de PostgreSQL a través de SQLModel, no de ninguna API
  propia de Supabase. Funcionarían igual con PostgreSQL local o con otro proveedor, como la base
  de pruebas de D12.
- **Conflicto**: los Principios IV y V de la constitución v1.1.0 nombran literalmente
  `SupabaseReglaRepository`, y la gobernanza dice que las violaciones del Principio IV no admiten
  excepción. Hace falta una enmienda de la constitución antes de implementar (ver P7 y el
  Constitution Check del plan).

## Pendientes

- **P1 — Reglas subsumidas**: ✅ resuelto en la spec (FR-009): se muestran todas.
- **P2 — Cobertura parcial de síntomas**: ✅ resuelto con la salvaguarda (FR-020, D3, D14).
- **P3 — `.env` (bloqueante para ejecutar)**: `DATABASE_URL` sigue con el prefijo duplicado; hay
  que comprobar también el esquema (`postgresql+psycopg`) y el host (`aws-0-us-east-1`). Falta
  `TEST_DATABASE_URL`. Lo debe corregir el usuario.
- **P4 — Python 3.12**: ✅ resuelto con la constitución v1.1.0 (D13).
- **P5 — Metadatos de aprobación**: `aprobada_por` y `fecha_aprobacion` siguen vacíos en las 30
  reglas. No bloquea esta funcionalidad, pero debilita la trazabilidad de la aprobación.
- **P6 — Texto literal de la salvaguarda en la spec (bloqueante para implementar)**: Principio I
  (b). Hay que añadir el texto de D14 a FR-020.
- **P7 — Nombres de los adaptadores en la constitución (bloqueante para implementar)**: hay que
  enmendar los Principios IV y V para que digan `PostgresReglaRepository` (D15). Se propone PATCH,
  porque no cambia la arquitectura, solo el nombre del adaptador.
- **P8 — Base de pruebas**: crear la base separada (proyecto o branch de Supabase, o PostgreSQL
  local) con el esquema y las 30 reglas, y definir `TEST_DATABASE_URL`. Bloquea ejecutar las
  suites `integration`, `aceptacion` y `e2e`, pero no escribirlas.
