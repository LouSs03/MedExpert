---

description: "Lista de tareas para implementar la consulta de orientación sobre automedicación"
---

# Tasks: Consulta de orientación sobre automedicación

**Input**: Design documents from `/specs/001-consulta-orientacion/`

**Prerequisites**: [plan.md](plan.md) (rev. 2), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: SÍ se incluyen. Los exige el Principio VIII de la constitución (unitarias, integración,
aceptación de las 30 reglas y e2e) y la spec define criterios verificables (SC-001 a SC-011). Dentro
de cada historia, las pruebas se escriben primero y deben fallar antes de implementar.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## ⛔ Prerrequisitos para ejecutar (no son tareas de código)

El Constitution Check del [plan](plan.md#constitution-check) no tiene violaciones: se puede
implementar. Para **ejecutar** hace falta:

1. **P3**: corregir `DATABASE_URL` en `.env` (sigue con el prefijo `DATABASE_URL=` duplicado dentro
   del valor; comprobar también el esquema `postgresql+psycopg` y el host `aws-0-us-east-1`).
   Bloquea arrancar la aplicación contra la base real.
2. **P8**: crear la base de pruebas separada y definir `TEST_DATABASE_URL` (guía en T025). Sin ella
   no se pueden **ejecutar** las suites `integration`, `aceptacion` ni `e2e`, aunque sí escribirlas.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

Proyecto único: paquetes `domain`, `application`, `infrastructure` y `api` bajo `src/` (importados
sin prefijo `src.` gracias a `pythonpath = ["src"]`) y pruebas en `tests/` (ver
[plan.md](plan.md#project-structure)).

## Convenciones que aplican a todas las tareas

- Type hints en todo el código; docstring en toda función o clase pública que diga **qué** hace
  (Principio IX). Nombres del dominio en español.
- `src/domain/` no importa nada fuera de la biblioteca estándar; `src/application/` solo importa
  `domain`; `clips` solo en `src/infrastructure/inference/`; SQLModel/SQLAlchemy/psycopg solo en
  `src/infrastructure/db/`; los routers no importan `infrastructure` (Principios IV y V).
- Ningún log, excepción ni mensaje de error muestra `DATABASE_URL`, `TEST_DATABASE_URL` ni
  credenciales (Principio X).
- Commits con Conventional Commits (Principio VI), un cambio lógico por commit.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Inicializar el proyecto, las herramientas y la estructura del Principio IV.

- [X] T001 Crear el esqueleto de carpetas con `__init__.py` vacío en cada paquete: `src/domain/`, `src/application/`, `src/application/ports/`, `src/application/casos_uso/`, `src/infrastructure/`, `src/infrastructure/db/`, `src/infrastructure/inference/`, `src/api/`, `src/api/routers/`, y las carpetas sin `__init__.py` `src/api/plantillas/`, `src/api/estaticos/`, `tests/fakes/`, `tests/unit/domain/`, `tests/unit/application/`, `tests/unit/inference/`, `tests/unit/api/`, `tests/integration/aceptacion/`, `tests/e2e/`
- [X] T002 Crear `pyproject.toml` con `[project]` (`name = "medexpert"`, `requires-python = ">=3.12"`; dependencias `fastapi==0.162.0`, `jinja2==3.1.6`, `python-multipart>=0.0.20`, `clipspy==1.0.6`, `sqlmodel==0.0.48`, `sqlalchemy==2.1.8`, `psycopg[binary]==3.3.8`, `python-dotenv==1.2.4`, `uvicorn==0.54.0`), `[project.optional-dependencies] dev` (`pytest==9.2.0`, `pytest-cov==7.1.0`, `pytest-playwright==0.10.0`, `playwright==1.64.1`, `ruff==0.17.3`, `mypy==2.4.1`, `pyyaml==6.0.3`, `httpx==0.28.1`), `[build-system]` con setuptools, `[tool.setuptools.packages.find] where = ["src"]` y `[tool.setuptools.package-data] api = ["plantillas/*.html", "estaticos/*"]`
- [X] T003 Añadir a `pyproject.toml` la sección `[tool.ruff]` (`target-version = "py312"`, `line-length = 100`, `src = ["src", "tests"]`) y `[tool.ruff.lint]` con `select = ["E", "F", "W", "I", "UP", "B", "SIM", "RUF", "D"]`, `pydocstyle.convention = "google"`, ignorando `D100`, `D104` y `D107`, y con `per-file-ignores` que desactiven `D` en `tests/**`
- [X] T004 Añadir a `pyproject.toml` la sección `[tool.mypy]` con `strict = true`, `python_version = "3.12"`, `mypy_path = "src"` y `files = ["src/domain", "src/application"]`
- [X] T005 Añadir a `pyproject.toml` `[tool.pytest.ini_options]` (`pythonpath = ["src"]`, `testpaths = ["tests"]`, `addopts = "--import-mode=importlib --strict-markers"`, `markers` = `integration`, `aceptacion`, `e2e` y `lento`, cada uno descrito) y `[tool.coverage.run] source = ["src/domain", "src/application"]`
- [X] T006 [P] Crear `.python-version` con `3.13` y completar `.env.example` con las claves sin valor `DATABASE_URL=`, `TEST_DATABASE_URL=` y `SALVAGUARDA_PENDIENTE_APROBACION=true`, con un comentario que indique el formato `postgresql+psycopg://usuario:clave@host:5432/postgres` (research D9, D13, D14)
- [X] T007 [P] Añadir a `.gitignore` las entradas `.coverage`, `htmlcov/`, `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`, `test-results/` y `*.egg-info/` (manteniendo `.venv/`, `.env`, `__pycache__/` y `*.pyc`)
- [X] T008 Instalar con `.venv/Scripts/python.exe -m pip install -e ".[dev]"` y `.venv/Scripts/python.exe -m playwright install chromium`; después regenerar `requirements.txt` en **UTF-8** (el actual está en UTF-16) solo con las dependencias de ejecución fijadas de T002, y comprobar que `ruff check .` y `mypy` terminan sin errores sobre el esqueleto vacío

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: El dominio completo, los puertos, la configuración, los logs, el acceso a la base y la
infraestructura de pruebas. Todas las historias dependen de esto.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Pruebas del dominio (escribirlas primero; deben fallar)

- [X] T009 [P] Escribir `tests/unit/domain/test_nivel.py`: severidad `ORIENTAR=1 < ADVERTIR=2 < DERIVAR=3`; etiquetas visibles "Orientar", "Advertir" y "Derivar al médico"; `EstadoRegla` con los valores `PENDIENTE`, `APROBADA` y `RECHAZADA` (data-model: Nivel, EstadoRegla)
- [X] T010 [P] Escribir `tests/unit/domain/test_vocabulario.py`: `Vocabulario.validar` devuelve `HechosConsulta` con un medicamento, síntomas ≥ 1 y condiciones ≥ 0; elimina duplicados; lanza `VocabularioInvalido` con **todos** los `valores_rechazados` ante códigos desconocidos, ante cero síntomas y ante un medicamento ausente (FR-002 a FR-005)
- [X] T011 [P] Escribir `tests/unit/domain/test_regla.py`: `Regla` rechaza `sin_condiciones = true` con `condiciones` no vacías, `sintomas` vacíos, `mensajes` vacíos y códigos que no cumplen `^[A-Z][A-Z0-9_]*$`; es inmutable (`frozen`)
- [X] T012 [P] Escribir `tests/unit/domain/test_resolucion_nivel.py` para `ResolucionPorSeveridad.resolver(hechos, disparadas)`: (1) sin reglas → `DERIVAR`, `sin_regla = True`, `sintomas_no_cubiertos` vacío aunque haya síntomas; (2) con reglas y todo cubierto → máximo de severidad; (3) con síntomas no cubiertos → `max(nivel, ADVERTIR)`, nunca rebaja `DERIVAR`; orden FR-009 (severidad ↓, `especificidad` ↓, `codigo` ↑) con empates construidos a propósito; `sintomas_no_cubiertos` ordenados por `id`; misma salida al barajar la entrada (SC-010)
- [X] T013 [P] Escribir `tests/unit/domain/test_mensajes_sistema.py`: la plantilla `COMBINACION_NO_CUBIERTA` produce exactamente "Esta combinación de medicamento, síntomas y condiciones no está cubierta por la base de conocimiento validada. Consulte con un médico." con `pendiente_aprobacion = False`; la plantilla `SINTOMA_NO_CUBIERTO` con Fiebre e Ibuprofeno produce exactamente "«Fiebre» no tiene orientación específica con Ibuprofeno en la base de conocimiento validada. Consulte a un médico o farmacéutico." y toma `pendiente_aprobacion` de `ConfiguracionSalvaguarda` (`True` y `False`)

### Dominio

- [X] T014 [P] Implementar `src/domain/nivel.py`: `Nivel(Enum)` con valores `ORIENTAR`, `ADVERTIR` y `DERIVAR`, propiedades `severidad` y `etiqueta`; `EstadoRegla(Enum)` (data-model)
- [X] T015 [P] Implementar `src/domain/errores.py`: `VocabularioInvalido(valores_rechazados: tuple[str, ...])` y `BaseConocimientoNoDisponible(motivo: str)`, cuyo motivo nunca incluye una cadena de conexión
- [X] T016 Implementar `src/domain/vocabulario.py`: objetos de valor `Medicamento`, `Sintoma` y `Condicion` (`id: int`, `codigo: str` único con `^[A-Z][A-Z0-9_]*$`, `nombre: str`), `Vocabulario` (tuplas ordenadas por `id`) con `validar(...)`, y `HechosConsulta` (`medicamento`, `sintomas: frozenset[Sintoma]` ≥ 1, `condiciones: frozenset[Condicion]` ≥ 0) (depende de T015)
- [X] T017 Implementar `src/domain/regla.py`: `Regla` con los campos `id`, `codigo`, `version`, `medicamento`, `sintomas: frozenset[str]` (≥ 1), `condiciones: frozenset[str]`, `sin_condiciones`, `especificidad`, `nivel`, `estado`, `mensajes: tuple[str, ...]` (≥ 1) y los invariantes de T011; `ReglaDisparada(regla, orden)` (depende de T014)
- [X] T018 [P] Implementar `src/domain/base_conocimiento.py`: `BaseConocimiento(vocabulario, reglas: tuple[Regla, ...])` con reglas ≥ 1 (depende de T016 y T017)
- [X] T019 [P] Implementar `src/domain/mensajes_sistema.py`: `TipoMensajeSistema`, `MensajeSistema(tipo, texto, pendiente_aprobacion, sintoma)`, `ConfiguracionSalvaguarda(pendiente_aprobacion: bool = True)` y las dos plantillas con el texto **literal** de T013 como constantes; únicas fuentes de texto no proveniente de reglas (Principios I y II) (depende de T016)
- [X] T020 Implementar `src/domain/resolucion_nivel.py`: protocolo `EstrategiaResolucionNivel`, `Resolucion(nivel, sin_regla, reglas_disparadas, sintomas_no_cubiertos)` y `ResolucionPorSeveridad` según la tabla de decisión de data-model; la salvaguarda no es desactivable (depende de T017 y T019)
- [X] T021 Implementar `src/domain/consulta.py`: `Consulta(hechos, nivel, sin_regla, reglas_disparadas)` sin campos personales y `ResultadoEvaluacion` (`nivel`, `sin_regla`, `reglas_disparadas`, `sintomas_no_cubiertos`, `mensajes_sistema`, `persistida`, `consulta_id: UUID | None`) con la propiedad derivada `salvaguarda_activada` (depende de T019 y T020)

### Puertos y fakes

- [X] T022 [P] Implementar los tres puertos `typing.Protocol` según [contracts/puertos.md](contracts/puertos.md): `src/application/ports/regla_repository.py` (`obtener_vocabulario`, `listar_reglas_aprobadas_vigentes`), `src/application/ports/consulta_repository.py` (`guardar(consulta) -> UUID`) y `src/application/ports/motor_inferencia.py` (`evaluar(hechos) -> Sequence[Regla]`)
- [X] T023 Implementar los dobles de prueba en `tests/fakes/__init__.py`, `tests/fakes/repositorios.py` (`ReglaRepositoryEnMemoria`, `ConsultaRepositoryEnMemoria` con `fallar: bool` que lanza `RuntimeError("fallo simulado postgresql://usuario:secreto@host/db")` para probar la redacción), `tests/fakes/motor.py` (`FakeMotorInferencia` que devuelve las reglas preconfiguradas) y `tests/fakes/reglas_ejemplo.py` (vocabulario completo de FR-001 y reglas de ejemplo equivalentes a R01, R02, R07, R10, R11 y R18, con sus códigos, niveles, `sin_condiciones` y especificidad de [research.md](research.md))

### Configuración, logs y base de datos

- [X] T024 [P] Escribir `tests/unit/test_arquitectura.py`, que recorre con `ast` todos los `.py` de `src/` y falla si: `domain` importa algo distinto de la biblioteca estándar (`sys.stdlib_module_names`) o de `domain`; `application` importa algo distinto de la biblioteca estándar, `domain` o `application`; se importa `clips` fuera de `infrastructure/inference`; se importa `sqlmodel`, `sqlalchemy` o `psycopg` fuera de `infrastructure/db`; `infrastructure` importa `api`; un módulo de `api/routers/` importa `infrastructure` (Principios IV y V)
- [X] T025 [P] Escribir `docs/base-de-pruebas.md`: cómo crear la base separada (proyecto o branch de Supabase, o PostgreSQL local) con `pg_dump --schema-only` de la base real y `pg_dump --data-only` de **solo** `medicamento`, `sintoma`, `condicion`, `regla`, `regla_sintoma`, `regla_condicion` y `regla_mensaje`; verificación de 30 reglas y RLS activo; y cómo definir `TEST_DATABASE_URL` (research D12, P8)
- [X] T026 [P] Escribir `tests/unit/test_config.py`: `cargar_configuracion` acepta `postgresql+psycopg://…`, normaliza `postgresql://…` a `postgresql+psycopg://…` y rechaza cualquier otro esquema (incluido un valor que empieza por `DATABASE_URL=`) con un error cuyo texto **no** contiene la URL; `SALVAGUARDA_PENDIENTE_APROBACION` vale `True` por defecto, acepta `true` y `false` sin distinguir mayúsculas y rechaza cualquier otro valor (`"quizas"`)
- [X] T027 Implementar `src/infrastructure/config.py`: `Configuracion(database_url, salvaguarda: ConfiguracionSalvaguarda)` y `cargar_configuracion(entorno: Mapping[str, str] = os.environ)`, que carga `.env` con `python-dotenv` solo si existe y sin sobrescribir variables ya definidas; `ConfiguracionInvalida` sin secretos (research D9, D14) (depende de T019 y T026)
- [X] T028 [P] Escribir `tests/unit/test_logging.py`: un registro de log cuyo mensaje o excepción contiene `postgresql+psycopg://u:clave@host:5432/db`, o el valor exacto configurado de `DATABASE_URL` o `TEST_DATABASE_URL`, sale con `<redacted>` y sin `clave` (research D8)
- [X] T029 Implementar `src/infrastructure/logging.py`: `FiltroSecretos(logging.Filter)`, que redacta URLs `postgres*://\S+` y los valores de los secretos configurados en `msg`, `args` y el texto de la excepción, y `configurar_logging(config)`, que lo instala en el logger raíz (depende de T027 y T028)
- [X] T030 Implementar `src/infrastructure/db/engine.py`: `crear_engine(database_url)` con `pool_pre_ping=True` y `get_session(engine)` como generador de `sqlmodel.Session`; nunca registra la URL
- [X] T031 Implementar `src/infrastructure/db/modelos.py`: modelos SQLModel `table=True` que reflejan **exactamente** el esquema existente, sin `create_all`: `medicamento`, `sintoma` y `condicion` (`id smallint PK`, `codigo text UNIQUE NOT NULL`, `nombre text NOT NULL`, más `descripcion text NULL` solo en `condicion`); `regla` (`id int PK`, `codigo text`, `version smallint`, `medicamento_id smallint FK`, `nivel text`, `sin_condiciones bool`, `especificidad smallint`, `estado text`, `aprobada_por text NULL`, `fecha_aprobacion date NULL`, `fuente text NULL`, `creado_en timestamptz`); `regla_sintoma` y `regla_condicion` (PK compuesta); `regla_mensaje` (`id int PK`, `regla_id int FK`, `orden smallint`, `texto text`); `consulta` (`id uuid PK` con valor por defecto en el servidor, `creado_en timestamptz` por defecto en el servidor, `medicamento_id smallint FK`, `nivel_resultado text NULL`, `sin_regla bool`); `consulta_sintoma`, `consulta_condicion` y `consulta_regla_disparada` (`consulta_id uuid`, `regla_id int`, `orden smallint`)
- [X] T032 Implementar `tests/conftest.py` (FR-021): al importarse, carga `.env` con `python-dotenv` (`load_dotenv(override=False)`) **antes** de cualquier guarda; fixture de sesión `url_base_pruebas` que **falla** si `DATABASE_URL` o `TEST_DATABASE_URL` no están definidas (sin `DATABASE_URL` la comparación no protegería nada) y llama a `pytest.exit` si coincide en host, puerto y nombre de base con `DATABASE_URL` (comparando con `sqlalchemy.engine.make_url`, sin imprimir las URLs); fixtures `engine_pruebas` y `sesion_rollback` (conexión con transacción externa y rollback al terminar). Las fixtures solo se activan en pruebas que las usan, así que las unitarias no requieren las variables

**Checkpoint**: dominio y fundamentos listos; `pytest tests/unit` en verde con T009–T013, T024, T026 y T028.

---

## Phase 3: User Story 1 - Obtener orientación para una combinación cubierta (Priority: P1) 🎯 MVP

**Goal**: la persona envía medicamento, síntomas y condiciones y ve el nivel, los mensajes
aprobados ordenados (FR-009), los códigos aplicados y, si corresponde, la salvaguarda de cobertura
(FR-020), con el aviso de prototipo en todas las pantallas. La base de conocimiento se carga desde
PostgreSQL al arrancar (FR-018 si falla) y la consulta se guarda (camino feliz).

**Independent Test**: con la base de pruebas, el escenario 1 de [quickstart.md](quickstart.md)
(paracetamol + dolor de cabeza) muestra Orientar con R01, y el escenario 6 (ibuprofeno + dolor de
cabeza + fiebre) muestra Advertir con R18 y el mensaje de salvaguarda para Fiebre con el distintivo
"Pendiente de aprobación médica".

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T033 [P] [US1] Escribir `tests/unit/inference/test_traductor_reglas.py` según [contracts/traduccion-clips.md](contracts/traduccion-clips.md): el texto generado para R10-v1 y R07-v1 coincide con el contrato; síntomas y condiciones en orden alfabético; `(not (condicion))` solo si `sin_condiciones`; `ValueError` ante el código `"FIEBRE) (assert"` o un `regla-id` no entero
- [X] T034 [P] [US1] Escribir `tests/unit/inference/test_clips_motor_inferencia.py`: con las reglas de `tests/fakes/reglas_ejemplo.py` en una `FabricaEntornoClips` real, se cumple FR-006 (todos los síntomas y condiciones presentes; los hechos de más no bloquean; una regla "sin condiciones" no se dispara con cualquier condición marcada); dos entornos creados por la fábrica no comparten hechos; 20 hilos simultáneos con hechos distintos obtienen lo mismo que en secuencia (FR-016, SC-008)
- [X] T035 [P] [US1] Escribir `tests/unit/application/test_cargar_base_conocimiento.py`: carga correcta; 0 reglas → `BaseConocimientoNoDisponible`; excepción del repositorio → `BaseConocimientoNoDisponible` con un motivo sin URL; código de regla duplicado o código no presente en el vocabulario → `BaseConocimientoNoDisponible`; `especificidad ≠ |síntomas| + |condiciones|` → `logging.WARNING` sin fallar
- [X] T036 [P] [US1] Escribir `tests/unit/application/test_evaluar_consulta.py` con fakes: combinación cubierta → nivel, reglas en orden FR-009 y `persistida = True` con `consulta_id`; salvaguarda: Orientar → Advertir con un `SINTOMA_NO_CUBIERTO` por síntoma no cubierto y `pendiente_aprobacion` igual a `ConfiguracionSalvaguarda` (probar `True` y `False`); `Consulta` entregada a `ConsultaRepositoryEnMemoria` con el nivel ya elevado; `VocabularioInvalido` se propaga sin llamar al motor ni al repositorio
- [X] T037 [P] [US1] Escribir `tests/unit/api/test_rutas_consulta.py` con `TestClient` y `app.dependency_overrides`: `GET /` muestra 2 medicamentos, 6 síntomas y 7 condiciones y el aviso "Prototipo académico: no reemplaza la consulta médica o farmacéutica."; `POST /consulta` muestra el nivel, los mensajes agrupados por regla en orden, `#explicacion` con "Reglas aplicadas: …" y, con salvaguarda, `<aside id="mensajes-sistema">`, el distintivo "Pendiente de aprobación médica" y "Salvaguarda del sistema (pendiente de aprobación médica): síntomas sin regla aplicable: …" (el paréntesis solo con `pendiente_aprobacion = true`); `POST /api/v1/consultas` devuelve el `ResultadoDTO` de [contracts/http.md](contracts/http.md); 422 con `valores_rechazados`; 503 en `/`, `/consulta`, `/api/v1/consultas` y `/salud` cuando la base no está disponible; el aviso aparece en todas las respuestas HTML (SC-007)
- [X] T038 [P] [US1] Escribir `tests/integration/test_postgres_regla_repository.py` (marcador `integration`, fixture `engine_pruebas`): el vocabulario cargado coincide exactamente con FR-001 (`PARACETAMOL`, `IBUPROFENO`; los 6 síntomas y las 7 condiciones de research); 30 reglas, todas en la versión más reciente en estado `aprobada`; los mensajes respetan `regla_mensaje.orden`; una versión 2 `pendiente` insertada dentro de `sesion_rollback` no reemplaza a la versión 1 `aprobada`
- [X] T039 [P] [US1] Escribir `tests/integration/test_carga_base_conocimiento.py` (marcador `integration`): `CargarBaseConocimiento` con `PostgresReglaRepository` real produce 30 reglas, y las 30 se traducen y se construyen en un entorno de `FabricaEntornoClips` sin error
- [X] T040 [US1] Crear `tests/integration/aceptacion/casos_reglas.yaml`, la biblioteca indexada (Principio VIII), con un caso por regla: `codigo`, `medicamento`, `sintomas`, `condiciones`, `regla_id` (el `regla-id` de su `defrule` en el [Apéndice B](#apéndice-b-defrule-esperado-por-regla)), `nivel_esperado`, `reglas_esperadas` en orden y `salvaguarda: false`. Usar **exactamente** los valores de la tabla del [Apéndice A](#apéndice-a-casos-de-aceptación-r01r30), calculados el 2026-11-04 sobre las reglas reales Añadir además `tests/integration/aceptacion/test_ids_reglas.py` (marcador `integration`, fixture `engine_pruebas`), que carga las reglas con `PostgresReglaRepository` y comprueba que, para cada código, el `id` de la regla cargada es igual a su `regla_id` del YAML; si falla, el Apéndice B y el YAML dejaron de reflejar la base y deben regenerarse
- [X] T041 [US1] Escribir `tests/integration/aceptacion/test_aceptacion_reglas.py` (marcador `aceptacion`), parametrizado con `casos_reglas.yaml` (id = código de la regla): ejecuta `EvaluarConsulta` con `PostgresReglaRepository`, `ClipsMotorInferencia` y `ResolucionPorSeveridad` reales y `ConsultaRepositoryEnMemoria`; verifica el nivel, la lista de códigos en orden, que los mensajes de la regla del caso aparecen completos y en orden (texto de `regla_mensaje` de su versión) y que `salvaguarda_activada` es `False` (SC-001)
- [X] T042 [US1] Escribir `tests/unit/inference/test_traduccion_30_reglas.py` y su fixture `tests/unit/inference/defrules_esperados.clp` (con el texto **exacto** del [Apéndice B](#apéndice-b-defrule-esperado-por-regla), un constructo por regla separado por una línea en blanco): prueba parametrizada (id = código de la regla) que, para cada una de las 30 reglas de `tests/integration/aceptacion/casos_reglas.yaml` (T040), construye una `Regla` del dominio (`id` = número del código, `version = 1`, `sin_condiciones` = sin condiciones, `especificidad` = nº de síntomas + nº de condiciones, `nivel` = `nivel_esperado`, un mensaje cualquiera), comprueba que `TraductorReglasClips.traducir` produce exactamente su `defrule` del Apéndice B y que, en un entorno nuevo con solo las plantillas y esa regla, afirmar sus hechos exactos dispara esa regla y ninguna otra (Principio VIII, unitarias; no usa la base)

### Implementation for User Story 1

- [X] T043 [P] [US1] Implementar `src/infrastructure/inference/traductor_reglas.py`: `TraductorReglasClips` con `plantillas() -> tuple[str, ...]` (los cuatro `deftemplate` del contrato) y `traducir(regla) -> str` según las reglas 1 a 6 del contrato
- [X] T044 [US1] Implementar `src/infrastructure/inference/fabrica_entorno.py`: `FabricaEntornoClips(reglas)` que precalcula la tupla inmutable de constructos y `crear() -> clips.Environment`, que construye un entorno nuevo llamando a `build()` **una vez por constructo** (depende de T043)
- [X] T045 [US1] Implementar `src/infrastructure/inference/clips_motor_inferencia.py`: `ClipsMotorInferencia(fabrica)` implementa `MotorInferencia.evaluar`: afirma los hechos, ejecuta `run(1000)`, recoge los `disparo` y los mapea a `Regla` por `id`; el entorno se descarta tras cada consulta (depende de T044)
- [X] T046 [P] [US1] Implementar `src/infrastructure/db/postgres_regla_repository.py`: `PostgresReglaRepository(engine)` con `obtener_vocabulario()` (catálogos ordenados por `id`) y `listar_reglas_aprobadas_vigentes()` (`SELECT DISTINCT ON (codigo) … WHERE estado = 'aprobada' ORDER BY codigo, version DESC` y después síntomas, condiciones y mensajes de esas reglas en tres consultas en bloque, sin N+1), devolviendo entidades del dominio
- [X] T047 [P] [US1] Implementar `src/infrastructure/db/postgres_consulta_repository.py`: `PostgresConsultaRepository(session).guardar(consulta)` inserta en **una sola transacción** `consulta` (`medicamento_id`, `nivel_resultado` = valor del enum, `sin_regla`) y recupera el `id` generado, y luego `consulta_sintoma`, `consulta_condicion` y `consulta_regla_disparada` (`regla_id` = id de la versión, `orden` de `ReglaDisparada`); devuelve el `UUID`
- [X] T048 [US1] Implementar `src/application/casos_uso/cargar_base_conocimiento.py`: `CargarBaseConocimiento(repositorio).ejecutar()` según T035 y los invariantes de data-model
- [X] T049 [US1] Implementar `src/application/casos_uso/evaluar_consulta.py`: `EvaluarConsulta(vocabulario, motor, estrategia, consultas, salvaguarda).ejecutar(medicamento, sintomas, condiciones)` con los pasos 1 a 6 de [contracts/puertos.md](contracts/puertos.md); en esta fase el paso 4 solo genera mensajes `SINTOMA_NO_CUBIERTO` (US2 añade `COMBINACION_NO_CUBIERTA`) y el paso 5 deja propagar la excepción del repositorio (US3 añade FR-019)
- [X] T050 [P] [US1] Implementar `src/api/esquemas.py`: `ConsultaEntradaDTO` (`sintomas` con `min_length=1`, eliminación de duplicados, `condiciones` por defecto `[]`), `ReglaAplicadaDTO`, `SintomaDTO`, `MensajeSistemaDTO`, `ResultadoDTO` y `ErrorValidacionDTO` con los campos y reglas de [contracts/http.md](contracts/http.md), más una función `a_resultado_dto(resultado, vocabulario)` que traduce entidades a DTO
- [X] T051 [US1] Implementar `src/api/dependencias.py`: proveedores para `Depends` que leen de `request.app.state` (`base`, `motor`, `estrategia`, `salvaguarda`, `engine`) y `get_evaluar_consulta(request, session=Depends(get_session))`, que arma `EvaluarConsulta` con `PostgresConsultaRepository(session)`; si la base no está disponible, lanza la excepción que el router traduce a 503
- [X] T052 [US1] Implementar `src/api/main.py`: `create_app()` con `lifespan` que ejecuta `cargar_configuracion`, `configurar_logging`, `crear_engine`, `CargarBaseConocimiento(PostgresReglaRepository(engine))`, `FabricaEntornoClips`, `ClipsMotorInferencia`, `ResolucionPorSeveridad()` y guarda todo una sola vez en `app.state`; ante `BaseConocimientoNoDisponible` guarda `app.state.base = None` y sigue arrancando (FR-018); monta `estaticos/` y configura `Jinja2Templates` sobre `plantillas/`; **no** expone `app` a nivel de módulo: se arranca con `uvicorn api.main:create_app --factory --app-dir src`
- [X] T053 [US1] Implementar `src/api/routers/consulta.py`: `GET /` (formulario desde el vocabulario), `POST /consulta` (formulario urlencoded → `resultado.html`; 422 → `formulario.html` con los errores y los valores marcados) y `POST /api/v1/consultas` (JSON); solo invocan el caso de uso recibido por `Depends` (sin lógica de negocio); 503 con `no_disponible.html` o JSON `{"detalle": …}`
- [X] T054 [P] [US1] Implementar `src/api/routers/salud.py`: `GET /salud` → 200 `{"base_conocimiento": "disponible", "reglas": N}` o 503 `{"base_conocimiento": "no_disponible"}`
- [X] T055 [P] [US1] Crear `src/api/plantillas/base.html` (con el aviso "Prototipo académico: no reemplaza la consulta médica o farmacéutica." visible en todas las páginas, `lang="es"`), `src/api/plantillas/formulario.html` (radio para el medicamento, checkboxes para síntomas y condiciones, con los nombres del vocabulario y la lista de errores de validación) y `src/api/plantillas/no_disponible.html`
- [X] T056 [US1] Crear `src/api/plantillas/resultado.html` según la sección "Presentación HTML del resultado" de [contracts/http.md](contracts/http.md): `<section id="resultado" data-nivel=… data-salvaguarda=…>`, nivel destacado, mensajes agrupados por regla en el orden del DTO, `<aside id="mensajes-sistema">` **después** de los mensajes de las reglas con el encabezado "Mensaje del sistema (no proviene de una regla validada)" y el distintivo "Pendiente de aprobación médica" cuando `pendiente_aprobacion`, y `#explicacion` con los códigos y los síntomas no cubiertos
- [X] T057 [P] [US1] Crear `src/api/estaticos/estilos.css`: estilos legibles y accesibles (contraste AA, colores distintos por nivel que no dependan solo del color, distintivo de "pendiente" visible)
- [X] T058 [US1] Escribir `tests/e2e/conftest.py` y `tests/e2e/test_flujo_consulta.py` (marcador `e2e`): el fixture levanta `uvicorn api.main:create_app --factory --app-dir src` en un subproceso con `DATABASE_URL = TEST_DATABASE_URL` y `SALVAGUARDA_PENDIENTE_APROBACION=true`; con Playwright, los escenarios 1 (Orientar, R01), 2 (Advertir, R10), 3 (Derivar al médico, R11) y 6 (Advertir, R18, salvaguarda para Fiebre con distintivo) de quickstart: rellenar el formulario, enviar, comprobar el nivel, los mensajes, `#explicacion` y el aviso

**Checkpoint**: US1 funciona por sí sola: T033–T041 y T058 en verde. No abrir PR a `main` todavía:
el Principio III exige el manejo de FR-019 (US3).

---

## Phase 4: User Story 2 - Respuesta segura ante una combinación no cubierta (Priority: P2)

**Goal**: si no se dispara ninguna regla, el resultado es Derivar al médico con el mensaje de
combinación no cubierta, sin reglas aplicadas y sin mensajes de salvaguarda (FR-011, FR-012).

**Independent Test**: escenario 8 de quickstart (ibuprofeno + fiebre) y escenario 9 (paracetamol +
dolor de cabeza + uso de aspirina): Derivar al médico, solo el mensaje de combinación no cubierta y
"Ninguna regla aplicada".

### Tests for User Story 2 ⚠️

- [X] T059 [P] [US2] Escribir `tests/unit/application/test_evaluar_consulta_no_cubierta.py`: con `FakeMotorInferencia` vacío → `DERIVAR`, `sin_regla = True`, exactamente un `MensajeSistema` `COMBINACION_NO_CUBIERTA` con `pendiente_aprobacion = False`, ningún `SINTOMA_NO_CUBIERTO` (aunque haya síntomas), `reglas_disparadas` y `sintomas_no_cubiertos` vacíos
- [X] T060 [P] [US2] Escribir `tests/unit/api/test_rutas_no_cubierta.py`: el HTML muestra "Derivar al médico", el texto exacto de `COMBINACION_NO_CUBIERTA` sin el distintivo de pendiente y "Ninguna regla aplicada"; el JSON cumple el caso `sin_regla = true` de la tabla "Casos de `mensajes_sistema`" de [contracts/http.md](contracts/http.md)
- [X] T061 [P] [US2] Añadir a `tests/integration/aceptacion/casos_reglas.yaml` una sección `no_cubiertos` con IBUPROFENO + FIEBRE sin condiciones y PARACETAMOL + DOLOR_CABEZA + USO_ASPIRINA (`nivel_esperado: DERIVAR`, `sin_regla: true`), y en `tests/integration/aceptacion/test_aceptacion_reglas.py` un test parametrizado sobre esa sección que verifica el nivel, `sin_regla` y el único mensaje del sistema (SC-002)

### Implementation for User Story 2

- [X] T062 [US2] Completar el paso 4 de `src/application/casos_uso/evaluar_consulta.py`: si `sin_regla`, `mensajes_sistema` es exactamente `(COMBINACION_NO_CUBIERTA,)`; nunca se mezclan los dos tipos
- [X] T063 [US2] Completar `src/api/plantillas/resultado.html` para el caso `sin_regla`: bloque de mensaje del sistema sin distintivo y `#explicacion` con "Ninguna regla aplicada"
- [X] T064 [US2] Añadir a `tests/e2e/test_flujo_consulta.py` los escenarios 8 y 9 de quickstart

**Checkpoint**: US1 y US2 funcionan; T059–T061 y T064 en verde.

---

## Phase 5: User Story 3 - Registro trazable de cada consulta (Priority: P3)

**Goal**: toda consulta respondida queda registrada sin datos personales y con el nivel ya
elevado, y un fallo de registro no impide mostrar el resultado: se marca internamente y se registra
en el log sin secretos (FR-014, FR-015, FR-019).

**Independent Test**: tras el escenario 6, la base de pruebas tiene una `consulta` con
`nivel_resultado = 'ADVERTIR'`, `sin_regla = false` y filas hijas coherentes; si el repositorio
falla, la respuesta trae el resultado completo con `persistida: false`, `X-Consulta-Persistida:
false` y un `ERROR` en el log sin credenciales.

### Tests for User Story 3 ⚠️

- [X] T065 [P] [US3] Escribir `tests/unit/application/test_evaluar_consulta_persistencia.py`: con `ConsultaRepositoryEnMemoria(fallar=True)` el resultado conserva nivel, reglas y mensajes, con `persistida = False` y `consulta_id = None`; `caplog` contiene un registro `ERROR` con el tipo de la excepción y **sin** `secreto` ni `postgresql://` (filtro de T029 instalado)
- [X] T066 [P] [US3] Escribir `tests/unit/api/test_marca_persistencia.py`: cabecera `X-Consulta-Persistida: true|false` en `POST /consulta` y `POST /api/v1/consultas`; atributo `data-consulta-persistida` en `#resultado`; con `false` no aparece ningún texto visible adicional y el resto de la respuesta es idéntico
- [X] T067 [P] [US3] Escribir `tests/integration/test_postgres_consulta_repository.py` (marcador `integration`, `sesion_rollback`): tras `guardar`, las filas de `consulta`, `consulta_sintoma`, `consulta_condicion` y `consulta_regla_disparada` coinciden con la `Consulta` (incluido `orden` y, para el escenario 6, `nivel_resultado = 'ADVERTIR'`); atomicidad: un `regla_id` inexistente hace fallar el guardado y no deja ninguna fila de `consulta`
- [X] T068 [P] [US3] Escribir `tests/integration/test_sin_datos_personales.py` (marcador `integration`): las columnas de `consulta`, `consulta_sintoma`, `consulta_condicion` y `consulta_regla_disparada` en `information_schema.columns` son exactamente {`id`, `creado_en`, `medicamento_id`, `nivel_resultado`, `sin_regla`, `consulta_id`, `sintoma_id`, `condicion_id`, `regla_id`, `orden`} (FR-015, SC-006)

### Implementation for User Story 3

- [X] T069 [US3] Completar el paso 5 de `src/application/casos_uso/evaluar_consulta.py` (FR-019): capturar cualquier excepción de `consultas.guardar`, registrar `logger.error("No se pudo persistir la consulta", exc_info=True, extra={"tipo_error": type(e).__name__})`, de modo que el mensaje y la traza de la excepción queden en el log saneados por `FiltroSecretos` (T029; verificado en T065), y devolver el resultado completo con `persistida = False` y `consulta_id = None`
- [X] T070 [US3] Añadir la marca interna en `src/api/routers/consulta.py` (cabecera `X-Consulta-Persistida`) y en `src/api/plantillas/resultado.html` (atributo `data-consulta-persistida`), sin texto visible

**Checkpoint**: las tres historias funcionan; la suite completa en verde.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Verificaciones transversales, documentación y validación final.

- [ ] T071 [P] Escribir `tests/integration/test_combinaciones.py` (marcadores `integration` y `lento`): recorre las 16.128 combinaciones (2 medicamentos × 63 subconjuntos no vacíos de síntomas × 128 subconjuntos de condiciones) y compara `ClipsMotorInferencia` + `ResolucionPorSeveridad` con un oráculo escrito en la prueba según FR-006, FR-009 y FR-020 (nivel, `sin_regla`, códigos en orden, síntomas no cubiertos); además verifica que ninguna combinación con reglas disparadas y síntomas no cubiertos termina en Orientar (SC-009) y que todo mensaje del resultado es, o bien un mensaje de una regla presente en `reglas_disparadas`, o bien uno de los dos mensajes del sistema (`COMBINACION_NO_CUBIERTA`, `SINTOMA_NO_CUBIERTO`) (SC-003, FR-012)
- [ ] T072 [P] Escribir `tests/integration/test_concurrencia.py` (marcador `integration`): 20 consultas distintas lanzadas a la vez con `concurrent.futures.ThreadPoolExecutor` contra `EvaluarConsulta` real dan exactamente el mismo resultado que en secuencia (SC-008); y repetir 10 veces la misma consulta da siempre el mismo orden de reglas y mensajes (SC-010)
- [ ] T073 [P] Escribir `tests/integration/test_rls.py` (marcador `integration`, fixture `engine_pruebas`): consulta `pg_class` y `pg_namespace` y verifica `relrowsecurity = true` en **todas** las tablas (`relkind = 'r'`) del esquema `public` (hoy 11) (Principio X). Se ejecuta sobre la base de pruebas, que se crea con `pg_dump --schema-only` de la real (T025) y por tanto conserva su RLS; FR-021 impide ejecutarla contra la base real
- [ ] T074 [P] Añadir a `tests/e2e/test_flujo_consulta.py` una medición: el tiempo desde el envío del formulario hasta que aparece `#resultado` es menor de 2 s en el escenario 6 (SC-005)
- [ ] T075 [P] Actualizar `README.md`: qué es el prototipo, aviso académico, requisitos (Python ≥ 3.12, referencia 3.13), variables de entorno (`DATABASE_URL`, `TEST_DATABASE_URL`, `SALVAGUARDA_PENDIENTE_APROBACION` y el procedimiento para ponerla en `false` solo tras la aprobación del médico, documentada en el commit), y cómo ejecutar la aplicación (`uvicorn api.main:create_app --factory --app-dir src`) y las pruebas
- [ ] T076 [P] Actualizar `specs/001-consulta-orientacion/quickstart.md`: la línea de la suite completa pasa a `pytest --cov=domain --cov=application --cov-report=term-missing --cov-fail-under=80`
- [ ] T077 Ejecutar `ruff format .`, `ruff check .`, `mypy` y `pytest --cov=domain --cov=application --cov-fail-under=80` con la base de pruebas, y corregir hasta que todo pase (cobertura ≥ 80 % en `domain` y `application`, Principio VIII)
- [ ] T078 Ejecutar la validación manual de [quickstart.md](quickstart.md): escenarios 1 a 9, casos negativos y la comprobación de SC-011 (conteo de `consulta` en la base real antes y después de la suite completa: debe ser idéntico); y una prueba de usabilidad con 2 o 3 personas sin entrenamiento previo, que realizan los escenarios 1, 6 y 8, cronometrando cada consulta desde abrir el formulario hasta ver el resultado, con los tiempos anotados en `docs/usabilidad-sc004.md` (objetivo SC-004: menos de 1 minuto por consulta)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Prerrequisitos ⛔ (P3, P8)**: no bloquean escribir el código; P3 bloquea ejecutar la
  aplicación y P8 bloquea ejecutar las suites `integration`, `aceptacion` y `e2e`.
- **Setup (Phase 1)**: sin dependencias. T002 antes de T003–T005 (mismo archivo); T008 al final.
- **Foundational (Phase 2)**: depende de Setup. Bloquea todas las historias.
- **US1 (Phase 3)**: depende de Foundational.
- **US2 (Phase 4)**: depende de Foundational y de las rutas y plantillas de US1 (T053, T056), porque
  reutiliza el mismo flujo de pantalla.
- **US3 (Phase 5)**: depende de Foundational y de `EvaluarConsulta` y las rutas de US1 (T049, T053).
  Puede hacerse en paralelo con US2, salvo por los archivos compartidos (`evaluar_consulta.py`,
  `resultado.html`, `consulta.py`), que se tocan en secuencia.
- **Polish (Phase 6)**: depende de las tres historias.

### Dependencias clave dentro de las fases

- Dominio: T015 → T016; T014 → T017; (T016, T017) → T018; T016 → T019; (T017, T019) → T020;
  (T019, T020) → T021. Configuración: (T019, T026) → T027 → T029.
- US1: T043 → T044 → T045; (T046, T048) dependen de T022 y del dominio; T049 depende de T020, T021 y
  T022; T050 → T051 → T052 → T053; T055 → T056; T040 → (T041, T042).
- `src/application/casos_uso/evaluar_consulta.py`: T049 (US1) → T062 (US2) → T069 (US3).
- `src/api/plantillas/resultado.html`: T056 → T063 → T070.
- `tests/e2e/test_flujo_consulta.py`: T058 → T064 → T074.

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Dominio → casos de uso → adaptadores → API → plantillas → e2e
- Story complete before moving to next priority

### Parallel Opportunities

- Setup: T006 y T007 en paralelo con T003–T005 (estas tres editan `pyproject.toml` y van en
  secuencia tras T002).
- Foundational: las pruebas T009–T013, T024, T026 y T028 a la vez; T014, T015 y T022 a la vez;
  T025 en cualquier momento.
- US1: las pruebas T033–T039 a la vez; T043, T046, T047, T050, T054, T055 y T057 a la vez.
- US2 y US3: sus pruebas (T059–T061, T065–T068) a la vez.
- Polish: T071–T076 a la vez.

---

## Parallel Example: User Story 1

```bash
# Pruebas de US1 en paralelo (escribirlas primero):
Task: "Escribir tests/unit/inference/test_traductor_reglas.py"
Task: "Escribir tests/unit/inference/test_clips_motor_inferencia.py"
Task: "Escribir tests/unit/application/test_cargar_base_conocimiento.py"
Task: "Escribir tests/unit/application/test_evaluar_consulta.py"
Task: "Escribir tests/unit/api/test_rutas_consulta.py"
Task: "Escribir tests/integration/test_postgres_regla_repository.py"

# Adaptadores y piezas de API independientes en paralelo:
Task: "Implementar src/infrastructure/inference/traductor_reglas.py"
Task: "Implementar src/infrastructure/db/postgres_regla_repository.py"
Task: "Implementar src/infrastructure/db/postgres_consulta_repository.py"
Task: "Implementar src/api/esquemas.py"
Task: "Crear src/api/plantillas/base.html, formulario.html y no_disponible.html"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Resolver los prerrequisitos ⛔ (P3 y P8) antes de ejecutar pruebas de integración y e2e.
2. Complete Phase 1: Setup.
3. Complete Phase 2: Foundational (CRITICAL - blocks all stories).
4. Complete Phase 3: User Story 1.
5. **STOP and VALIDATE**: escenarios 1, 2, 3 y 6 de quickstart y la suite de aceptación R01–R30.
6. Demo local. **No** fusionar a `main` todavía: el Principio III (FR-019) llega con US3.

### Incremental Delivery

1. Setup + Foundational → dominio y fundamentos probados.
2. US1 → MVP demostrable (orientación, orden, salvaguarda).
3. US2 → respuesta segura para combinaciones no cubiertas.
4. US3 → trazabilidad completa y fallo de registro controlado.
5. Polish → verificación exhaustiva (16.128 combinaciones), concurrencia, rendimiento y
   documentación; luego un único PR de `001-consulta-orientacion` a `main` con la suite completa
   en verde (Principio VII).

---

## Apéndice A: casos de aceptación R01–R30

Valores esperados para `tests/integration/aceptacion/casos_reglas.yaml` (T040), calculados el
2026-11-04 con un oráculo independiente sobre las reglas reales (FR-006, FR-009, FR-020). En los 30
casos la salvaguarda **no** se activa. Si en el futuro cambia una regla, este apéndice y el YAML se
actualizan en el mismo commit, citando el código de la regla (Principio VI).

| Código | Medicamento | Síntomas | Condiciones | Nivel esperado | Reglas esperadas (en orden) |
|--------|-------------|----------|-------------|----------------|-----------------------------|
| R01 | PARACETAMOL | DOLOR_CABEZA | — | ORIENTAR | R01 |
| R02 | PARACETAMOL | FIEBRE | — | ORIENTAR | R02 |
| R03 | PARACETAMOL | DOLOR_MUSCULAR | — | ORIENTAR | R03 |
| R04 | PARACETAMOL | DOLOR_DENTAL | — | ORIENTAR | R04 |
| R05 | PARACETAMOL | DOLOR_ABDOMINAL | — | ADVERTIR | R05 |
| R06 | PARACETAMOL | FIEBRE, MOLESTIAS_RESPIRATORIAS | — | ORIENTAR | R06, R02 |
| R07 | PARACETAMOL | DOLOR_CABEZA, FIEBRE | — | ORIENTAR | R07, R01, R02 |
| R08 | PARACETAMOL | FIEBRE, DOLOR_MUSCULAR | — | ORIENTAR | R08, R02, R03 |
| R09 | PARACETAMOL | DOLOR_CABEZA | HIPERTENSION | ORIENTAR | R09 |
| R10 | PARACETAMOL | DOLOR_CABEZA | EMBARAZO | ADVERTIR | R10 |
| R11 | PARACETAMOL | FIEBRE | EMBARAZO | DERIVAR | R11 |
| R12 | PARACETAMOL | DOLOR_MUSCULAR | ADULTO_MAYOR | ADVERTIR | R12 |
| R13 | PARACETAMOL | FIEBRE, DOLOR_ABDOMINAL | — | DERIVAR | R13, R05, R02 |
| R14 | PARACETAMOL | FIEBRE, MOLESTIAS_RESPIRATORIAS | USO_ANTIGRIPAL | ADVERTIR | R14 |
| R15 | PARACETAMOL | DOLOR_MUSCULAR | ADULTO_MAYOR, USO_ASPIRINA | ADVERTIR | R15, R12 |
| R16 | IBUPROFENO | DOLOR_DENTAL | — | ORIENTAR | R16 |
| R17 | IBUPROFENO | DOLOR_MUSCULAR | — | ORIENTAR | R17 |
| R18 | IBUPROFENO | DOLOR_CABEZA | — | ORIENTAR | R18 |
| R19 | IBUPROFENO | DOLOR_ABDOMINAL | — | DERIVAR | R19 |
| R20 | IBUPROFENO | FIEBRE, DOLOR_MUSCULAR | — | ORIENTAR | R20, R17 |
| R21 | IBUPROFENO | FIEBRE, MOLESTIAS_RESPIRATORIAS | — | ORIENTAR | R21 |
| R22 | IBUPROFENO | DOLOR_CABEZA | EMBARAZO | DERIVAR | R22 |
| R23 | IBUPROFENO | DOLOR_MUSCULAR | HIPERTENSION | ADVERTIR | R23 |
| R24 | IBUPROFENO | DOLOR_DENTAL | DIABETES | ADVERTIR | R24 |
| R25 | IBUPROFENO | DOLOR_MUSCULAR | ADULTO_MAYOR | ADVERTIR | R25 |
| R26 | IBUPROFENO | DOLOR_CABEZA | USO_ANTIGRIPAL | ADVERTIR | R26 |
| R27 | IBUPROFENO | FIEBRE, MOLESTIAS_RESPIRATORIAS | USO_ASPIRINA | ADVERTIR | R27 |
| R28 | IBUPROFENO | DOLOR_MUSCULAR | HIPERTENSION, ADULTO_MAYOR | DERIVAR | R28, R23, R25 |
| R29 | IBUPROFENO | DOLOR_MUSCULAR | DIABETES, HIPERTENSION | DERIVAR | R29, R23 |
| R30 | IBUPROFENO | DOLOR_DENTAL | ADULTO_MAYOR, OTRO_TRATAMIENTO | DERIVAR | R30 |

---

## Apéndice B: `defrule` esperado por regla

Texto exacto para `tests/unit/inference/defrules_esperados.clp` (T042). Se generó el 2026-11-04
con el formato de [contracts/traduccion-clips.md](contracts/traduccion-clips.md) sobre las reglas
reales, y se verificó que cada constructo se construye solo en CLIPS y se dispara con sus hechos
exactos. Si cambia una regla, este apéndice, el Apéndice A y los fixtures se actualizan en el mismo
commit, citando el código de la regla (Principio VI).

**Supuesto**: el `regla-id` de cada `defrule` es el `regla.id` de la versión vigente en la base, que
el 2026-11-04 coincide con el número del código (R07 → 7). Una versión nueva de una regla tendrá
otro `id`, así que este apéndice depende de las versiones actuales. T040 lo comprueba contra la
base de pruebas con `regla_id` en `casos_reglas.yaml`.

```clips
(defrule R01-v1
  (medicamento (codigo PARACETAMOL))
  (sintoma (codigo DOLOR_CABEZA))
  (not (condicion))
  =>
  (assert (disparo (regla-id 1))))

(defrule R02-v1
  (medicamento (codigo PARACETAMOL))
  (sintoma (codigo FIEBRE))
  (not (condicion))
  =>
  (assert (disparo (regla-id 2))))

(defrule R03-v1
  (medicamento (codigo PARACETAMOL))
  (sintoma (codigo DOLOR_MUSCULAR))
  (not (condicion))
  =>
  (assert (disparo (regla-id 3))))

(defrule R04-v1
  (medicamento (codigo PARACETAMOL))
  (sintoma (codigo DOLOR_DENTAL))
  (not (condicion))
  =>
  (assert (disparo (regla-id 4))))

(defrule R05-v1
  (medicamento (codigo PARACETAMOL))
  (sintoma (codigo DOLOR_ABDOMINAL))
  (not (condicion))
  =>
  (assert (disparo (regla-id 5))))

(defrule R06-v1
  (medicamento (codigo PARACETAMOL))
  (sintoma (codigo FIEBRE))
  (sintoma (codigo MOLESTIAS_RESPIRATORIAS))
  (not (condicion))
  =>
  (assert (disparo (regla-id 6))))

(defrule R07-v1
  (medicamento (codigo PARACETAMOL))
  (sintoma (codigo DOLOR_CABEZA))
  (sintoma (codigo FIEBRE))
  (not (condicion))
  =>
  (assert (disparo (regla-id 7))))

(defrule R08-v1
  (medicamento (codigo PARACETAMOL))
  (sintoma (codigo DOLOR_MUSCULAR))
  (sintoma (codigo FIEBRE))
  (not (condicion))
  =>
  (assert (disparo (regla-id 8))))

(defrule R09-v1
  (medicamento (codigo PARACETAMOL))
  (sintoma (codigo DOLOR_CABEZA))
  (condicion (codigo HIPERTENSION))
  =>
  (assert (disparo (regla-id 9))))

(defrule R10-v1
  (medicamento (codigo PARACETAMOL))
  (sintoma (codigo DOLOR_CABEZA))
  (condicion (codigo EMBARAZO))
  =>
  (assert (disparo (regla-id 10))))

(defrule R11-v1
  (medicamento (codigo PARACETAMOL))
  (sintoma (codigo FIEBRE))
  (condicion (codigo EMBARAZO))
  =>
  (assert (disparo (regla-id 11))))

(defrule R12-v1
  (medicamento (codigo PARACETAMOL))
  (sintoma (codigo DOLOR_MUSCULAR))
  (condicion (codigo ADULTO_MAYOR))
  =>
  (assert (disparo (regla-id 12))))

(defrule R13-v1
  (medicamento (codigo PARACETAMOL))
  (sintoma (codigo DOLOR_ABDOMINAL))
  (sintoma (codigo FIEBRE))
  (not (condicion))
  =>
  (assert (disparo (regla-id 13))))

(defrule R14-v1
  (medicamento (codigo PARACETAMOL))
  (sintoma (codigo FIEBRE))
  (sintoma (codigo MOLESTIAS_RESPIRATORIAS))
  (condicion (codigo USO_ANTIGRIPAL))
  =>
  (assert (disparo (regla-id 14))))

(defrule R15-v1
  (medicamento (codigo PARACETAMOL))
  (sintoma (codigo DOLOR_MUSCULAR))
  (condicion (codigo ADULTO_MAYOR))
  (condicion (codigo USO_ASPIRINA))
  =>
  (assert (disparo (regla-id 15))))

(defrule R16-v1
  (medicamento (codigo IBUPROFENO))
  (sintoma (codigo DOLOR_DENTAL))
  (not (condicion))
  =>
  (assert (disparo (regla-id 16))))

(defrule R17-v1
  (medicamento (codigo IBUPROFENO))
  (sintoma (codigo DOLOR_MUSCULAR))
  (not (condicion))
  =>
  (assert (disparo (regla-id 17))))

(defrule R18-v1
  (medicamento (codigo IBUPROFENO))
  (sintoma (codigo DOLOR_CABEZA))
  (not (condicion))
  =>
  (assert (disparo (regla-id 18))))

(defrule R19-v1
  (medicamento (codigo IBUPROFENO))
  (sintoma (codigo DOLOR_ABDOMINAL))
  (not (condicion))
  =>
  (assert (disparo (regla-id 19))))

(defrule R20-v1
  (medicamento (codigo IBUPROFENO))
  (sintoma (codigo DOLOR_MUSCULAR))
  (sintoma (codigo FIEBRE))
  (not (condicion))
  =>
  (assert (disparo (regla-id 20))))

(defrule R21-v1
  (medicamento (codigo IBUPROFENO))
  (sintoma (codigo FIEBRE))
  (sintoma (codigo MOLESTIAS_RESPIRATORIAS))
  (not (condicion))
  =>
  (assert (disparo (regla-id 21))))

(defrule R22-v1
  (medicamento (codigo IBUPROFENO))
  (sintoma (codigo DOLOR_CABEZA))
  (condicion (codigo EMBARAZO))
  =>
  (assert (disparo (regla-id 22))))

(defrule R23-v1
  (medicamento (codigo IBUPROFENO))
  (sintoma (codigo DOLOR_MUSCULAR))
  (condicion (codigo HIPERTENSION))
  =>
  (assert (disparo (regla-id 23))))

(defrule R24-v1
  (medicamento (codigo IBUPROFENO))
  (sintoma (codigo DOLOR_DENTAL))
  (condicion (codigo DIABETES))
  =>
  (assert (disparo (regla-id 24))))

(defrule R25-v1
  (medicamento (codigo IBUPROFENO))
  (sintoma (codigo DOLOR_MUSCULAR))
  (condicion (codigo ADULTO_MAYOR))
  =>
  (assert (disparo (regla-id 25))))

(defrule R26-v1
  (medicamento (codigo IBUPROFENO))
  (sintoma (codigo DOLOR_CABEZA))
  (condicion (codigo USO_ANTIGRIPAL))
  =>
  (assert (disparo (regla-id 26))))

(defrule R27-v1
  (medicamento (codigo IBUPROFENO))
  (sintoma (codigo FIEBRE))
  (sintoma (codigo MOLESTIAS_RESPIRATORIAS))
  (condicion (codigo USO_ASPIRINA))
  =>
  (assert (disparo (regla-id 27))))

(defrule R28-v1
  (medicamento (codigo IBUPROFENO))
  (sintoma (codigo DOLOR_MUSCULAR))
  (condicion (codigo ADULTO_MAYOR))
  (condicion (codigo HIPERTENSION))
  =>
  (assert (disparo (regla-id 28))))

(defrule R29-v1
  (medicamento (codigo IBUPROFENO))
  (sintoma (codigo DOLOR_MUSCULAR))
  (condicion (codigo DIABETES))
  (condicion (codigo HIPERTENSION))
  =>
  (assert (disparo (regla-id 29))))

(defrule R30-v1
  (medicamento (codigo IBUPROFENO))
  (sintoma (codigo DOLOR_DENTAL))
  (condicion (codigo ADULTO_MAYOR))
  (condicion (codigo OTRO_TRATAMIENTO))
  =>
  (assert (disparo (regla-id 30))))
```

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
