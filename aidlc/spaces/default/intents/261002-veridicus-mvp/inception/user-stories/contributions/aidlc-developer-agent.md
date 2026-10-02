**Collaborator:** aidlc-developer-agent

## Contribution

Ángulo: si cada historia se puede construir y verificar como rebanada vertical con la pila fijada
(FastAPI, React/TS, cola Redis, PostgreSQL + `pgvector` con CloudNativePG, juez local ≤ 8B en CPU,
*fakes* deterministas de LLM y *embeddings* en los niveles 0 y 1). No reabro las decisiones P1–P8. Cada
propuesta trae el ID que tocaría y es integrable tal cual o con un ajuste de redacción.

### 1. Riesgo técnico oculto: la «afirmación» no tiene quien la produzca (US3.1, US4.1, US2.3)

P4 fijó la evaluación **por afirmación**, pero ninguna historia dice cómo un turno se convierte en
afirmaciones, y de eso dependen la recuperación por afirmación, el umbral y la equivalencia de AC2.3.2.
Si la extracción la hace el LLM, cada turno paga una llamada más en CPU (presión sobre NFR3 y NFR8) y el
resultado deja de ser reproducible en los niveles 0 y 1.

- **AC3.1.5 (nuevo)** Given un turno, When el sistema lo divide en afirmaciones, Then usa una regla
  determinista (la fija Functional Design) y el mismo texto produce siempre las mismas afirmaciones,
  cada una subcadena literal del turno (prueba de propiedad con Hypothesis, nivel 0).
- **AC3.1.6 (nuevo)** Given un turno evaluado, When consulto su registro de evaluación por la API, Then
  cada afirmación guarda su texto, su similitud máxima, los 3 pasajes más cercanos y su calificación
  (nivel 1). No es visible en la interfaz (respeta «congruente → nada visible» de P4), pero lo necesitan
  el arnés de nivel 2, el reporte y las pruebas de US4.1.

### 2. El umbral debe ganarle al juez, y hay una combinación sin regla (US4.1)

- **AC4.1.6 (nuevo)** Given una afirmación con similitud por debajo del umbral y un juez (*fake*) que
  responde «incongruente», When se evalúa, Then queda «no documentada» y no hay alerta. La guardia vive
  en `domain/` y decide antes que el juez; así AUTONOMIA-05 no depende del comportamiento del modelo y la
  rama queda dentro del 100 % de ramas de los módulos guardia.
- **Hueco a cerrar (no decidido en P4):** similitud **en o sobre** el umbral y juez que responde
  «no documentada». Propuesta: cuenta como «no documentada», entra al paquete y no genera alerta
  (**AC4.1.7**). Si el líder prefiere otra regla, igual debe quedar escrita: hoy el código tendría que
  inventarla.
- **«CoT interrumpida» (AC4.1.3) no está definida** cuando la guardia decide antes de llamar al juez,
  porque entonces no existe CoT del modelo. Propuesta: la produce el sistema de forma determinista
  (pasajes recuperados, similitud máxima, umbral de la sesión y el motivo «similitud X < umbral Y») y no
  el LLM. Así no se gasta una inferencia en CPU en un resultado que por regla no se usa.
- **AC4.1.1 y AC4.1.2** solo se pueden ejecutar con similitudes controladas: precisar «con el doble
  determinista de *embeddings* configurado para dar umbral − ε / umbral exacto» (niveles 0 y 1). Con el
  modelo real no se puede construir el «justo por debajo».

### 3. Partir US4.1 y US6.3 ahora, no en Functional Design

Units Generation y Delivery Planning reparten historias, no criterios; si la partición se deja para
Functional Design, la unidad ya quedó dimensionada con la historia grande.

- **US4.1 → US4.1a «Calificar como no documentada por umbral»** (AC4.1.1, 4.1.2, 4.1.4, 4.1.6, 4.1.7;
  dominio + worker; visible porque el turno no produce alerta) y **US4.1b «Recibir el Paquete de
  Contexto de Traspaso»** (AC4.1.3 + aviso y panel lateral; depende de US4.1a). AC4.1.5 pasa a US4.1b
  con su contraparte de nivel 1 (ver punto 4).
- **US6.3 → AC6.3.1 se muda a US6.1** como poscondición de consolidar («Given una sesión consolidada,
  When intento cambiar una alerta, Then la API responde 409 con Problem Details»), y US6.3 queda solo con
  la copia de trabajo y la versión nueva (AC6.3.2–6.3.4).
- **Riesgo de modelo de datos en US6.3:** si el estado de la alerta vive en la fila de la alerta, la
  copia de trabajo pisa el estado de la versión anterior. Propuesta de AC que obliga a modelarlo bien:
  **AC6.3.5** Given dos versiones de reporte, When consulto los estados de alertas de cada una, Then cada
  versión conserva los suyos (la revisión pertenece a la versión de reporte). **AC6.3.6** Given una copia
  de trabajo abierta, When pulso otra vez «Corregir reporte», Then vuelvo a la misma copia; nunca hay
  dos abiertas por sesión.

### 4. Criterios que solo se verifican en el nivel 2 necesitan contraparte en PR (AUTONOMIA-02)

Con *fakes* deterministas, estos criterios son triviales o no aplican; con el modelo real solo corren
fuera de la CI. Cada uno debe tener un criterio de nivel 0/1 que bloquee el PR, y conservar el de nivel 2
como evidencia de NFR4/NFR5:

| AC | Contraparte de nivel 0/1 propuesta |
|---|---|
| AC3.1.4 (CoT trazable) | El esquema JSON del juez exige que cada paso de la CoT cite IDs de pasaje, y el validador rechaza un ID que no esté entre los recuperados para esa afirmación (nivel 0). El 100 % semántico sigue en NFR4. |
| AC3.3.1 (inyección del Escenario A) | El *prompt* renderizado contiene el testimonio solo dentro del bloque delimitado de datos, y el *prompt* del sistema se lee del archivo montado cuyo SHA-256 coincide con el del repositorio (nivel 0). La igualdad de alertas con el modelo real queda en nivel 2. |
| AC3.3.2 | Concretar: política Kyverno que exige `readOnly: true` en el montaje del *prompt* (nivel 0) y prueba que con el rol de base de datos del agente un `INSERT`/`UPDATE` sobre pasajes falla (nivel 1). |
| AC2.3.2 (pegada = turno a turno) | Con los dobles deterministas, el conjunto de alertas y de Hechos No Documentados es idéntico (nivel 1); con el Golden Dataset y el modelo real, nivel 2. |
| AC4.1.5 (caso HND) | Con el doble configurado para el caso HND: 0 alertas, 0 preguntas, 1 paquete (nivel 1); el Golden Dataset real, nivel 2. |

### 5. «CoT desplegada» necesita evidencia en la API (US5.1, US5.2)

AC5.1.1 dice que la API rechaza el cambio, pero la API no sabe qué hizo el navegador.

- **AC5.1.4 (nuevo)** Given una alerta, When despliego su CoT, Then la interfaz registra un evento
  «CoT consultada» con mi usuario y la hora, que solo admite inserciones.
- **AC5.1.1 (precisión)** … Then la API responde 409 con un `code` estable (p. ej. `cot_not_viewed`) si
  no existe ese evento **del mismo usuario** para esa alerta.
- **AC5.2.4 (nuevo)** El mismo rechazo para `editada` (US5.2 hoy no tiene el criterio negativo que exige
  FR6.2).
- Límite que conviene declarar: el evento prueba que se pidió desplegar la CoT, no que se leyó. Es
  evidencia de auditoría, no una garantía.

### 6. Detectar el corte del navegador (US7.1)

«Se corta la conexión» no es observable para el servidor sin un canal vivo, y los WebSockets de
*streaming* están en WON'T. Propuesta medible y sin *sockets*:

- **AC7.1.1 (reescrito)** Given una sesión abierta, When el servidor no recibe el latido de la consola
  durante *T* segundos (configurable; *T* lo fija NFR Requirements), Then la sesión pasa a `suspendida`
  en ≤ *T* + el intervalo de revisión, y el cambio guarda la hora.
- **AC7.1.4 (nuevo)** Given una sesión `suspendida`, When siguen turnos en cola, Then el worker los
  termina y sus resultados quedan en la sesión (la suspensión no detiene el procesamiento).
- El «0 perdidos» de AC7.1.3 depende más del worker que del navegador; ver punto 7.

### 7. Entrega de la cola: al menos una vez e idempotente (US2.2)

NFR8 (0 fallos en 50 sesiones) y AC7.1.3 caen si un worker muere con un turno a medias: con una lista
Redis simple (`BRPOP`) el mensaje se pierde.

- **AC2.2.4 (nuevo)** Given un worker que muere mientras procesa un turno, When otro worker toma el
  mensaje pendiente, Then el turno se evalúa y produce exactamente un resultado (idempotencia por ID de
  turno; nivel 1 contra Redis real).
- **AC2.2.2 (medible)** Given el doble del juez bloqueado indefinidamente sobre el turno 1, When envío
  el turno 2 o abro una alerta, Then la API responde en ≤ 1 s (o el valor que fije NFR Requirements)
  con `202` para el turno. Igual para AC10.2.2.

### 8. Consolidar con turnos aún en proceso (US6.1, US2.4, US3.2)

AC6.1.1 solo mira alertas `pendiente`; un turno en `procesando` puede crear una alerta nueva después de
consolidar. Además AC3.2.2 («puedo reenviarlo») choca con AC2.4.1 («no se aceptan más turnos») si el
turno falla después de «Finalizar sesión».

- **AC6.1.5 (nuevo)** Given una sesión con algún turno `en cola` o `procesando`, When intento
  consolidar, Then la API lo rechaza.
- **AC3.2.3 (nuevo)** Given una sesión finalizada con un turno en `error`, When lo reenvío, Then se
  reprocesa el mismo turno con su mismo número (no es un turno nuevo).
- **Decisión pendiente para el líder:** un turno que sigue en `error` (con temperatura 0 y semilla fija,
  reenviarlo puede fallar igual) ¿bloquea la consolidación o aparece en el reporte como «turno no
  evaluado (`code`)»? Propongo lo segundo: bloquearlo dejaría una sesión imposible de cerrar.

### 9. Precisiones de implementabilidad menores

- **US1.1:** indexar 1 MB toma hasta 3 min (NFR9), así que es asíncrona. **AC1.1.5 (nuevo)** Given una
  carga válida, When la envío, Then la API responde `202` y el escenario aparece `indexando` hasta pasar
  a `listo` o `fallido`. AC1.1.4: la escritura de pasajes es atómica (con el doble de *embeddings*
  fallando en el pasaje *n*, 0 pasajes visibles; nivel 1). AC1.1.2: el archivo Latin-1 de prueba debe
  tener bytes inválidos en UTF-8 (p. ej. `ñ` como `0xF1`); uno solo ASCII es UTF-8 válido. El PDF se
  detecta por contenido (`%PDF`), no por extensión.
- **AC1.2.2 y NFR11:** «no existe o responde con error» es débil. Dos comprobaciones: el contrato
  OpenAPI no tiene `PUT`/`PATCH`/`DELETE` sobre pasajes (nivel 0), y el rol de base de datos de la
  aplicación no tiene `UPDATE`/`DELETE` sobre pasajes ni historiales (nivel 1). Propongo **AC5.1.5**: un
  `UPDATE` o `DELETE` sobre el historial de estados con el rol de la aplicación falla.
- **AC5.5.1:** el escaneo solo es completo si todo texto visible sale de un catálogo de mensajes en
  español (escaneable en nivel 0) y si se aplica a los campos del juez **salvo** `fragmento` y `cita`.
  Riesgo: «falso» es palabra corriente y la CoT del modelo puede usarla. Propongo que también sea una
  guardia en ejecución: una CoT con vocabulario prohibido fuera de citas se trata como salida inválida
  (turno en `error`, `code` estable, sin alerta parcial) y cuenta como error de formato en el nivel 2.
- **AC8.3.4:** concretar: el umbral se lee una sola vez al arrancar desde `VERIDICUS_<AJUSTE>` a un
  objeto de configuración inmutable; ninguna tabla guarda el umbral salvo la copia de la sesión, y
  ninguna ruta de escritura de la API lo recibe (prueba de contrato, nivel 0).
- **AC8.1.4** es transversal: verificarlo con una prueba de esquema que exige `NOT NULL` en actor y hora
  de cada tabla de cambios de estado (nivel 1), no como criterio de la historia de *login*.
- **AC9.2.2** (humo) necesita el flujo de texto completo (alerta y paquete); no puede cerrarse con US9.2
  al principio. Que dependa de US3.1 y US4.1b, o que se mueva a Build and Test.
- **AC9.4.1 (AUTONOMIA-01):** redactar «When el humano lo aplica tras la fusión de su PR» y añadir un
  criterio de nivel 0: `helm template` + `kubeconform` muestran el `Cluster` de CloudNativePG con la
  extensión `pgvector` y Redis.
- **US10.5:** duplica las inferencias por alerta candidata en CPU; Delivery Planning debe contarlo frente
  a NFR3 y NFR8.

### 10. Dependencias corregidas

| Historia | Depende de (propuesta) | Cambio |
|---|---|---|
| US1.2, US1.3 | US1.1 | faltaba |
| US2.1 | US1.3 (elegir versión del catálogo), US8.1 | antes US1.1 |
| US2.4 | US2.2 | faltaba |
| US4.1b | US4.1a | por la partición |
| US5.4, US8.2 | US8.1 | faltaba |
| US6.1 | US2.4, US4.1b (el reporte lleva los paquetes), US5.1–US5.3 | faltaba US4.1b |
| US7.1 | US2.2, US5.1 (AC7.1.3 cuenta cambios de estado) | faltaba US5.1 |
| US10.3 | US4.1a (supresión por «no documentada») | faltaba |
| US9.2 (AC9.2.2) | US3.1, US4.1b | faltaba |

Ruta crítica del flujo de texto: US8.1 → US1.1 → US1.3 → US2.1 → US2.2 → US3.1 → US4.1a → US5.1 →
US2.4 → US6.1 → US6.2.

## Positions

- AGREE: épicas por recorrido con el flujo de texto como primera unidad — coincide con el orden de entrega de team-practices y con la ruta crítica.
- AGREE: AC3.2.1 y AC3.1.2 (sin alerta parcial, una prueba por campo) — son deterministas y se cubren en el nivel 0 con el *fake* del juez.
- AGREE: dejar NFR2–NFR9 y NFR13–NFR14 fuera de las historias — su verificación es de NFR Requirements y Build and Test.
- OBJECT: dejar a Functional Design la partición de US4.1 y US6.3 — Units Generation dimensiona con historias; deben llegar ya partidas (US4.1a/US4.1b; AC6.3.1 a US6.1).
- OBJECT: AC3.1.4, AC3.3.1, AC2.3.2 y AC4.1.5 solo verificables en el nivel 2 — necesitan contraparte de nivel 0/1 para que el PR las pruebe (AUTONOMIA-02).
- OBJECT: AC5.1.1 sin mecanismo de evidencia — la API no puede rechazar sin un evento «CoT consultada» registrado.
- OBJECT: AC7.1.1 tal como está — «se corta la conexión» no es observable sin un latido con plazo medible.
- OBJECT: consolidar mirando solo alertas `pendiente` — un turno aún en proceso puede crear una alerta después de consolidar (AC6.1.5).
- OBJECT: tabla de dependencias — faltan US2.4→US2.2, US6.1→US4.1, US2.1→US1.3 y US10.3→US4.1.
