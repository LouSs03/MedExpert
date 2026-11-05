# Contrato de puertos (application/ports y domain), rev. 2

Firmas de referencia. Los puertos son `typing.Protocol`. Ningún archivo de este contrato importa
librerías externas (Principio IV).

```python
# application/ports/regla_repository.py
class ReglaRepository(Protocol):
    def obtener_vocabulario(self) -> Vocabulario:
        """Devuelve los catálogos de medicamentos, síntomas y condiciones."""
    def listar_reglas_aprobadas_vigentes(self) -> Sequence[Regla]:
        """Devuelve la versión más reciente en estado aprobada de cada regla."""

# application/ports/consulta_repository.py
class ConsultaRepository(Protocol):
    def guardar(self, consulta: Consulta) -> UUID:
        """Persiste la consulta completa de forma atómica y devuelve su identificador."""

# application/ports/motor_inferencia.py
class MotorInferencia(Protocol):
    def evaluar(self, hechos: HechosConsulta) -> Sequence[Regla]:
        """Devuelve las reglas de la base cargada cuyas condiciones satisfacen los hechos."""

# domain/resolucion_nivel.py
class EstrategiaResolucionNivel(Protocol):
    def resolver(self, hechos: HechosConsulta, disparadas: Sequence[Regla]) -> Resolucion:
        """Devuelve el nivel final, las reglas ordenadas y los síntomas no cubiertos."""
```

`Resolucion`, `MensajeSistema` y `ConfiguracionSalvaguarda` se definen en
[data-model.md](../data-model.md).

## Implementaciones

| Puerto | Producción | Pruebas |
|--------|------------|---------|
| `ReglaRepository` | `infrastructure/db/postgres_regla_repository.py` → `PostgresReglaRepository` | `tests/fakes/ReglaRepositoryEnMemoria` |
| `ConsultaRepository` | `infrastructure/db/postgres_consulta_repository.py` → `PostgresConsultaRepository` | `tests/fakes/ConsultaRepositoryEnMemoria` (con opción `fallar=True`) |
| `MotorInferencia` | `infrastructure/inference/clips_motor_inferencia.py` → `ClipsMotorInferencia` | `tests/fakes/FakeMotorInferencia` (devuelve reglas preconfiguradas) |
| `EstrategiaResolucionNivel` | `domain/resolucion_nivel.py` → `ResolucionPorSeveridad` (incluye la salvaguarda de cobertura, no desactivable) | — |

Los adaptadores `Postgres*Repository` solo dependen de PostgreSQL vía SQLModel/SQLAlchemy, no de
ninguna API propia de Supabase (research D15). Funcionan igual contra la base de producción y la
de pruebas.

`FakeMotorInferencia` vive en `tests/fakes/`, porque el código de producción no lo necesita. El
Principio V exige que exista, no que se despliegue.

## Casos de uso

```python
class CargarBaseConocimiento:
    def __init__(self, repositorio: ReglaRepository) -> None: ...
    def ejecutar(self) -> BaseConocimiento:
        """Carga y valida la base de conocimiento; lanza BaseConocimientoNoDisponible."""

class EvaluarConsulta:
    def __init__(self, vocabulario: Vocabulario, motor: MotorInferencia,
                 estrategia: EstrategiaResolucionNivel, consultas: ConsultaRepository,
                 salvaguarda: ConfiguracionSalvaguarda) -> None: ...
    def ejecutar(self, medicamento: str, sintomas: Sequence[str],
                 condiciones: Sequence[str]) -> ResultadoEvaluacion:
        """Valida, evalúa, resuelve el nivel y registra la consulta; lanza VocabularioInvalido."""
```

Flujo de `EvaluarConsulta.ejecutar`:

1. Valida con `vocabulario.validar(...)` y obtiene `HechosConsulta`.
2. Obtiene las reglas disparadas con `motor.evaluar(hechos)`.
3. Resuelve con `estrategia.resolver(hechos, disparadas)` y obtiene `Resolucion` (nivel, orden y
   síntomas no cubiertos).
4. Construye los `mensajes_sistema`: `COMBINACION_NO_CUBIERTA` si `sin_regla`; si no, un
   `SINTOMA_NO_CUBIERTO` por cada síntoma no cubierto, con
   `pendiente_aprobacion = salvaguarda.pendiente_aprobacion`.
5. Construye `Consulta` (con el nivel ya resuelto) y llama a `consultas.guardar(...)`. Si lanza
   una excepción: `logger.error` saneado y `persistida=False`.
6. Devuelve `ResultadoEvaluacion`.

## Composición (api/dependencias.py)

El `lifespan` crea una sola vez y guarda en `app.state`: la `BaseConocimiento` (con
`PostgresReglaRepository`), `FabricaEntornoClips(base.reglas)`, `ClipsMotorInferencia(fabrica)`,
`ResolucionPorSeveridad()` y la `ConfiguracionSalvaguarda` leída por `infrastructure/config.py`.
`get_evaluar_consulta(request, session=Depends(get_session))` arma `EvaluarConsulta` en cada
request con un `PostgresConsultaRepository(session)`. Los routers solo reciben el caso de uso con
`Depends`.
