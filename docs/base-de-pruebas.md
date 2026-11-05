# Base de datos de pruebas (`TEST_DATABASE_URL`)

Las suites `integration`, `aceptacion` y `e2e` se ejecutan **solo** contra una base separada de la
real (FR-021, SC-011). Esta base tiene el mismo esquema y la misma base de conocimiento (las 30
reglas), pero **ninguna consulta real**. `tests/conftest.py` aborta la ejecución si
`TEST_DATABASE_URL` apunta a la misma base que `DATABASE_URL`.

## 1. Elegir dónde crearla

Cualquiera de estas opciones sirve, porque los adaptadores dependen de PostgreSQL y no del
proveedor:

- **Un proyecto nuevo de Supabase** (gratuito), dedicado a pruebas.
- **Un branch de Supabase** del proyecto real, si tu plan lo permite.
- **PostgreSQL local** (versión igual o superior a la del proyecto real), por ejemplo con Docker:
  `docker run --name medexpert-pruebas -e POSTGRES_PASSWORD=<clave> -p 5433:5432 -d postgres:17`.

## 2. Copiar el esquema y la base de conocimiento

Se necesitan las herramientas cliente de PostgreSQL (`pg_dump` y `psql`), en una versión igual o
superior a la del servidor de origen.

En una terminal, define las dos URL **solo en esa sesión**, sin guardarlas en el historial ni en
archivos versionados. Usa el formato de libpq (`postgresql://`, sin `+psycopg`):

```bash
export ORIGEN='postgresql://<usuario>:<clave>@aws-0-us-east-1.pooler.supabase.com:5432/postgres'
export DESTINO='postgresql://<usuario>:<clave>@<host-de-pruebas>:<puerto>/postgres'
```

(En PowerShell: `$env:ORIGEN = '...'` y `$env:DESTINO = '...'`.)

**Esquema** (solo `public`; incluye las claves, las restricciones y `ENABLE ROW LEVEL SECURITY`):

```bash
pg_dump "$ORIGEN" --schema-only --schema=public --no-owner --no-privileges -f esquema.sql
psql "$DESTINO" -v ON_ERROR_STOP=1 -f esquema.sql
```

**Datos**: solo las 7 tablas de la base de conocimiento, **nunca** `consulta` ni sus tablas hijas:

```bash
pg_dump "$ORIGEN" --data-only --no-owner \
  -t public.medicamento -t public.sintoma -t public.condicion \
  -t public.regla -t public.regla_sintoma -t public.regla_condicion -t public.regla_mensaje \
  -f conocimiento.sql
psql "$DESTINO" -v ON_ERROR_STOP=1 -f conocimiento.sql
```

Si `psql` falla por una clave foránea, restaura las tablas una a una en este orden: `medicamento`,
`sintoma`, `condicion`, `regla`, `regla_sintoma`, `regla_condicion`, `regla_mensaje`.

Después borra `esquema.sql` y `conocimiento.sql`: no deben versionarse.

## 3. Verificar

Ejecuta en la base de **pruebas**:

```sql
-- 30 reglas aprobadas, 6 síntomas, 7 condiciones, 2 medicamentos
SELECT count(*) FROM regla WHERE estado = 'aprobada';                      -- 30
SELECT count(*) FROM sintoma;                                               -- 6
SELECT count(*) FROM condicion;                                             -- 7
SELECT count(*) FROM medicamento;                                           -- 2

-- Ninguna consulta copiada
SELECT count(*) FROM consulta;                                              -- 0

-- RLS activo en todas las tablas de public (Principio X): no debe devolver filas
SELECT c.relname
FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'public' AND c.relkind = 'r' AND NOT c.relrowsecurity;
```

## 4. Definir `TEST_DATABASE_URL`

Añádela a `.env`, que nunca se versiona, con el formato que usa la aplicación (`postgresql+psycopg://`):

```text
TEST_DATABASE_URL=postgresql+psycopg://<usuario>:<clave>@<host-de-pruebas>:<puerto>/postgres
```

Debe ser **distinta** de `DATABASE_URL`: si coinciden el host, el puerto y el nombre de la base,
`pytest` aborta antes de ejecutar cualquier prueba que use la base.

## 5. Mantenerla al día

Cuando se apruebe una regla nueva o una versión nueva de una regla en la base real, repite el paso
2 (o copia solo las filas nuevas) y vuelve a ejecutar la suite completa de aceptación
(Principio XI).
