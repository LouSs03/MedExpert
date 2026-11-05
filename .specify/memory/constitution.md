# Constitución de MedExpert

Sistema experto basado en reglas para la orientación preventiva sobre automedicación en Perú
(tesis de pregrado).

## Core Principles

### I. Seguridad del Paciente Primero (NO NEGOCIABLE)

- El sistema orienta; NUNCA prescribe medicamentos, dosis ni tratamientos.
- Toda pantalla DEBE mostrar un aviso visible de que se trata de un prototipo académico que no
  reemplaza la consulta médica o farmacéutica.
- Si ninguna regla aprobada se dispara, la respuesta DEBE ser "Derivar al médico".
- Se autoriza UNA segunda excepción: un mensaje del sistema de **salvaguarda de cobertura** cuando
  algún síntoma marcado no está cubierto por las reglas disparadas. Condiciones:
  - (a) solo puede remitir al usuario a un médico o farmacéutico, sin indicar dosis, medicamentos
    ni recomendaciones clínicas;
  - (b) su texto y su activación DEBEN estar definidos en la especificación;
  - (c) mientras el médico especialista no lo apruebe, DEBE mostrarse marcado como "pendiente de
    aprobación";
  - (d) cualquier otro texto que no provenga de una regla aprobada sigue prohibido.
- Fuera de estas dos excepciones, el sistema NO DEBE inventar, inferir ni completar ninguna
  recomendación que no provenga literalmente de una regla aprobada.

**Justificación**: un consejo erróneo sobre automedicación puede causar daño real; ante la duda,
la única salida segura es derivar a un profesional.

### II. Conocimiento Separado del Código

- Las reglas DEBEN residir en la base de datos. Está PROHIBIDO codificar reglas, umbrales
  clínicos o mensajes de recomendación dentro del código fuente.
- Al arrancar, el motor DEBE cargar únicamente las reglas en estado `aprobada` y, de cada una,
  solo su versión más reciente.
- Ninguna recomendación puede mostrarse si no proviene de una regla validada por el médico
  especialista.
- Las únicas excepciones son los dos mensajes del sistema autorizados en el Principio I ("Derivar
  al médico" cuando ninguna regla aplica y la salvaguarda de cobertura). No son reglas ni
  recomendaciones, por lo que su texto puede definirse en el sistema, siempre conforme a la
  especificación y a las condiciones del Principio I.

**Justificación**: el conocimiento clínico lo valida el especialista, no el programador; separarlo
permite revisarlo, versionarlo y auditarlo sin tocar el código.

### III. Trazabilidad y Explicabilidad

- Cada recomendación DEBE registrar y mostrar al usuario los códigos de las reglas que se
  dispararon (R01–R30 y sucesivos).
- Cada consulta DEBE persistirse con sus hechos de entrada, el nivel resultante y las reglas
  aplicadas.
- **Única excepción: fallo técnico de persistencia.** Si el registro de una consulta falla por un
  error técnico, el sistema:
  - DEBE mostrar igualmente el resultado al usuario, porque ocultar una recomendación de seguridad
    es peor que no registrarla;
  - DEBE registrar el error en el log con detalle saneado (sin credenciales ni cadenas de conexión,
    Principio X);
  - DEBE marcar la respuesta como no persistida.

  Fuera de este caso, toda consulta respondida DEBE quedar persistida.

**Justificación**: un sistema experto que no explica su razonamiento no puede validarse
clínicamente ni defenderse académicamente.

### IV. Arquitectura Hexagonal (Puertos y Adaptadores)

Estructura obligatoria:

- `src/domain/`: entidades y objetos de valor puros (`Regla`, `Hecho`, `Consulta`, `Nivel`,
  `Sintoma`, `Condicion`). CERO imports de FastAPI, SQLModel, clips o cualquier librería externa.
- `src/application/`: casos de uso (`EvaluarConsulta`, `CargarBaseConocimiento`) e interfaces de
  puertos (`ReglaRepository`, `MotorInferencia`).
- `src/infrastructure/`: adaptadores concretos; `db/` (`PostgresReglaRepository` y
  `PostgresConsultaRepository` con SQLModel) e `inference/` (`ClipsMotorInferencia` con clipspy).
  Los adaptadores de `db/` dependen de PostgreSQL vía SQLModel, no del proveedor que aloja la base.
- `src/api/`: routers de FastAPI, esquemas Pydantic y plantillas Jinja2.
- `tests/`: `unit/`, `integration/`, `e2e/`.

Regla de dependencia: las dependencias apuntan siempre hacia adentro. `domain` no conoce a
nadie; `application` solo conoce a `domain`; `infrastructure` y `api` conocen a `application` y
`domain`. Toda violación de esta regla es motivo de rechazo del cambio.

**Justificación**: aislar el dominio permite probar el razonamiento sin base de datos ni CLIPS, y
sustituir adaptadores sin reescribir la lógica.

### V. Patrones de Diseño Obligatorios

- **Repository**: interfaz `ReglaRepository` en `application/ports`; implementación
  `PostgresReglaRepository` en `infrastructure` (y `PostgresConsultaRepository` para el registro
  de consultas). Los casos de uso NUNCA ejecutan SQL.
- **Port/Adapter**: interfaz `MotorInferencia` en `application/ports`; implementación
  `ClipsMotorInferencia` en `infrastructure`. DEBE existir además `FakeMotorInferencia` para
  pruebas sin CLIPS.
- **Strategy**: la resolución del nivel final (DERIVAR > ADVERTIR > ORIENTAR) DEBE encapsularse
  en una estrategia sustituible, no en condicionales dispersos.
- **Factory**: una fábrica DEBE construir un entorno CLIPS limpio por cada consulta, de modo que
  los hechos de un usuario nunca se mezclen con los de otro. La base de conocimiento cargada al
  arranque se mantiene inmutable y se inyecta en la fábrica.
- **DTO**: Pydantic para la entrada y salida de la API. Las entidades de dominio NUNCA se exponen
  directamente en los endpoints.
- **Inyección de dependencias** mediante `Depends` de FastAPI. Está PROHIBIDO instanciar
  repositorios o el motor dentro de los routers.

Antipatrones prohibidos: lógica de negocio en los routers, SQL fuera de `infrastructure/db`,
imports de clips fuera de `infrastructure/inference` y variables globales mutables.

### VI. Estándar de Commits (Conventional Commits)

- Formato obligatorio: `tipo(alcance): descripción` en imperativo y minúscula, con un máximo de
  72 caracteres en la primera línea.
- Tipos permitidos: `feat`, `fix`, `docs`, `test`, `refactor`, `perf`, `style`, `chore`,
  `build`, `ci`.
- Alcances sugeridos: `domain`, `application`, `infra`, `api`, `db`, `motor`, `reglas`, `tests`,
  `docs`.
- Ejemplos: `feat(motor): cargar reglas aprobadas desde el repositorio`,
  `fix(api): validar sintoma fuera del vocabulario`,
  `test(reglas): agregar caso de regresion R11`.
- Un commit, un cambio lógico. Están PROHIBIDOS mensajes como "cambios", "avance" o "wip" en la
  rama principal.
- Si el cambio rompe compatibilidad, DEBE usarse `!` después del alcance y explicarse en el
  cuerpo.
- Todo commit que modifique una regla DEBE citar su código (R01–R30) en el cuerpo del mensaje.

### VII. Estrategia de Ramas (GitHub Flow)

- La rama `main` DEBE estar siempre en estado desplegable; nunca se commitea directamente sobre
  ella.
- **Ramas de funcionalidad**: las crea `/speckit-specify` con el formato obligatorio
  `NNN-descripcion-corta` (por ejemplo, `001-consulta-orientacion`). Cada rama DEBE corresponder
  1 a 1 con su carpeta en `specs/` (misma numeración y misma descripción); una funcionalidad
  especificada, una rama.
- **Ramas que no nacen de una especificación**: usan prefijo `fix/<descripcion>`,
  `docs/<descripcion>`, `chore/<descripcion>` o `test/<descripcion>`.
- Todos los nombres de rama van en minúscula y separados por guiones.
- Toda rama se integra a `main` mediante pull request, nunca por merge local directo. El pull
  request de una rama de funcionalidad DEBE indicar qué spec implementa, y ningún pull request se
  fusiona si la suite completa de pruebas falla.
- Las ramas se eliminan después de fusionarse.

**Justificación**: la numeración `NNN` da trazabilidad directa entre la especificación y la rama
que la implementa.

### VIII. Estrategia de Pruebas (Pirámide)

- **Unitarias**: traducción de cada regla de la base de datos a `defrule` de CLIPS, estrategia de
  resolución de nivel y validación del vocabulario.
- **Integración**: repositorio contra PostgreSQL real; carga completa de la base de conocimiento
  en el motor.
- **Aceptación de la base de conocimiento**: cada regla aprobada por el médico (las 30 reglas
  R01–R30 de la base inicial y toda regla aprobada posteriormente) es un caso de prueba
  obligatorio. Cada caso ejecuta el sistema con los hechos exactos de su regla y verifica que
  devuelva el nivel y los mensajes aprobados. Esta suite se ejecuta completa en cada cambio como
  pruebas de regresión (biblioteca indexada de casos de prueba; Buchanan y Shortliffe, 1984).
- **End-to-end con Playwright**: flujo completo del usuario (formulario, envío, resultado y
  explicación) para al menos un caso de cada nivel (ORIENTAR, ADVERTIR, DERIVAR).
- Cobertura mínima del 80% en `domain/` y `application/`.
- Ningún pull request se fusiona con pruebas en rojo.

### IX. Calidad y Estilo

- Type hints obligatorios en todo el código.
- `ruff` para formato y linting; `mypy` en modo estricto sobre `domain/` y `application/`.
- Los nombres del dominio DEBEN estar en español (`Regla`, `Sintoma`, `Consulta`, `Nivel`); está
  prohibido mezclar inglés en el dominio.
- Toda función pública DEBE tener un docstring que indique qué hace, no cómo lo hace.

### X. Seguridad de Datos

- No se almacena ningún dato personal identificable.
- Las credenciales residen únicamente en variables de entorno; `.env` DEBE estar siempre en
  `.gitignore`.
- RLS (Row Level Security) DEBE estar activo en todas las tablas de Supabase.
- Está PROHIBIDO registrar credenciales o cadenas de conexión en los logs.

### XI. Desarrollo Incremental de la Base de Conocimiento (Buchanan y Shortliffe, 1984)

- Toda regla nueva o modificada entra como versión nueva en estado `pendiente` y solo pasa a
  `aprobada` tras la validación del médico especialista.
- Al cambiar cualquier regla se DEBE ejecutar la suite completa de casos antiguos antes de
  aceptar el cambio.
- Una regla ya aprobada NUNCA se edita en sitio; todo cambio genera una nueva versión.

**Justificación**: el versionado inmutable preserva la trazabilidad de las consultas pasadas y
evita que un cambio silencioso altere recomendaciones ya validadas.

## Restricciones Técnicas y Stack

- Lenguaje: Python 3.12 o superior (verificado con 3.13). El despliegue DEBE fijar la versión
  explícitamente.
- API y presentación: FastAPI con plantillas Jinja2; esquemas de entrada/salida en Pydantic.
- Motor de inferencia: CLIPS mediante clipspy, confinado a `src/infrastructure/inference/`.
- Persistencia: SQLModel sobre PostgreSQL alojado en Supabase, confinado a
  `src/infrastructure/db/`.
- Pruebas: pytest (unitarias, integración y aceptación) y Playwright (end-to-end).
- Calidad: ruff y mypy (estricto en `domain/` y `application/`).
- Cualquier dependencia nueva DEBE justificarse en el plan de la funcionalidad y respetar la regla
  de dependencia del Principio IV.

## Flujo de Desarrollo y Puertas de Calidad

Todo pull request hacia `main` DEBE superar, como mínimo, estas puertas:

1. Rama nombrada según el Principio VII; si es de funcionalidad (`NNN-descripcion-corta`),
   corresponde a su carpeta en `specs/`.
2. Commits conforme al Principio VI (incluida la cita de códigos de regla cuando aplique).
3. `ruff` sin errores y `mypy` estricto sin errores en `domain/` y `application/`.
4. Suite completa en verde: unitarias, integración, aceptación de la base de conocimiento y
   end-to-end.
5. Cobertura ≥ 80% en `domain/` y `application/`.
6. Revisión de cumplimiento arquitectónico: sin imports prohibidos entre capas, sin SQL ni clips
   fuera de sus adaptadores, sin lógica de negocio en routers.
7. Si el cambio afecta reglas: nueva versión en estado `pendiente` y evidencia de validación del
   médico especialista antes de pasarla a `aprobada`.

## Gobernanza

- Esta constitución prevalece sobre cualquier otra práctica, guía o preferencia del proyecto. En
  caso de conflicto entre un spec, un plan o una tarea y esta constitución, prevalece la
  constitución.
- **Enmiendas**: toda modificación se propone mediante pull request desde una rama
  `docs/<descripcion-corta>`, describe el cambio y su motivo, actualiza la versión y la fecha de
  última enmienda, e incluye un plan de migración si afecta código o reglas existentes.
- **Versionado** (semántico):
  - MAJOR: eliminación o redefinición incompatible de un principio o de la gobernanza.
  - MINOR: adición de un principio o sección, o ampliación material de una guía.
  - PATCH: aclaraciones, redacción o correcciones sin cambio semántico.
- **Cumplimiento**: cada plan (`/speckit-plan`) DEBE incluir una verificación explícita frente a
  esta constitución, y cada revisión de pull request DEBE confirmar su cumplimiento. Toda
  excepción DEBE justificarse por escrito en el plan y aprobarse antes de implementarse; las
  violaciones de los Principios I, II y IV no admiten excepción.

**Version**: 1.2.0 | **Ratified**: 2026-11-04 | **Last Amended**: 2026-11-04
