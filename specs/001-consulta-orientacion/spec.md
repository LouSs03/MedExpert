# Feature Specification: Consulta de orientación sobre automedicación

**Feature Branch**: `001-consulta-orientacion`

**Created**: 2026-11-04

**Status**: Draft

**Input**: User description: "Primera funcionalidad: consulta de orientación sobre automedicación.
El usuario selecciona un medicamento (paracetamol o ibuprofeno), marca uno o más síntomas de una
lista cerrada (dolor de cabeza, fiebre, molestias respiratorias, dolor muscular o de espalda, dolor
abdominal o gástrico, dolor dental) y marca cero o más condiciones (embarazo, diabetes,
hipertensión, adulto mayor de 60 años o más, uso de otro tratamiento, uso de antigripal, uso de
aspirina). El sistema evalúa esos hechos contra la base de conocimiento mediante encadenamiento
hacia adelante con CLIPS y devuelve: el nivel resultante (Orientar, Advertir o Derivar al médico),
los mensajes de las reglas que se dispararon, y la lista de códigos de regla aplicados como
explicación del razonamiento. Si ninguna regla aplica, el sistema responde con nivel Derivar al
médico y un mensaje indicando que esa combinación no está cubierta por la base de conocimiento
validada. Cada consulta se guarda con sus hechos de entrada, el nivel resultante y las reglas
disparadas, sin ningún dato personal. Fuera de alcance en esta funcionalidad: autenticación de
usuarios, panel de administración de reglas, y medicamentos distintos a paracetamol e ibuprofeno.
Contexto importante: esta es la primera funcionalidad del repositorio, que está vacío salvo por la
configuración de Spec Kit. El plan debe incluir la creación de la estructura de carpetas de la
arquitectura hexagonal definida en el Principio IV, la conexión a PostgreSQL mediante la variable
de entorno DATABASE_URL, el arranque de FastAPI con una interfaz de formulario en Jinja2, y la
configuración de pytest, ruff y mypy. Las tablas y las 30 reglas ya existen en la base de datos;
el sistema solo las lee, no las crea."

## Clarifications

### Session 2026-11-04

- Q: ¿Qué debe hacer el sistema si una consulta ya evaluada no puede registrarse? → A: Muestra
  igualmente el resultado (excepción por fallo técnico del Principio III); registra el fallo en el log de
  la aplicación con el detalle del error, y la respuesta incluye una marca interna de que esa
  consulta no pudo persistirse.
- Q: ¿Cuándo se dispara una regla si la persona marca más hechos de los que la regla pide? → A: Una
  regla se dispara solo si todos sus síntomas y condiciones están presentes en la consulta; los
  hechos adicionales no la bloquean. La marca "sin condiciones" de una regla significa "ninguna
  condición marcada": esa regla no se dispara si la persona marcó cualquier condición.
- Q: ¿Qué se muestra cuando se disparan varias reglas a la vez? → A: Todas, ordenadas por nivel más
  severo, luego por especificidad (más síntomas y condiciones primero) y luego por código.
- Q: ¿Qué ocurre si algún síntoma marcado no aparece en ninguna regla disparada? → A: Salvaguarda
  de cobertura (Principio I): el nivel resultante es como mínimo Advertir, y por cada síntoma no
  cubierto se muestra un mensaje genérico del sistema que indica que ese síntoma no tiene
  orientación específica con ese medicamento y que consulte a un médico o farmacéutico. Ese mensaje
  no es una regla de la base: lo define el sistema y queda marcado como pendiente de aprobación del
  médico. No altera los 30 casos de aceptación.
- Q: ¿Contra qué base de datos se ejecutan las pruebas de integración y de punta a punta? → A:
  Contra una base separada (`TEST_DATABASE_URL`), nunca contra la base real.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Obtener orientación para una combinación cubierta (Priority: P1)

Una persona que está pensando en automedicarse entra al sistema, elige el medicamento que piensa
tomar (paracetamol o ibuprofeno), marca los síntomas que tiene y las condiciones que le aplican, y
envía la consulta. El sistema le muestra el nivel de orientación (Orientar, Advertir o Derivar al
médico), los mensajes aprobados por el médico especialista para su caso y los códigos de las reglas
que llevaron a esa conclusión.

**Why this priority**: es el propósito central del sistema experto. Sin este flujo no hay producto
que mostrar ni validar en la tesis.

**Independent Test**: se envía una combinación de hechos que coincide exactamente con una regla
aprobada (por ejemplo, la de R01) y se verifica que el resultado muestre el nivel, los mensajes y el
código aprobados para esa regla.

**Acceptance Scenarios**:

1. **Given** la base de conocimiento con sus reglas aprobadas está disponible, **When** la persona
   elige un medicamento, marca al menos un síntoma y envía una combinación que coincide con una
   regla aprobada, **Then** el sistema muestra el nivel de esa regla, su mensaje exacto y su código.
2. **Given** una combinación que dispara varias reglas con niveles distintos, **When** la persona
   envía la consulta, **Then** el nivel mostrado es el más severo entre los disparados
   (Derivar al médico > Advertir > Orientar), y se muestran los mensajes y códigos de todas las
   reglas disparadas, ordenados por nivel más severo, luego por especificidad y luego por código.
3. **Given** una combinación en la que se dispara al menos una regla pero algún síntoma marcado no
   aparece en ninguna de ellas (por ejemplo, ibuprofeno con dolor de cabeza y fiebre, donde solo se
   dispara la regla del dolor de cabeza), **When** la persona envía la consulta, **Then** el nivel es
   como mínimo Advertir, se muestran los mensajes de las reglas disparadas y, además, un mensaje del
   sistema por cada síntoma no cubierto que recomienda consultar a un médico o farmacéutico.
4. **Given** cualquier pantalla del sistema, **When** la persona la visualiza, **Then** ve un aviso
   de que se trata de un prototipo académico que no reemplaza la consulta médica o farmacéutica.

---

### User Story 2 - Respuesta segura ante una combinación no cubierta (Priority: P2)

La persona envía una combinación de medicamento, síntomas y condiciones para la que no existe
ninguna regla aprobada. En lugar de improvisar una recomendación, el sistema le indica que acuda al
médico y le explica que esa combinación no está cubierta por la base de conocimiento validada.

**Why this priority**: garantiza la seguridad del paciente (Principio I). Es imprescindible antes de
exponer el sistema a cualquier usuario, pero depende de que exista el flujo de consulta de la
historia 1.

**Independent Test**: se envía una combinación que ninguna regla aprobada cubre y se verifica que
el nivel sea "Derivar al médico", que aparezca el mensaje de combinación no cubierta y que la lista
de reglas aplicadas esté vacía.

**Acceptance Scenarios**:

1. **Given** una combinación de hechos que no satisface ninguna regla aprobada, **When** la persona
   envía la consulta, **Then** el sistema muestra el nivel "Derivar al médico" y un mensaje que
   indica que esa combinación no está cubierta por la base de conocimiento validada.
2. **Given** ese mismo caso, **When** se muestra el resultado, **Then** no aparece ninguna
   recomendación, dosis ni mensaje que no provenga de una regla aprobada, y la explicación indica
   que no se aplicó ninguna regla.

---

### User Story 3 - Registro trazable de cada consulta (Priority: P3)

Cada consulta que el sistema responde queda registrada con los hechos de entrada, el nivel
resultante y las reglas disparadas, sin ningún dato que identifique a la persona. Esto permite al
equipo de la tesis y al médico especialista auditar cómo razonó el sistema en cada caso.

**Why this priority**: es exigido por el Principio III y necesario para la validación académica,
pero no cambia lo que ve la persona usuaria en el momento de la consulta.

**Independent Test**: se realiza una consulta y se verifica que exista un registro con exactamente
el medicamento, los síntomas, las condiciones, el nivel y los códigos de regla mostrados, y que el
registro no contenga ningún campo de dato personal.

**Acceptance Scenarios**:

1. **Given** una consulta respondida (cubierta o no cubierta), **When** se revisa el registro de
   consultas, **Then** existe una entrada con sus hechos de entrada, el nivel resultante, los
   códigos y versiones de las reglas disparadas y la fecha y hora de la consulta.
2. **Given** cualquier entrada del registro, **When** se inspecciona, **Then** no contiene nombre,
   documento de identidad, correo, teléfono, dirección ni ningún otro dato personal identificable.
3. **Given** que el registro de consultas falla al guardar una consulta ya evaluada, **When** se
   responde a la persona, **Then** se le muestra el resultado completo, el log de la aplicación
   contiene el detalle del error y la respuesta lleva la marca interna de consulta no persistida.

---

### Edge Cases

- **Ningún síntoma marcado**: el sistema no evalúa la consulta y pide marcar al menos un síntoma.
- **Ningún medicamento elegido o más de uno**: el sistema no evalúa la consulta y pide elegir
  exactamente un medicamento.
- **Valores fuera de las listas cerradas** (por ejemplo, una solicitud manipulada con un síntoma o
  medicamento inexistente): el sistema rechaza la consulta sin evaluarla y sin registrarla como
  consulta respondida.
- **Varias reglas disparadas con distinto nivel**: se aplica el nivel más severo y se muestran todos
  los mensajes y códigos disparados, sin duplicados, ordenados por nivel más severo, luego por
  especificidad y luego por código.
- **Una regla general y otra más específica a la vez** (por ejemplo, paracetamol con dolor de cabeza
  y fiebre: se disparan la regla de dolor de cabeza, la de fiebre y la de ambos): se muestran las
  tres; la más específica aparece primero dentro de su nivel.
- **Hechos adicionales a los de una regla**: no impiden que la regla se dispare, salvo que la regla
  sea "sin condiciones" y la persona haya marcado alguna condición.
- **Síntoma marcado que ninguna regla disparada cubre**: se aplica la salvaguarda de cobertura; el
  nivel sube a Advertir si era Orientar (si ya era Advertir o Derivar al médico, se mantiene) y se
  añade un mensaje del sistema por cada síntoma no cubierto.
- **Ninguna regla disparada**: se aplica FR-011 (Derivar al médico y mensaje de combinación no
  cubierta), no la salvaguarda de cobertura; los dos mensajes del sistema nunca aparecen juntos.
- **Reglas en estado pendiente o versiones anteriores**: nunca participan en la evaluación, aunque
  sus condiciones coincidan con los hechos.
- **Base de conocimiento no disponible o sin reglas aprobadas al iniciar**: el sistema no ofrece
  evaluaciones y muestra un aviso de servicio no disponible, en lugar de responder "Derivar al
  médico" a todo.
- **Falla al registrar la consulta**: el sistema muestra igualmente el resultado, porque negar una
  orientación de seguridad por un fallo técnico contradice el Principio I; el fallo queda en el log
  de la aplicación y la respuesta lleva la marca interna de consulta no persistida.
- **Consultas simultáneas de distintas personas**: los hechos de una consulta nunca influyen en el
  resultado de otra.
- **Condiciones aparentemente irrelevantes para el medicamento elegido** (por ejemplo, uso de
  aspirina con paracetamol): se evalúan igual. Marcarlas impide que se disparen las reglas "sin
  condiciones"; si por eso no queda ninguna regla aplicable, el resultado es Derivar al médico
  (FR-011).
- **Pruebas automatizadas**: nunca escriben ni leen en la base real de consultas; usan una base
  separada con la misma base de conocimiento.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema DEBE presentar un formulario con exactamente estas opciones: medicamentos
  (paracetamol, ibuprofeno); síntomas (dolor de cabeza, fiebre, molestias respiratorias, dolor
  muscular o de espalda, dolor abdominal o gástrico, dolor dental); condiciones (embarazo, diabetes,
  hipertensión, adulto mayor de 60 años o más, uso de otro tratamiento, uso de antigripal, uso de
  aspirina).
- **FR-002**: El sistema DEBE exigir que se elija exactamente un medicamento por consulta.
- **FR-003**: El sistema DEBE exigir que se marque al menos un síntoma.
- **FR-004**: El sistema DEBE permitir marcar cero o más condiciones.
- **FR-005**: El sistema DEBE rechazar, sin evaluar, cualquier consulta que contenga valores fuera
  de las listas cerradas de FR-001, e informar a la persona qué debe corregir.
- **FR-006**: El sistema DEBE evaluar los hechos de la consulta mediante encadenamiento hacia
  adelante, usando únicamente las reglas en estado aprobada y, de cada una, solo su versión más
  reciente. Una regla se dispara si y solo si: el medicamento de la consulta es el de la regla;
  todos los síntomas de la regla están marcados; todas las condiciones de la regla están marcadas;
  y, si la regla es "sin condiciones", no hay ninguna condición marcada. Los hechos adicionales no
  impiden el disparo.
- **FR-007**: El sistema DEBE devolver un único nivel resultante, que es uno de: Orientar,
  Advertir o Derivar al médico.
- **FR-008**: Cuando se disparan varias reglas, el nivel resultante DEBE ser el más severo entre
  ellas, según el orden Derivar al médico > Advertir > Orientar, sujeto al mínimo que impone
  FR-020.
- **FR-009**: El sistema DEBE mostrar los mensajes de todas las reglas disparadas, tal como fueron
  aprobados, sin alterarlos, resumirlos ni completarlos, ordenados por nivel de la regla (más severo
  primero), luego por especificidad (mayor número de síntomas y condiciones primero) y luego por
  código ascendente. El mismo orden se aplica a la lista de códigos y al registro de la consulta.
- **FR-010**: El sistema DEBE mostrar, como explicación del razonamiento, la lista de códigos de las
  reglas disparadas (R01–R30 o los códigos que se aprueben después) y, si se activó la salvaguarda
  de FR-020, los síntomas no cubiertos, identificándola como salvaguarda del sistema y no como regla
  de la base.
- **FR-011**: Si ninguna regla se dispara, el sistema DEBE devolver el nivel "Derivar al médico", un
  mensaje que indique que la combinación no está cubierta por la base de conocimiento validada y una
  lista de reglas aplicadas vacía.
- **FR-012**: El sistema NO DEBE mostrar ninguna recomendación, dosis ni mensaje clínico que no
  provenga de una regla aprobada, salvo dos mensajes del sistema: el de combinación no cubierta
  (FR-011) y el de síntoma no cubierto (FR-020). Ambos solo remiten a un profesional y no
  contienen recomendaciones de uso.
- **FR-013**: Toda pantalla DEBE mostrar un aviso visible de que el sistema es un prototipo
  académico que no reemplaza la consulta médica o farmacéutica.
- **FR-014**: El sistema DEBE registrar cada consulta respondida con: medicamento, síntomas,
  condiciones, nivel resultante, códigos y versiones de las reglas disparadas, y fecha y hora.
- **FR-015**: El sistema NO DEBE solicitar ni almacenar ningún dato personal identificable.
- **FR-016**: Cada consulta DEBE evaluarse de forma aislada; los hechos de una consulta no pueden
  afectar el resultado de otra, incluso si ocurren al mismo tiempo.
- **FR-017**: El sistema DEBE tratar la base de conocimiento como de solo lectura: no crea,
  modifica ni elimina reglas.
- **FR-018**: Si al iniciar no puede cargarse la base de conocimiento o no contiene reglas
  aprobadas, el sistema NO DEBE ofrecer evaluaciones y DEBE mostrar un aviso de servicio no
  disponible.
- **FR-019**: Si una consulta ya evaluada no puede registrarse, el sistema DEBE mostrar igualmente
  su resultado completo a la persona, DEBE registrar el fallo en el log de la aplicación con el
  detalle del error (sin credenciales ni cadenas de conexión, según el Principio X) y la respuesta
  DEBE incluir una marca interna que indique que esa consulta no pudo persistirse. La marca no se
  presenta como mensaje clínico ni altera el nivel, los mensajes o los códigos mostrados.
- **FR-020**: Salvaguarda de cobertura. Si se disparó al menos una regla y algún síntoma marcado no
  aparece entre los síntomas de ninguna regla disparada, el sistema DEBE (a) elevar el nivel
  resultante a Advertir cuando el nivel de las reglas sea Orientar, sin rebajarlo nunca si ya es
  Advertir o Derivar al médico; y (b) mostrar, después de los mensajes de las reglas, un mensaje del
  sistema por cada síntoma no cubierto, que nombre el síntoma y el medicamento, indique que no tiene
  orientación específica y recomiende consultar a un médico o farmacéutico. El texto de ese mensaje
  lo define el sistema, no forma parte de la base de conocimiento y DEBE quedar identificado como
  pendiente de aprobación del médico especialista hasta que este lo valide. Texto literal, donde
  `{sintoma.nombre}` y `{medicamento.nombre}` son los nombres visibles del síntoma y del
  medicamento: *"«{sintoma.nombre}» no tiene orientación específica con {medicamento.nombre} en la
  base de conocimiento validada. Consulte a un médico o farmacéutico."*
- **FR-021**: Las pruebas automatizadas de integración y de punta a punta DEBEN ejecutarse contra
  una base de datos separada de la real, con el mismo esquema y la misma base de conocimiento;
  nunca DEBEN leer ni escribir en la base real de consultas.

### Key Entities *(include if feature involves data)*

- **Medicamento**: el fármaco que la persona piensa tomar. Valores posibles en esta funcionalidad:
  paracetamol, ibuprofeno.
- **Síntoma**: malestar declarado por la persona, de una lista cerrada de seis valores.
- **Condición**: circunstancia de la persona que puede modificar la orientación (embarazo,
  enfermedades crónicas, edad, otros tratamientos o fármacos), de una lista cerrada de siete valores.
- **Hecho**: cada dato de entrada de una consulta (el medicamento, cada síntoma y cada condición)
  sobre el que razonan las reglas.
- **Regla**: conocimiento validado por el médico especialista. Tiene un código (R01–R30), una
  versión, un estado (pendiente, aprobada o rechazada), las condiciones sobre hechos que la disparan, el nivel
  que asigna y el mensaje que muestra.
- **Nivel**: grado de orientación del resultado: Orientar, Advertir o Derivar al médico, ordenados
  de menor a mayor severidad.
- **Consulta**: registro anónimo de una evaluación: sus hechos de entrada, el nivel resultante, las
  reglas disparadas (código y versión) y la fecha y hora.
- **Resultado**: lo que se muestra a la persona: nivel, mensajes de las reglas disparadas en el orden
  de FR-009, lista de códigos aplicados y, si corresponde, los mensajes del sistema (combinación no
  cubierta o síntoma no cubierto).
- **Mensaje del sistema**: texto que no proviene de una regla de la base y que solo remite a un
  profesional. Hay dos tipos: combinación no cubierta (FR-011) y síntoma no cubierto (FR-020); este
  último está pendiente de aprobación del médico especialista.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Para el 100% de las 30 reglas aprobadas, una consulta con los hechos exactos de la
  regla devuelve el nivel y los mensajes aprobados para ella, y en ninguno de esos 30 casos se
  activa la salvaguarda de cobertura.
- **SC-002**: El 100% de las combinaciones no cubiertas por ninguna regla aprobada devuelven
  "Derivar al médico" con el mensaje de combinación no cubierta.
- **SC-003**: El 0% de los resultados mostrados contiene un mensaje sin código de regla aprobada que
  lo respalde, excepto los dos mensajes del sistema de FR-011 y FR-020.
- **SC-004**: Una persona sin entrenamiento previo completa una consulta, desde abrir el formulario
  hasta ver el resultado, en menos de 1 minuto.
- **SC-005**: El resultado aparece en menos de 2 segundos después de enviar la consulta.
- **SC-006**: El 100% de las consultas respondidas quedan registradas con sus hechos, nivel y
  reglas disparadas o, si el registro falla, tienen una entrada de error en el log y la marca de
  consulta no persistida en su respuesta; el 0% de los registros contiene datos personales.
- **SC-007**: El 100% de las pantallas muestran el aviso de prototipo académico.
- **SC-008**: Con 20 consultas simultáneas distintas, cada una obtiene exactamente el mismo
  resultado que obtendría si se enviara sola.
- **SC-009**: En el 100% de las consultas en que algún síntoma marcado no queda cubierto por las
  reglas disparadas, el nivel resultante es Advertir o Derivar al médico y aparece un mensaje de
  síntoma no cubierto por cada síntoma afectado; el 0% de esas consultas termina en Orientar.
- **SC-010**: Para la misma combinación de hechos, el orden de mensajes y códigos mostrado es
  idéntico en el 100% de las repeticiones.
- **SC-011**: Tras ejecutar la suite completa de pruebas, la base real de consultas no contiene
  ningún registro nuevo (0 registros creados por pruebas).

## Assumptions

- Las personas usuarias son público general en Perú, leen español y usan el sistema de forma
  anónima, sin crear cuenta ni iniciar sesión.
- La base de conocimiento con las 30 reglas aprobadas (R01–R30) y las estructuras de datos
  necesarias, incluida la del registro de consultas, ya existen. Esta funcionalidad lee las reglas y
  solo escribe registros de consulta; no crea estructuras ni reglas.
- Los valores de las listas cerradas de medicamentos, síntomas y condiciones coinciden con el
  vocabulario que usan las reglas almacenadas.
- "Adulto mayor de 60 años o más" se declara como una condición marcada por la persona; el sistema
  no pide la edad.
- Los mensajes de las reglas ya están redactados en español y aprobados por el médico especialista.
- El resultado es informativo: el sistema no indica dosis, frecuencias ni duración de tratamiento,
  salvo que ese contenido forme parte literal de un mensaje aprobado.
- Si el registro de una consulta falla, se prefiere mostrar el resultado aunque quede sin
  persistir, conforme a la excepción por fallo técnico del Principio III, y el fallo queda
  documentado en el log.
- La activación de la salvaguarda de cobertura no necesita un dato nuevo en el registro: se puede
  reconstruir a partir de los síntomas registrados y las versiones de las reglas disparadas. El
  registro guarda el nivel ya elevado.
- El texto del mensaje de síntoma no cubierto es provisional mientras el médico especialista no lo
  apruebe; su aprobación queda fuera de esta funcionalidad, y su identificación como "pendiente de
  aprobación" se mantiene visible en la explicación del resultado hasta entonces.
- La salvaguarda de cobertura se aplica solo a síntomas; las condiciones marcadas que ninguna regla
  disparada considera no la activan.
- Fuera de alcance: autenticación de usuarios, panel de administración de reglas, medicamentos
  distintos de paracetamol e ibuprofeno, y consulta del historial de consultas por parte de las
  personas usuarias.
- El contexto técnico indicado en la descripción (estructura hexagonal, conexión a la base de datos
  por variable de entorno, servidor web con formulario y herramientas de pruebas, formato y tipado)
  se resolverá en el plan de implementación.
