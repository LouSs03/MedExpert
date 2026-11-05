# MedExpert

Sistema experto basado en reglas para la **orientación preventiva sobre automedicación** en Perú.
Prototipo académico desarrollado como tesis de pregrado.

> **Prototipo académico: no reemplaza la consulta médica o farmacéutica.**
> Este aviso aparece en todas las pantallas de la aplicación.

## Qué es y qué no es

**Es** un sistema experto que, a partir del medicamento que una persona piensa tomar
(paracetamol o ibuprofeno), sus síntomas y algunas condiciones (embarazo, diabetes,
hipertensión, edad de 60 años o más, otros tratamientos, uso de antigripal o de aspirina),
devuelve:

- un **nivel de orientación**: *Orientar*, *Advertir* o *Derivar al médico*;
- los **mensajes aprobados** por un médico especialista para ese caso;
- la **explicación del razonamiento**: qué reglas (R01–R30) se aplicaron.

Razona por **encadenamiento hacia adelante** con CLIPS sobre una base de conocimiento de
**30 reglas** validadas por un médico especialista, guardadas en PostgreSQL.

**No es** un sistema de prescripción ni de diagnóstico:

- No indica dosis, frecuencias ni duración de tratamientos, salvo que el texto aprobado de una
  regla lo diga literalmente.
- No inventa recomendaciones: si ninguna regla aplica, responde *Derivar al médico*.
- Solo conoce 2 medicamentos, 6 síntomas y 7 condiciones. Cualquier caso fuera de ese
  vocabulario queda fuera de su alcance.
- No reemplaza al médico ni al farmacéutico en ningún caso.

## Cómo razona

1. La persona elige **un** medicamento, marca **al menos un** síntoma y cero o más condiciones.
2. Una regla se dispara si están presentes **todos** sus síntomas y condiciones. Los hechos de
   más no la bloquean, salvo en las reglas "sin condiciones", que solo se disparan si no se marcó
   ninguna condición.
3. Si se disparan varias reglas, se muestran **todas**: primero las de nivel más severo, luego
   las más específicas y luego por código. El nivel final es el más severo
   (*Derivar* > *Advertir* > *Orientar*).
4. **Si no se dispara ninguna regla**, el resultado es *Derivar al médico*, con un mensaje que
   indica que la combinación no está cubierta por la base de conocimiento validada.
5. **Salvaguarda de cobertura**: si algún síntoma marcado no aparece en ninguna regla disparada,
   el nivel sube como mínimo a *Advertir* y se añade un mensaje del sistema que remite a un
   médico o farmacéutico.
6. Cada consulta se registra (sin datos personales) con sus hechos, el nivel y las reglas
   aplicadas. Si el registro falla por un error técnico, el resultado se muestra igual y el error
   queda en el log, con las credenciales ocultas.

## Arquitectura

Arquitectura hexagonal (puertos y adaptadores). Las dependencias apuntan siempre hacia adentro:

```text
    ┌──────────────────────────────────────────────────────────────────┐
    │ api/  (FastAPI, Jinja2, DTOs Pydantic)                           │
    │ raíz de composición: create_app() y Depends                      │
    └──────────────────────────────────────────────────────────────────┘
                    │ usa
                    ▼
    ┌──────────────────────────────────────────────────────────────────┐
    │ application/                                                     │
    │   casos de uso: CargarBaseConocimiento, EvaluarConsulta          │
    │   puertos: ReglaRepository, ConsultaRepository, MotorInferencia  │
    └──────────────────────────────────────────────────────────────────┘
                    │ usa
                    ▼
    ┌──────────────────────────────────────────────────────────────────┐
    │ domain/  (Python puro, sin librerías externas)                   │
    │   Regla, Vocabulario, HechosConsulta, Nivel, Consulta,           │
    │   ResolucionPorSeveridad (+ salvaguarda), mensajes del sistema   │
    └──────────────────────────────────────────────────────────────────┘
                    ▲
                    │ usa el dominio e implementa los puertos de application/
    ┌──────────────────────────────────────────────────────────────────┐
    │ infrastructure/                                                  │
    │   db/         PostgresReglaRepository,                           │
    │               PostgresConsultaRepository   (SQLModel)            │
    │   inference/  ClipsMotorInferencia, FabricaEntornoClips          │
    │               (clipspy: un entorno CLIPS limpio por consulta)    │
    │   config.py, logging.py  (redacción de secretos)                 │
    └──────────────────────────────────────────────────────────────────┘
```

- `domain/` no importa nada fuera de la biblioteca estándar, y `application/` solo importa
  `domain/`.
- `clips` solo se importa en `infrastructure/inference/`, y SQLModel, SQLAlchemy y psycopg solo
  en `infrastructure/db/`.
- La prueba `tests/unit/test_arquitectura.py` hace fallar la suite si se rompe cualquiera de
  estas reglas.
- Patrones: Repository, Port/Adapter (con `FakeMotorInferencia` para pruebas sin CLIPS),
  Strategy (resolución del nivel), Factory (entornos CLIPS) y DTO.

La gobernanza del proyecto está en la constitución
([.specify/memory/constitution.md](.specify/memory/constitution.md)). El diseño de esta
funcionalidad está en [specs/001-consulta-orientacion/](specs/001-consulta-orientacion/).

## Requisitos

- Python **3.12 o superior**. La versión de referencia es **3.13** (`.python-version`).
- Una base PostgreSQL con el esquema y las 30 reglas aprobadas (hoy alojada en Supabase).
- Para las pruebas de integración y e2e: una **segunda** base, separada, solo para pruebas
  (ver [docs/base-de-pruebas.md](docs/base-de-pruebas.md)).

## Instalación

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate     Linux/macOS: source .venv/bin/activate
pip install -e ".[dev]"
playwright install chromium        # solo para las pruebas e2e
```

Copia `.env.example` a `.env` (nunca se versiona) y completa las variables:

| Variable | Obligatoria | Descripción |
|----------|-------------|-------------|
| `DATABASE_URL` | Sí | Base real. Formato `postgresql+psycopg://usuario:clave@host:5432/postgres` |
| `TEST_DATABASE_URL` | Solo para pruebas | Base **separada** de pruebas. Debe ser distinta de `DATABASE_URL`, o las pruebas abortan. **Nunca** se configura en producción |
| `SALVAGUARDA_PENDIENTE_APROBACION` | No (por defecto `true`) | Marca el mensaje de salvaguarda como "Pendiente de aprobación médica" |

**Sobre `SALVAGUARDA_PENDIENTE_APROBACION`**: solo puede ponerse en `false` cuando el médico
especialista haya aprobado el texto del mensaje de salvaguarda (FR-020). Ese cambio se hace en
un commit propio que deja constancia de la aprobación. Cualquier valor distinto de `true` o
`false` impide arrancar la aplicación.

## Ejecución

```bash
uvicorn api.main:create_app --factory --app-dir src --reload
```

| Ruta | Descripción |
|------|-------------|
| `GET /` | Formulario de consulta |
| `POST /consulta` | Envío del formulario; muestra el resultado |
| `POST /api/v1/consultas` | API JSON (ver [contracts/http.md](specs/001-consulta-orientacion/contracts/http.md)) |
| `GET /salud` | 200 si la base de conocimiento está cargada; 503 si no |

Ejemplo de consulta JSON:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/consultas \
  -H "Content-Type: application/json" \
  -d '{"medicamento": "PARACETAMOL", "sintomas": ["DOLOR_CABEZA"], "condiciones": []}'
```

La aplicación lee las reglas **al arrancar**. Para que tome en cuenta una regla nueva o
modificada, hay que reiniciarla. Si al arrancar no puede cargar ninguna regla aprobada, todas
las pantallas responden "servicio no disponible". Si la base no responde, cada intento de
conexión se abandona a los 10 s, para que el arranque no se cuelgue.

> Ojo: con `DATABASE_URL` apuntando a la base real, cada consulta que hagas a mano queda
> registrada en ella. Para probar, apunta `DATABASE_URL` a la base de pruebas.

## Pruebas

Las suites de integración, aceptación y e2e se ejecutan **solo** contra `TEST_DATABASE_URL`.
Nunca leen ni escriben en la base real (FR-021).

| Tipo | Comando | Qué cubre |
|------|---------|-----------|
| Unitarias | `pytest -m "not integration and not aceptacion and not e2e"` | Dominio, casos de uso con dobles, traducción de las 30 reglas a CLIPS, rutas, configuración, logs y regla de dependencia. No necesita base de datos |
| Integración | `pytest -m "integration and not lento"` | Repositorios contra PostgreSQL real, carga completa de la base, registro atómico, ausencia de datos personales y RLS |
| Aceptación | `pytest -m aceptacion` | Biblioteca de casos R01–R30 (un caso por regla) y combinaciones no cubiertas. Es la suite de regresión: se ejecuta en cada cambio |
| e2e | `pytest -m e2e` | Navegador real (Playwright): un caso por nivel, salvaguarda, combinaciones no cubiertas y tiempo de respuesta menor de 2 s |
| Lentas | `pytest -m lento` | Las **16.128** combinaciones posibles comparadas con un oráculo de la especificación (unos 2,5 min) y 20 consultas simultáneas |
| Todo, rápido | `pytest -m "not lento"` | Todo menos las lentas |
| Todo, con cobertura | `pytest --cov=domain --cov=application --cov-report=term-missing --cov-fail-under=80` | Suite completa; exige al menos 80 % de cobertura en `domain` y `application` |

Calidad del código:

```bash
ruff format --check . && ruff check .
mypy                     # modo estricto sobre src/domain y src/application
```

## Despliegue en Render

Servicio web de Python:

| Ajuste | Valor |
|--------|-------|
| Build command | `pip install -r requirements.txt && pip install --no-deps .` |
| Start command | `uvicorn --factory api.main:create_app --host 0.0.0.0 --port $PORT` |
| Health check path | `/salud` |

- **Por qué el build tiene dos partes**: `requirements.txt` fija las versiones exactas, y
  `pip install --no-deps .` instala los paquetes de `src/` con sus plantillas y estilos. Con solo
  `requirements.txt` la aplicación no arranca (`ModuleNotFoundError: No module named 'api'`).
- **Variables de entorno en Render**:
  - `DATABASE_URL`: la base real.
  - `PYTHON_VERSION=3.13.13`: la versión exacta verificada; la constitución exige fijarla en el
    despliegue.
  - `SALVAGUARDA_PENDIENTE_APROBACION=true`: opcional, pero conviene dejarla explícita.
  - **No** se configura `TEST_DATABASE_URL`.
- **Verificado sin desplegar**: el arranque se comprobó en un entorno limpio con Python 3.13.13,
  y todas las dependencias, incluido `clipspy`, tienen paquetes precompilados para Linux x86_64.
- **Si la base no carga**: `/salud` devuelve 503 cuando la base de conocimiento no pudo cargarse
  al arrancar. Así Render detecta el despliegue como fallido, en lugar de publicar un servicio
  que solo muestra "no disponible".

## Limitaciones

Conviene tenerlas presentes al evaluar o presentar el sistema:

- **Cobertura de solo 30 reglas.** De las 16.128 combinaciones posibles de medicamento,
  síntomas y condiciones, unas **4.365 (27 %) no activan ninguna regla** y terminan en *Derivar
  al médico* con el mensaje de combinación no cubierta. Es la respuesta segura, pero indica
  cuánto del espacio de consultas no está cubierto por conocimiento validado.
- **La salvaguarda de cobertura cambia mucho el resultado.** Sin ella, 731 combinaciones darían
  *Orientar*; con ella, **657 de esas 731** suben a *Advertir*, porque algún síntoma marcado
  queda sin regla. Solo 74 combinaciones terminan en *Orientar*.
- **El texto de la salvaguarda está pendiente de aprobación médica.** Lo define el sistema, no
  una regla validada. Se muestra con el distintivo "Pendiente de aprobación médica" hasta que el
  médico lo apruebe (Principio I de la constitución).
- **La aprobación de las reglas no está registrada en la base.** Las 30 reglas están en estado
  `aprobada`, pero los campos `aprobada_por` y `fecha_aprobacion` están vacíos. La trazabilidad
  de quién aprobó cada regla y cuándo depende hoy de documentación externa.
- **Sin interfaz para administrar reglas.** El sistema solo lee la base de conocimiento.
  Aprobar, versionar o rechazar reglas se hace directamente en la base, y cada cambio exige
  volver a ejecutar la suite de aceptación.
- **Las condiciones las declara la persona.** Por ejemplo, el sistema no pide la edad: la
  persona marca "Adulto mayor (60 años o más)". El resultado depende de que la información sea
  correcta.
- **Alcance reducido**: dos medicamentos, interfaz solo en español, sin cuentas de usuario y sin
  historial de consultas visible para la persona.
- **Usabilidad sin medir todavía**: el objetivo de completar una consulta en menos de un minuto
  (SC-004) está pendiente de una prueba con personas
  ([docs/usabilidad-sc004.md](docs/usabilidad-sc004.md)).
