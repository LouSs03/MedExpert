# Contrato HTTP (rev. 2)

Todas las respuestas HTML heredan de `base.html`, que contiene el aviso de prototipo académico
(FR-013). Las entidades de dominio nunca se serializan directamente; solo se exponen los DTOs de
abajo (Principio V).

## Rutas

| Método | Ruta | Entrada | Éxito | Errores |
|--------|------|---------|-------|---------|
| GET | `/` | — | 200, HTML con el formulario generado desde el `Vocabulario` | 503, HTML "servicio no disponible" (FR-018) |
| POST | `/consulta` | `application/x-www-form-urlencoded` (campos abajo) | 200, HTML con el resultado | 422, HTML del formulario con errores y los valores marcados; 503 |
| POST | `/api/v1/consultas` | JSON `ConsultaEntradaDTO` | 200, JSON `ResultadoDTO` | 422, JSON `ErrorValidacionDTO`; 503, JSON `{"detalle": "..."}` |
| GET | `/salud` | — | 200 `{"base_conocimiento": "disponible", "reglas": 30}` | 503 `{"base_conocimiento": "no_disponible"}` |

Las respuestas de `POST /consulta` y `POST /api/v1/consultas` incluyen siempre la cabecera
`X-Consulta-Persistida: true|false` (marca interna, FR-019).

## Campos del formulario (`POST /consulta`)

| Campo | Repetible | Valores |
|-------|-----------|---------|
| `medicamento` | no (radio) | códigos de `medicamento` |
| `sintomas` | sí (checkbox) | códigos de `sintoma` |
| `condiciones` | sí (checkbox) | códigos de `condicion` |

## DTOs (Pydantic)

### ConsultaEntradaDTO

```json
{
  "medicamento": "IBUPROFENO",
  "sintomas": ["DOLOR_CABEZA", "FIEBRE"],
  "condiciones": []
}
```

- `medicamento`: `str`, obligatorio.
- `sintomas`: `list[str]`, `min_length=1`, se eliminan duplicados.
- `condiciones`: `list[str]`, por defecto `[]`, se eliminan duplicados.
- La pertenencia al vocabulario **no** se comprueba en el DTO, sino en `Vocabulario.validar`.
  Si falla, se responde 422 con `valores_rechazados`.

### ResultadoDTO

Ejemplo con salvaguarda activada (ibuprofeno con dolor de cabeza y fiebre; verificado contra las
reglas reales):

```json
{
  "nivel": "ADVERTIR",
  "nivel_etiqueta": "Advertir",
  "sin_regla": false,
  "reglas_aplicadas": [
    {
      "codigo": "R18",
      "version": 1,
      "nivel": "ORIENTAR",
      "especificidad": 1,
      "mensajes": ["<texto aprobado de R18>"]
    }
  ],
  "salvaguarda_activada": true,
  "sintomas_no_cubiertos": [{"codigo": "FIEBRE", "nombre": "Fiebre"}],
  "mensajes_sistema": [
    {
      "tipo": "SINTOMA_NO_CUBIERTO",
      "texto": "«Fiebre» no tiene orientación específica con Ibuprofeno en la base de conocimiento validada. Consulte a un médico o farmacéutico.",
      "pendiente_aprobacion": true,
      "sintoma": "FIEBRE"
    }
  ],
  "persistida": true,
  "aviso": "Prototipo académico: no reemplaza la consulta médica o farmacéutica."
}
```

Reglas del DTO:

| Campo | Tipo | Regla |
|-------|------|-------|
| `nivel` | `"ORIENTAR" \| "ADVERTIR" \| "DERIVAR"` | Ya elevado por la salvaguarda si correspondía |
| `nivel_etiqueta` | `str` | "Orientar" · "Advertir" · "Derivar al médico" |
| `sin_regla` | `bool` | |
| `reglas_aplicadas` | `list[ReglaAplicadaDTO]` | Orden FR-009; cada una con sus `mensajes` aprobados en orden; `[]` si `sin_regla` |
| `salvaguarda_activada` | `bool` | `true` si `sintomas_no_cubiertos` no está vacío |
| `sintomas_no_cubiertos` | `list[{codigo, nombre}]` | Orden por `id` del síntoma; `[]` si `sin_regla` |
| `mensajes_sistema` | `list[MensajeSistemaDTO]` | Ver los casos abajo |
| `persistida` | `bool` | `false` no cambia ningún otro campo |
| `aviso` | `str` | Constante |

`MensajeSistemaDTO`: `tipo` (`"COMBINACION_NO_CUBIERTA" | "SINTOMA_NO_CUBIERTO"`), `texto`,
`pendiente_aprobacion` (`bool`), `sintoma` (`str | null`).

Casos de `mensajes_sistema`:

| Caso | Contenido |
|------|-----------|
| `sin_regla = true` | Exactamente `[{"tipo": "COMBINACION_NO_CUBIERTA", "pendiente_aprobacion": false, "sintoma": null, ...}]`; `nivel = "DERIVAR"` |
| Reglas disparadas y todo cubierto | `[]` |
| Reglas disparadas y síntomas no cubiertos | Un `SINTOMA_NO_CUBIERTO` por síntoma, en el orden de `sintomas_no_cubiertos`, con `pendiente_aprobacion` igual a la configuración `SALVAGUARDA_PENDIENTE_APROBACION` |

Los dos tipos nunca aparecen juntos.

### ErrorValidacionDTO

```json
{"detalle": "La consulta contiene valores no reconocidos.", "valores_rechazados": ["SINTOMA_X"]}
```

## Presentación HTML del resultado

- Un contenedor `<section id="resultado" data-nivel="ADVERTIR" data-consulta-persistida="true"
  data-salvaguarda="true">`.
- La etiqueta del nivel es visible y destaca más que los mensajes.
- Los mensajes de las reglas se muestran en el orden de `reglas_aplicadas`, agrupados por regla.
- **Después** de los mensajes de las reglas va un bloque `<aside id="mensajes-sistema">` con los
  mensajes del sistema, con el encabezado "Mensaje del sistema (no proviene de una regla
  validada)". Si `pendiente_aprobacion` es `true`, se añade el distintivo visible
  "Pendiente de aprobación médica" (Principio I (c)).
- La explicación va en `id="explicacion"`: "Reglas aplicadas: R18" (o "Ninguna regla aplicada")
  y, si se activó la salvaguarda, "Salvaguarda del sistema (pendiente de aprobación médica):
  síntomas sin regla aplicable: Fiebre" (FR-010). El paréntesis aparece solo mientras
  `pendiente_aprobacion` sea `true`.
- La marca de no persistida se transmite **solo** con el atributo `data-` y la cabecera; no se
  muestra ningún texto al usuario por ese motivo.
