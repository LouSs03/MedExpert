# Prueba de usabilidad (SC-004)

**Objetivo (SC-004)**: una persona sin entrenamiento previo completa una consulta, desde abrir el
formulario hasta ver el resultado, en **menos de 1 minuto**.

**Estado**: pendiente. Esta plantilla se completa al realizar la prueba (tarea T078).

## Preparación

- Ejecutar la aplicación con `DATABASE_URL` apuntando a la **base de pruebas**, para que las
  consultas de la prueba no queden en el registro real.
- 2 o 3 personas que no hayan visto el sistema antes. No registrar datos personales: usar
  identificadores como P1, P2 y P3.
- Explicar solo el objetivo ("averigüe si puede tomar este medicamento con estos síntomas") y
  no cómo usar el formulario.
- Cronometrar desde que la persona ve el formulario hasta que aparece el resultado.

## Escenarios

| Escenario | Medicamento | Síntomas | Condiciones | Resultado esperado |
|-----------|-------------|----------|-------------|--------------------|
| 1 | Paracetamol | Dolor de cabeza | — | Orientar (R01) |
| 6 | Ibuprofeno | Dolor de cabeza, fiebre | — | Advertir (R18 + salvaguarda por fiebre) |
| 8 | Ibuprofeno | Fiebre | — | Derivar al médico (combinación no cubierta) |

## Resultados

Fecha de la prueba: ____________

| Persona | Escenario | Tiempo (s) | ¿Completó sin ayuda? | ¿Entendió el resultado? | Observaciones |
|---------|-----------|------------|----------------------|-------------------------|---------------|
| P1 | 1 | | | | |
| P1 | 6 | | | | |
| P1 | 8 | | | | |
| P2 | 1 | | | | |
| P2 | 6 | | | | |
| P2 | 8 | | | | |
| P3 | 1 | | | | |
| P3 | 6 | | | | |
| P3 | 8 | | | | |

## Conclusión

- Consultas por debajo de 1 minuto: __ de __.
- ¿Se cumple SC-004?: ____
- Problemas de comprensión detectados (por ejemplo, el distintivo "Pendiente de aprobación
  médica" o la explicación del razonamiento):
