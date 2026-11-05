# Contrato de traducción Regla → CLIPS

Lo implementa `infrastructure/inference/traductor_reglas.py`. Es la única parte del sistema,
junto con `fabrica_entorno.py` y `clips_motor_inferencia.py`, que importa `clips` (Principio V).

## Plantillas (se definen una vez por entorno)

```clips
(deftemplate medicamento (slot codigo))
(deftemplate sintoma     (slot codigo))
(deftemplate condicion   (slot codigo))
(deftemplate disparo     (slot regla-id))
```

## Una regla por cada `Regla` cargada

Nombre del constructo: `<codigo>-v<version>`, por ejemplo `R10-v1`. El lado derecho solo afirma
`disparo`; los mensajes **no** se copian a CLIPS, se toman de la entidad `Regla` por `regla-id`.

Regla con condiciones (R10: paracetamol, dolor de cabeza y embarazo, ADVERTIR):

```clips
(defrule R10-v1
  (medicamento (codigo PARACETAMOL))
  (sintoma (codigo DOLOR_CABEZA))
  (condicion (codigo EMBARAZO))
  =>
  (assert (disparo (regla-id 10))))
```

Regla con `sin_condiciones = true` (R07: paracetamol, dolor de cabeza y fiebre):

```clips
(defrule R07-v1
  (medicamento (codigo PARACETAMOL))
  (sintoma (codigo DOLOR_CABEZA))
  (sintoma (codigo FIEBRE))
  (not (condicion))
  =>
  (assert (disparo (regla-id 7))))
```

## Reglas de traducción

1. Un patrón `(medicamento (codigo M))`.
2. Un patrón `(sintoma (codigo S))` por cada síntoma, en orden alfabético para que la salida sea
   determinista.
3. Un patrón `(condicion (codigo C))` por cada condición, también en orden alfabético.
4. Si `sin_condiciones`, se añade `(not (condicion))`.
5. Los códigos deben cumplir `^[A-Z][A-Z0-9_]*$` y `regla-id` debe ser un `int`. Si no, se lanza
   `ValueError`, la carga falla y la base queda "no disponible".
6. No se usa `salience`: el orden de presentación lo fija la estrategia (research D2).

## Evaluación de una consulta

1. `FabricaEntornoClips.crear()` devuelve un `clips.Environment` nuevo, con plantillas y reglas
   ya construidas. `Environment.build()` de clipspy acepta **un solo constructo por llamada**
   (verificado: con varios, lanza `[STRNGFUN2] extraneous input`), así que la fábrica guarda una
   `tuple[str, ...]` de constructos y los construye uno por uno. En el prototipo esto costó
   unos 7,4 ms por consulta con las 30 reglas.
2. Se afirma un hecho `medicamento`, un `sintoma` por cada síntoma y una `condicion` por cada
   condición de `HechosConsulta`.
3. Se ejecuta `env.run()` con un límite de seguridad de 1.000 disparos. Las reglas no se
   encadenan entre sí, así que ninguna consulta se acerca al límite.
4. Se recogen los `regla-id` de los hechos `disparo` y se mapean a `Regla`. El entorno se
   descarta.

## Pruebas unitarias exigidas (Principio VIII)

- Para cada una de las 30 reglas: el texto generado coincide con el patrón esperado, y al
  construirlo en un entorno limpio y afirmar sus hechos exactos, se dispara.
- `sin_condiciones` no se dispara si hay cualquier condición marcada.
- Un código con caracteres no permitidos (`"FIEBRE) (assert"`) lanza `ValueError`.
- Dos entornos creados por la fábrica no comparten hechos.
