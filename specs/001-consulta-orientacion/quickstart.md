# Quickstart: validar la consulta de orientación (rev. 2)

Guía para comprobar de punta a punta que la funcionalidad cumple la [spec](spec.md). Los detalles
de interfaces están en [contracts/](contracts/) y los de entidades en [data-model.md](data-model.md).

## Prerrequisitos

1. Python 3.12 o superior. La versión de referencia es la de `.python-version` (3.13); ver
   research D13.
2. `.env` (nunca se versiona) con:
   - `DATABASE_URL=postgresql+psycopg://<usuario>:<clave>@aws-0-us-east-1.pooler.supabase.com:5432/postgres`.
     El nombre de la variable debe aparecer una sola vez (research P3).
   - `TEST_DATABASE_URL=...` apuntando a la base **separada** de pruebas, con el mismo esquema y
     las 30 reglas (research D12, P8). Debe ser distinta de `DATABASE_URL`; si no lo es, la suite
     aborta.
   - Opcional: `SALVAGUARDA_PENDIENTE_APROBACION=true` (valor por defecto; research D14).
3. Instalar dependencias: `pip install -e ".[dev]"`, y después `playwright install chromium`.

## Comprobaciones estáticas

```bash
ruff format --check . && ruff check .
mypy                       # strict sobre src/domain y src/application (configurado en pyproject)
```

Resultado esperado: ningún error.

## Pruebas

```bash
pytest -m "not integration and not aceptacion and not e2e"   # unitarias, sin red
pytest -m integration                                        # repositorios contra la base de pruebas
pytest -m aceptacion                                         # 30 casos R01–R30 (regresión)
pytest -m e2e                                                # Playwright contra la base de pruebas
pytest -m lento                                              # 16.128 combinaciones y concurrencia (~2,5 min)
pytest --cov=domain --cov=application --cov-report=term-missing --cov-fail-under=80   # todo + cobertura
```

Resultado esperado:

- Todo en verde.
- `tests/unit/test_arquitectura.py` sin violaciones de la regla de dependencia.
- En los 30 casos de aceptación, `salvaguarda_activada = false` (SC-001).

### Comprobación de SC-011 (ninguna escritura en la base real)

Antes y después de `pytest`, contar las consultas de la base **real** desde una consola SQL
(Supabase SQL editor o `psql` con `DATABASE_URL`):

```sql
SELECT count(*) FROM consulta;
```

Resultado esperado: el mismo número antes y después.

## Ejecutar la aplicación

```bash
uvicorn api.main:create_app --factory --app-dir src --reload
```

- `GET http://127.0.0.1:8000/salud` → `{"base_conocimiento": "disponible", "reglas": 30}`.
- `http://127.0.0.1:8000/` muestra el formulario con 2 medicamentos, 6 síntomas y 7 condiciones, y
  el aviso de prototipo académico.

## Escenarios de validación manual

Resultados verificados con el prototipo sobre las reglas reales (2026-11-04), aplicando FR-006,
FR-009 y FR-020:

| # | Medicamento | Síntomas | Condiciones | Nivel esperado | Reglas aplicadas (en orden) | Síntomas no cubiertos | Historia / requisito |
|---|-------------|----------|-------------|----------------|-----------------------------|-----------------------|----------------------|
| 1 | Paracetamol | Dolor de cabeza | — | Orientar | R01 | — | US1 |
| 2 | Paracetamol | Dolor de cabeza | Embarazo | Advertir | R10 | — | US1 |
| 3 | Paracetamol | Fiebre | Embarazo | Derivar al médico | R11 | — | US1 |
| 4 | Paracetamol | Fiebre, dolor abdominal | — | Derivar al médico | R13, R05, R02 | — | FR-008, FR-009 |
| 5 | Paracetamol | Dolor de cabeza, fiebre | — | Orientar | R07, R01, R02 | — | FR-009 (regla general y específica) |
| 6 | **Ibuprofeno** | **Dolor de cabeza, fiebre** | — | **Advertir** (sube desde Orientar) | R18 | **Fiebre** | **FR-020, SC-009** |
| 7 | Paracetamol | Fiebre, dolor dental | Embarazo | Derivar al médico (no se rebaja) | R11 | Dolor dental | FR-020 |
| 8 | Ibuprofeno | Fiebre | — | Derivar al médico + mensaje de no cubierta | ninguna | — (no se evalúa) | US2, FR-011 |
| 9 | Paracetamol | Dolor de cabeza | Uso de aspirina | Derivar al médico + mensaje de no cubierta | ninguna (R01 es "sin condiciones") | — | FR-006, Edge Cases |

En cada escenario hay que comprobar:

- El nivel, los mensajes de cada regla (texto idéntico al de `regla_mensaje`) y la lista de
  códigos coinciden con la tabla, en ese orden.
- Escenarios 6 y 7: después de los mensajes de las reglas aparece el bloque "Mensaje del sistema"
  con *"«Fiebre» no tiene orientación específica con Ibuprofeno…"* (o con «Dolor dental» y
  Paracetamol), el distintivo **"Pendiente de aprobación médica"** y, en la explicación,
  "Salvaguarda del sistema (pendiente de aprobación médica): síntomas sin regla aplicable: …". En el JSON:
  `salvaguarda_activada: true`, `sintomas_no_cubiertos` y `mensajes_sistema[].pendiente_aprobacion: true`.
- Con `SALVAGUARDA_PENDIENTE_APROBACION=false` y la aplicación reiniciada, el escenario 6 da el
  mismo nivel y el mismo mensaje, sin el distintivo y con `pendiente_aprobacion: false`.
- Escenarios 8 y 9: solo aparece el mensaje de combinación no cubierta, nunca el de síntoma no
  cubierto.
- Repetir cualquier escenario 10 veces da exactamente el mismo orden de reglas y mensajes
  (SC-010).
- Hay una fila nueva en `consulta` con `nivel_resultado` igual al nivel mostrado (en el escenario
  6, `ADVERTIR`), `sin_regla` correcto, y filas en `consulta_sintoma`, `consulta_condicion` y
  `consulta_regla_disparada` con el mismo `orden`. Ninguna columna contiene datos personales (US3).

## Casos negativos

| Caso | Cómo provocarlo | Esperado |
|------|-----------------|----------|
| Sin síntomas | Enviar el formulario sin marcar síntomas | 422 con el formulario y el error; no se escribe nada en `consulta` |
| Valor fuera de vocabulario | `POST /api/v1/consultas` con `"sintomas": ["SINTOMA_X"]` | 422 con `valores_rechazados: ["SINTOMA_X"]` |
| Base no disponible | Arrancar con `DATABASE_URL` hacia una base sin reglas aprobadas | `/` y `/salud` responden 503 "servicio no disponible" |
| Fallo al registrar | Prueba de integración que hace fallar el `ConsultaRepository` | 200 con el resultado completo, `persistida: false`, cabecera `X-Consulta-Persistida: false` y una entrada `ERROR` en el log sin la cadena de conexión |
| Configuración inválida | `SALVAGUARDA_PENDIENTE_APROBACION=quizas` | La aplicación no arranca y el mensaje de error no muestra ningún secreto |
| Base de pruebas = base real | `TEST_DATABASE_URL` igual a `DATABASE_URL` | `pytest` aborta antes de ejecutar ninguna prueba que use la base |
