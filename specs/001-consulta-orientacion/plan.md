# Implementation Plan: Consulta de orientación sobre automedicación

**Branch**: `001-consulta-orientacion` | **Date**: 2026-11-04 (rev. 2) | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-consulta-orientacion/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

Una persona elige un medicamento, sus síntomas y sus condiciones, y recibe un nivel de orientación
(Orientar, Advertir o Derivar al médico), los mensajes aprobados y los códigos de las reglas que
se dispararon, en un orden determinista. El enfoque técnico: al arrancar, FastAPI carga desde
PostgreSQL el vocabulario y las 30 reglas aprobadas vigentes y las convierte en una base de
conocimiento inmutable. Por cada consulta, una fábrica crea un entorno CLIPS limpio con las reglas
traducidas a `defrule` y ejecuta el encadenamiento hacia adelante. Una estrategia sustituible
resuelve el nivel por severidad e incluye la **salvaguarda de cobertura**: si un síntoma marcado
no está en ninguna regla disparada, el nivel sube como mínimo a Advertir y se añade un mensaje del
sistema, marcado "pendiente de aprobación" según configuración. La consulta se guarda en una sola
transacción; si falla, el resultado se muestra igual con una marca interna. Las pruebas de
integración y e2e corren solo contra una base separada. Como es la primera funcionalidad, el plan
incluye también la estructura hexagonal, la configuración y las herramientas de calidad.

**Cambios de la rev. 2**: FR-006, FR-009, FR-020 y FR-021 y SC-009 a SC-011 incorporados; DTO con
síntomas no cubiertos y mensajes del sistema; marca configurable
`SALVAGUARDA_PENDIENTE_APROBACION`; adaptadores renombrados a `PostgresReglaRepository` y
`PostgresConsultaRepository`; constitución v1.1.0 (Python 3.12 o superior).

## Technical Context

**Language/Version**: Python ≥ 3.12; referencia y despliegue fijados en 3.13 con
`.python-version` (constitución v1.1.0, [research D13](research.md))

**Primary Dependencies**: FastAPI 0.162, Jinja2 3.1, python-multipart (nuevo), clipspy 1.0.6,
SQLModel 0.0.48 / SQLAlchemy 2.1, psycopg 3.3, python-dotenv 1.2, uvicorn 0.54

**Storage**: PostgreSQL (hoy alojado en Supabase), con esquema existente (11 tablas, RLS activo),
accedido por el pooler en modo sesión (5432). Solo lectura de catálogos y reglas; escritura en
`consulta` y sus tablas hijas. Base separada para pruebas (`TEST_DATABASE_URL`).

**Testing**: pytest 9 + pytest-cov (unit, integration, aceptacion), Playwright 1.64 +
pytest-playwright (e2e), ruff 0.17, mypy 2.4 (strict en domain/application)

**Target Platform**: servidor web Linux o Windows con Python 3.13; navegador de escritorio o móvil
actual

**Project Type**: aplicación web monolítica (HTML renderizado en el servidor + API JSON)

**Performance Goals**: resultado en < 2 s tras enviar (SC-005); evaluación CLIPS medida en el
prototipo: unos 7,4 ms por consulta

**Constraints**: entorno CLIPS aislado por consulta (FR-016); orden de salida determinista
(SC-010); ningún dato personal (FR-015); sin credenciales en logs (Principio X); base de
conocimiento de solo lectura (FR-017); las pruebas nunca tocan la base real (FR-021)

**Scale/Scope**: prototipo de tesis: 2 medicamentos, 6 síntomas, 7 condiciones, 30 reglas
(16.128 combinaciones posibles); 20 consultas simultáneas (SC-008); 5 pantallas o estados

No quedan NEEDS CLARIFICATION. Los pendientes P3, P5 y P8 de [research.md](research.md)
son acciones del usuario, no incógnitas técnicas.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Contra la constitución **v1.2.0**.

| # | Principio | Cómo lo cumple el diseño | Estado |
|---|-----------|--------------------------|--------|
| I | Seguridad del paciente | Aviso en `base.html`; solo dos mensajes del sistema: `COMBINACION_NO_CUBIERTA` y `SINTOMA_NO_CUBIERTO`. El segundo (a) solo remite a médico o farmacéutico; (c) se muestra "pendiente de aprobación médica" mientras `SALVAGUARDA_PENDIENTE_APROBACION=true`; (d) ningún otro texto fuera de las reglas. La salvaguarda nunca rebaja el nivel ni es desactivable; (b) texto literal y activación definidos en FR-020 | ✅ |
| II | Conocimiento separado | Reglas y vocabulario se leen de la base al arrancar; solo `aprobada` y la versión más reciente; en el código solo están las dos plantillas autorizadas por la excepción del Principio II | ✅ |
| III | Trazabilidad | `consulta` + hijas con `regla_id` de la versión exacta y `orden` de FR-009; nivel ya elevado; explicación con códigos y síntomas no cubiertos (FR-010); el fallo técnico de persistencia (FR-019) sigue la única excepción del Principio III: resultado visible, error saneado en el log y marca de no persistida | ✅ |
| IV | Hexagonal | Layout `src/domain`, `application`, `infrastructure`, `api`; `test_arquitectura.py` hace fallar la suite ante imports prohibidos; adaptadores `PostgresReglaRepository` y `PostgresConsultaRepository` como nombra la constitución | ✅ |
| V | Patrones | Repository (`ReglaRepository`/`ConsultaRepository` + `Postgres*Repository`), Port/Adapter (`MotorInferencia` + `ClipsMotorInferencia` + `FakeMotorInferencia`), Strategy (`ResolucionPorSeveridad`, que incluye la salvaguarda), Factory (`FabricaEntornoClips`), DTOs Pydantic, `Depends`; estado solo en `app.state`, sin `app` a nivel de módulo (`uvicorn --factory`) | ✅ |
| VI | Commits | Convención aplicada en `/speckit-implement`; esta funcionalidad no modifica reglas | ✅ |
| VII | Ramas | `001-consulta-orientacion` ↔ `specs/001-consulta-orientacion/` | ✅ |
| VIII | Pruebas | Unit (traductor, estrategia + salvaguarda, vocabulario, arquitectura, logs), integración (repositorios, carga completa), aceptación (30 casos R01–R30 sin salvaguarda activa), e2e (un caso por nivel + no cubierta + salvaguarda), cobertura ≥ 80 % | ✅ (ejecutarlas requiere P8) |
| IX | Calidad | ruff + mypy strict en `pyproject.toml`; nombres de dominio en español; docstrings de "qué hace" | ✅ |
| X | Seguridad de datos | Sin datos personales; `DATABASE_URL`/`TEST_DATABASE_URL` por entorno; filtro de logs; RLS activo en las 11 tablas (verificado) | ✅ |
| XI | Desarrollo incremental | Solo lectura de reglas; suite de aceptación de 30 casos en cada cambio | ✅ |
| Stack | Python ≥ 3.12, versión fijada en despliegue | `requires-python >= 3.12` + `.python-version` = 3.13 | ✅ |

**Resultado del gate**:

- **Diseño, `/speckit-tasks` y `/speckit-implement`: aprobado.** No hay violaciones de la
  constitución.
- Para **ejecutar** la aplicación hace falta P3 (`.env` corregido), y para ejecutar las suites
  `integration`, `aceptacion` y `e2e`, P8 (base de pruebas). Ninguno de los dos impide escribir el
  código.

## Project Structure

### Documentation (this feature)

```text
specs/001-consulta-orientacion/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   ├── http.md
│   ├── puertos.md
│   └── traduccion-clips.md
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
pyproject.toml                 # dependencias + ruff + mypy + pytest (fuente única)
requirements.txt               # regenerado en UTF-8 desde pyproject.toml
.python-version                # 3.13 (versión fijada para referencia y despliegue)
.env.example                   # DATABASE_URL, TEST_DATABASE_URL, SALVAGUARDA_PENDIENTE_APROBACION (sin valores)

src/
├── domain/                    # sin imports externos
│   ├── __init__.py
│   ├── nivel.py               # Nivel, EstadoRegla
│   ├── vocabulario.py         # Medicamento, Sintoma, Condicion, Vocabulario, HechosConsulta
│   ├── regla.py               # Regla, ReglaDisparada
│   ├── base_conocimiento.py   # BaseConocimiento
│   ├── mensajes_sistema.py    # TipoMensajeSistema, MensajeSistema, ConfiguracionSalvaguarda, plantillas
│   ├── consulta.py            # Consulta, ResultadoEvaluacion
│   ├── resolucion_nivel.py    # EstrategiaResolucionNivel, Resolucion, ResolucionPorSeveridad (+ salvaguarda)
│   └── errores.py             # VocabularioInvalido, BaseConocimientoNoDisponible
├── application/               # solo conoce a domain
│   ├── __init__.py
│   ├── ports/
│   │   ├── regla_repository.py
│   │   ├── consulta_repository.py
│   │   └── motor_inferencia.py
│   └── casos_uso/
│       ├── cargar_base_conocimiento.py
│       └── evaluar_consulta.py
├── infrastructure/
│   ├── __init__.py
│   ├── config.py              # DATABASE_URL y SALVAGUARDA_PENDIENTE_APROBACION
│   ├── logging.py             # filtro de redacción de secretos
│   ├── db/
│   │   ├── engine.py          # create_engine + get_session
│   │   ├── modelos.py         # SQLModel table=True que reflejan el esquema existente
│   │   ├── postgres_regla_repository.py
│   │   └── postgres_consulta_repository.py
│   └── inference/             # único lugar que importa clips
│       ├── traductor_reglas.py
│       ├── fabrica_entorno.py
│       └── clips_motor_inferencia.py
└── api/
    ├── __init__.py
    ├── main.py                # create_app() + lifespan
    ├── dependencias.py        # proveedores para Depends
    ├── esquemas.py            # DTOs Pydantic (incl. MensajeSistemaDTO, sintomas_no_cubiertos)
    ├── routers/
    │   ├── consulta.py        # GET /, POST /consulta, POST /api/v1/consultas
    │   └── salud.py           # GET /salud
    ├── plantillas/
    │   ├── base.html          # aviso de prototipo académico
    │   ├── formulario.html
    │   ├── resultado.html     # reglas, bloque "Mensaje del sistema", explicación
    │   └── no_disponible.html
    └── estaticos/
        └── estilos.css

docs/
├── base-de-pruebas.md         # cómo crear la base separada de pruebas (FR-021)
└── usabilidad-sc004.md        # tiempos de la prueba de usabilidad (SC-004)

tests/
├── conftest.py                # exige TEST_DATABASE_URL ≠ DATABASE_URL (FR-021)
├── fakes/                     # FakeMotorInferencia, repositorios en memoria
├── unit/
│   ├── domain/                # vocabulario, resolución + salvaguarda (tabla de decisión), orden FR-009
│   ├── application/           # EvaluarConsulta y CargarBaseConocimiento con fakes; marca configurable
│   ├── inference/             # traducción de cada regla a defrule, aislamiento de entornos
│   │   ├── test_traduccion_30_reglas.py  # defrule exacto y disparo de cada una de las 30 reglas
│   │   └── defrules_esperados.clp        # texto esperado (Apéndice B de tasks.md)
│   ├── api/                   # DTOs, rutas con dependencias sustituidas, marca interna, mensajes del sistema
│   ├── test_config.py         # SALVAGUARDA_PENDIENTE_APROBACION válida / inválida
│   ├── test_logging.py        # redacción de secretos
│   └── test_arquitectura.py   # regla de dependencia del Principio IV
├── integration/
│   ├── test_postgres_regla_repository.py
│   ├── test_postgres_consulta_repository.py
│   ├── test_carga_base_conocimiento.py
│   ├── test_combinaciones.py  # 16.128 combinaciones: CLIPS == oráculo FR-006/FR-020 (marcador lento)
│   ├── test_concurrencia.py   # 20 consultas simultáneas y orden estable (SC-008, SC-010)
│   ├── test_rls.py            # RLS activo en todas las tablas de public (Principio X)
│   └── aceptacion/
│       ├── casos_reglas.yaml  # biblioteca indexada R01–R30: hechos, nivel y códigos esperados
│       └── test_aceptacion_reglas.py
└── e2e/
    ├── conftest.py            # levanta el servidor con DATABASE_URL = TEST_DATABASE_URL
    └── test_flujo_consulta.py # Orientar, Advertir, Derivar, no cubierta y salvaguarda (escenario 6)
```

**Structure Decision**: proyecto único con las cuatro capas del Principio IV como paquetes de
primer nivel bajo `src/` (`pythonpath = ["src"]`). La suite de aceptación vive en
`tests/integration/aceptacion/` porque necesita la base y CLIPS reales. `test_combinaciones.py`
compara el motor CLIPS con el oráculo de FR-006 y FR-020 en todas las combinaciones (unos 2 min
según el prototipo), así que se marca como lenta pero forma parte de la suite completa. Los fakes
quedan en `tests/fakes/`, fuera del código desplegable.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

Sin violaciones que justificar.
