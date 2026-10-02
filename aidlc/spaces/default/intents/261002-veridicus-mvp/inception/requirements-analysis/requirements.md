# Requisitos — Veridicus (MVP académico)

**Insumos.** `specs/prd.md` (fuente única de requisitos, con las 19 decisiones de
`docs/coherencia-insumos.md` ya aplicadas), `pvb.md` (superado por el PRD donde difieren, nota H6),
`docs/limite-autonomia.md` (reglas AUTONOMIA-01..05), las prácticas afirmadas en
`aidlc/spaces/default/intents/261002-veridicus-mvp/inception/practices-discovery/team-practices.md`
(team-practices) y las respuestas de
`requirements-analysis-questions.md` (P1–P8 y Seguimiento 1).

El scope `classic` omite Ideation, así que no hay intent-statement ni scope-document; el proyecto es
greenfield, así que no hay business-overview, architecture ni code-structure. Por eso cada requisito se
traza a un segmento del PRD (S1–S13), a una regla AUTONOMIA o a una respuesta de este análisis.

**Prioridad.** MUST, SHOULD y COULD siguen el MoSCoW del PRD (S8). Los WON'T están en
«Fuera de alcance».

---

## 1. Análisis de la intención

- **Qué se busca.** Que un analista de verdad contraste un testimonio en español contra un marco de
  verdad sintético y reciba, por cada afirmación, sugerencias de revisión justificadas con su Cadena de
  Pensamiento (CoT), sin que la IA decida nada sobre la veracidad del compareciente (S1, S6-P1).
- **Para quién.** Analista de Verdad (usuario), Líder SRE/CISO (veto de soberanía) y Oficial de
  Cumplimiento Ético (veto de integridad del proceso) (S3).
- **Por qué importa.** Reducir la fatiga analítica y el tiempo de cotejo sin que datos sensibles salgan
  del clúster local (S2, S6-P3).
- **Tipo de trabajo.** Producto nuevo (greenfield), multicomponente, complejidad estándar; profundidad
  **Standard**. Este trabajo se detiene en la Parte 1 (plan de tareas) de Code Generation de cada unidad.
- **Resultado del MVP.** El flujo de **texto** de punta a punta funciona en CPU: cargar el escenario →
  ingresar el testimonio → consultar `pgvector` → mostrar la alerta con su CoT → revisar →
  consolidar → descargar (S13 §5; orden de entrega de team-practices).

### Vocabulario del dominio

| Término (PRD) | Significado en estos requisitos |
|---|---|
| Escenario de control (marco de verdad) | Documento sintético de hechos indexado en `pgvector`; versionado e inmutable (FR2). |
| Turno | Unidad de testimonio que el sistema evalúa; un envío del analista o un bloque de una transcripción dividida (FR3). |
| Calificación de una afirmación | Solo `congruente`, `incongruente` o `no documentada`; nunca «verdadero», «falso» ni «miente». |
| Sugerencia de revisión (alerta) | Hallazgo de incongruencia de la IA que un humano debe revisar; estados `pendiente`, `aceptada`, `editada`, `descartada`. |
| Silencio Fáctico / Hecho No Documentado | Resultado normal cuando la similitud recuperada está por debajo del umbral: sin alerta ni pregunta, con Paquete de Contexto de Traspaso (FR5). |

---

## 2. Requisitos funcionales

### FR1 — Inicio de sesión y roles (MUST) · S8, S9-B, P5

- **FR1.1** El sistema autentica con usuario y contraseña locales; la contraseña se guarda solo como hash
  de un algoritmo adaptativo con sal. *Criterio:* ninguna columna ni log contiene la contraseña en claro
  (prueba de integración que inspecciona la base y los logs tras crear un usuario).
- **FR1.2** Existen exactamente dos roles, `analista` y `admin`, con esta matriz (P5):

  | Acción | `analista` | `admin` |
  |---|---|---|
  | Gestionar usuarios | No | Sí |
  | Cargar escenarios de control | Sí | Sí |
  | Crear sesiones e ingresar testimonio | Sí | No |
  | Cambiar el estado de alertas y consolidar | Solo en sus propias sesiones | No |
  | Leer sesiones y reportes | Todas | Todas |
  | Aplicar un cambio de umbral | No | Sí |

  *Criterio:* una prueba por cada celda «No» o «Solo propias» verifica que la API responde 403 con un
  Problem Details en español.
- **FR1.3** Toda acción que cambia estado (carga de escenario, cambio de estado de alerta,
  consolidación, nueva versión de reporte, cambio de umbral) registra el usuario autenticado y la hora
  UTC. *Criterio:* ninguna de esas filas admite actor o hora nulos (restricción de base de datos y
  prueba de integración).

### FR2 — Escenario de control (MUST) · S5-CU1, S7-J1, P3, P4

- **FR2.1** El usuario carga un documento Markdown o texto plano en UTF-8 de **hasta 1 MB**. Cualquier
  otro formato, codificación o tamaño se rechaza con un mensaje en español y no se indexa nada (P4).
  *Criterio:* pruebas con 1 MB exacto (aceptado), 1 MB + 1 byte, un PDF y un archivo Latin-1 (rechazados).
- **FR2.2** El sistema segmenta el documento, calcula los *embeddings* con un modelo local y guarda
  pasajes y vectores en PostgreSQL + `pgvector` dentro del clúster, sin tráfico de red fuera del clúster.
  *Criterio:* cada pasaje guarda su texto literal, su posición y el identificador de documento que
  citará la alerta.
- **FR2.3** Al terminar, la interfaz muestra que el escenario está indexado y listo; si falla, muestra
  el error en español y el escenario no queda disponible para sesiones.
- **FR2.4** Un escenario indexado es **inmutable**. Corregirlo crea una **versión nueva** con su propio
  identificador y el SHA-256 del documento fuente; las versiones anteriores se conservan (P3).
  *Criterio:* la API no ofrece ninguna operación que modifique pasajes de una versión existente.
- **FR2.5** Hay un catálogo de escenarios y versiones para elegir al crear una sesión (S7-J1).

### FR3 — Sesión e ingreso del testimonio en texto (MUST) · S8, S5-CU2, P2

- **FR3.1** Crear una sesión exige elegir una versión de escenario; la sesión queda ligada a ese
  identificador y SHA-256 durante toda su vida (P3).
- **FR3.2** El analista envía el testimonio **turno a turno**: cada envío es un turno numerado en orden
  (P2).
- **FR3.3** El analista también puede pegar una transcripción completa; el sistema la divide en turnos
  por línea vacía o por marca de hablante y los procesa en orden, como si se hubieran enviado uno a uno
  (P2). *Criterio:* una transcripción del Golden Dataset produce el mismo resultado pegada completa que
  enviada turno a turno.
- **FR3.4** Cada turno se encola en Redis y se procesa de forma asíncrona; enviar un turno nunca bloquea
  la interfaz y el turno muestra su estado (`en cola`, `procesando`, `evaluado`, `error`) (S6-P2).
- **FR3.5** El analista pulsa «Finalizar sesión» para cerrar el ingreso de turnos; desde ese momento
  empieza la medición de MTTV (NFR7).

### FR4 — Validación semántica (MUST) · S5-CU3, S9-D, S11, AUTONOMIA-05

- **FR4.1** Por cada turno, el agente semántico recupera de `pgvector` los pasajes más similares de la
  versión de escenario de la sesión, con su coeficiente de similitud.
- **FR4.2** Un juez LLM local (*LLM-as-a-judge*) con temperatura 0 y semilla fija califica cada
  afirmación del turno como `congruente`, `incongruente` o `no documentada`, y su salida se valida contra
  un esquema JSON. *Criterio:* una salida que no cumple el esquema no produce alerta, el turno queda en
  `error` con un `code` estable y nunca se emite una alerta parcial.
- **FR4.3** Solo una afirmación `incongruente` cuya similitud recuperada esté **en o por encima** del
  umbral produce una alerta (AUTONOMIA-05).
- **FR4.4** Una alerta tiene cuatro campos obligatorios: fragmento literal de la transcripción, cita
  literal del pasaje, identificador del documento y traza CoT. Una alerta sin cualquiera de ellos se
  rechaza antes de guardarse (AUTONOMIA-05, S6-P4). *Criterio:* cuatro pruebas, una por campo ausente.
- **FR4.5** Toda afirmación de la CoT es trazable a pasajes de la versión de escenario de la sesión; la
  IA no añade hechos, nombres ni deducciones externas (S11 §2.1). Se mide en NFR4.
- **FR4.6** El texto del testimonio se trata como datos: las instrucciones del sistema son una
  configuración inmutable de solo lectura y el juez solo tiene permisos de lectura sobre el marco de
  verdad (S12-R7). Se mide en NFR5.

### FR5 — Silencio Fáctico y Paquete de Contexto de Traspaso (MUST) · S7-J4, S8, AUTONOMIA-05

- **FR5.1** El umbral de similitud es un parámetro de configuración obligatorio
  (`VERIDICUS_<AJUSTE>`); si falta o es inválido, el servicio no arranca. Su valor lo fija NFR
  Requirements contra el Golden Dataset.
- **FR5.2** Si la similitud máxima recuperada para un turno está por debajo del umbral, el turno queda
  como Hecho No Documentado: **0 alertas y 0 preguntas sugeridas** para ese turno.
  *Criterio:* prueba con similitud justo por debajo, igual y justo por encima del umbral.
- **FR5.3** En ese caso el sistema genera un Paquete de Contexto de Traspaso con: el fragmento literal
  actual y los tres turnos previos; los 3 pasajes más cercanos con su coeficiente; la traza CoT
  interrumpida; y las fluctuaciones afectivas solo si el clasificador afectivo ligero (FR11.1) está
  activo.
- **FR5.4** La interfaz muestra el aviso destacado «La IA no puede validar este fragmento de forma
  autónoma. Control manual requerido» y el paquete en un panel lateral.

### FR6 — Revisión humana de alertas (MUST) · S6-P1, S8, S12-R2, P5, P6, AUTONOMIA-03

- **FR6.1** Toda alerta nace `pendiente`. Solo un humano la cambia a `aceptada`, `editada` o
  `descartada`, y solo el analista dueño de la sesión (FR1.2). Cada cambio guarda actor, hora, estado
  anterior y estado nuevo en un historial que no se borra.
- **FR6.2** La CoT se muestra plegada. No se puede marcar una alerta como `aceptada` ni `editada` sin
  haber desplegado su CoT (P6). *Criterio:* prueba de interfaz y de API (la API rechaza el cambio si no
  consta el despliegue).
- **FR6.3** Descartar exige una nota no vacía; aceptar o editar admite una nota opcional (P6).
- **FR6.4** Ni la salida de la IA ni la interfaz contienen etiquetas de veracidad sobre el compareciente
  («mentiroso», «falso», «miente», «verdadero», puntaje binario de verdad); el esquema de la alerta no
  tiene campos de veracidad. El escaneo excluye las citas literales del testimonio y del escenario.
  *Criterio:* prueba automatizada que falla si aparece una de esas etiquetas (AUTONOMIA-03).
- **FR6.5** La interfaz recuerda, junto a cada alerta, que la IA es un asistente y que el criterio del
  analista prevalece (S12-R2).

### FR7 — Consolidación, reporte y descarga (MUST) · S5-CU5, S7-J1, S8, P7, Seguimiento 1

- **FR7.1** Solo el analista dueño puede ejecutar «Finalizar y Consolidar», y solo después de
  «Finalizar sesión». El botón está deshabilitado mientras haya alguna alerta `pendiente`
  (Seguimiento 1). *Criterio:* la API rechaza la consolidación con alertas pendientes.
- **FR7.2** El reporte es un Markdown con: transcripción completa por turnos; cada alerta con su estado
  final, notas, fragmento, cita, identificador de documento y CoT; los Hechos No Documentados con su
  paquete; la versión de escenario (identificador y SHA-256); y quién consolidó y cuándo.
- **FR7.3** El sistema guarda el reporte en el volumen persistente y registra su SHA-256. *Criterio:*
  recalcular el SHA-256 del archivo descargado coincide con el registrado.
- **FR7.4** El analista descarga el reporte consolidado desde la interfaz.
- **FR7.5** Tras consolidar, la sesión y sus alertas quedan **bloqueadas**. Una corrección crea una
  **versión nueva** del reporte, con nuevo SHA-256 y nueva consolidación (quién y cuándo), que referencia
  a la anterior; la anterior se conserva intacta (P7).

### FR8 — Reanudación de sesión (MUST) · S7-J3, S8

- **FR8.1** El estado de la sesión se persiste en PostgreSQL en cada turno.
- **FR8.2** Si la conexión del navegador se pierde con la sesión abierta, la sesión pasa a `suspendida`
  y nada procesado se pierde.
- **FR8.3** Al volver a entrar, el analista ve el aviso de sesión interrumpida y puede reanudar desde el
  último turno registrado. *Criterio:* prueba de integración que corta la conexión a mitad de una
  transcripción y verifica 0 turnos, alertas o cambios de estado perdidos tras reanudar.

### FR9 — Umbral bajo control humano (MUST) · S8 WON'T, S10 §4, AUTONOMIA-03

- **FR9.1** El sistema nunca cambia sus umbrales por sí mismo.
- **FR9.2** Un cambio de umbral solo lo aplica un `admin` y queda registrado con quién, cuándo, valor
  anterior y valor nuevo (FR1.2). Si el umbral vive en la configuración del despliegue, el cambio entra
  como artefacto revisable por PR (AUTONOMIA-01).
- **FR9.3** (SHOULD) Si una sesión supera el umbral AIR (> 25 % de alertas consecutivas descartadas o
  ignoradas), Prometheus/Grafana alertan con una **propuesta** de nuevo umbral; aplicarla sigue FR9.2.

### FR10 — Funciones SHOULD · S8

- **FR10.1** Indicadores de procesamiento en la interfaz («Procesando audio…», «Consultando marco de
  verdad…») con cronómetro de latencia.
- **FR10.2** Grabación por demanda (*push-to-talk*) en WAV/MP3 enviada por HTTP POST asíncrono y
  transcrita con Whisper ligero en CPU dentro del clúster; el turno resultante sigue el mismo camino que
  FR3.2. Se agrega solo cuando el flujo de texto funciona de punta a punta.
- **FR10.3** Sugerencia de siguiente pregunta al analista, basada solo en el marco de verdad. Ninguna
  pregunta llega al compareciente sin la decisión del analista, se suprime en un Hecho No Documentado
  (FR5.2) y ningún MUST depende de ella.
- **FR10.4** Audio por demanda de la pregunta (TTS ligero en CPU), solo al pulsar «Escuchar audio».
- **FR10.5** Protocolo de permutación en línea: cada alerta se evalúa en ambos órdenes de lectura, de
  forma asíncrona, y solo se registra si la discrepancia aparece en los dos.

### FR11 — Funciones COULD · S8

- **FR11.1** Clasificador afectivo ligero (palabras clave emocionales en el *prompt*), sin meta
  numérica.
- **FR11.2** Historial de sesiones en un panel lateral.
- **FR11.3** Proxy de anonimización hacia un LLM externo: enmascara nombres, ubicaciones y números de
  expediente con expresiones regulares en español antes de cualquier llamada externa. Si se construye,
  una prueba verifica que el *payload* saliente pasó por el anonimizador (AUTONOMIA-04). Ningún MUST
  depende de él.

### FR12 — Plataforma en el clúster · S8 §5, S13

- **FR12.1** (MUST) PostgreSQL + `pgvector` con el operador CloudNativePG; Redis como cola asíncrona.
- **FR12.2** (MUST) Manifiestos o chart con `resources.requests` y `resources.limits` en cada pod.
  *Criterio:* política de manifiestos (Kyverno CLI) que falla si falta alguno.
- **FR12.3** (MUST) Una `NetworkPolicy`, entregada como artefacto revisable, que niega la salida a
  internet a todos los pods que manejan datos sin anonimizar (AUTONOMIA-04).
- **FR12.4** (MUST) Credenciales inyectadas desde Kubernetes Secrets en tiempo de ejecución; los
  manifiestos solo los referencian.
- **FR12.5** (MUST) Cada servicio expone un *endpoint* de salud que responde 200 cuando está listo
  (lo usa la prueba de humo de team-practices).
- **FR12.6** (SHOULD) Despliegue GitOps con Argo CD; Prometheus y Grafana con el panel AIR.
- **FR12.7** (COULD) Autoescalado con KEDA según la longitud de la cola; perfil GPU opcional para
  evaluación y demostración.

---

## 3. Requisitos no funcionales

- **NFR1 — Soberanía de datos (MUST, AUTONOMIA-04, S6-P3).** Ningún audio crudo, transcripción sin
  anonimizar, nombre de víctima ni identificador real del proceso sale del clúster. El diseño declara,
  por componente, si corre dentro o fuera del clúster y qué datos cruzan esa frontera. *Criterio:*
  política estática de `NetworkPolicy` en nivel 0 y verificación manual en el clúster antes de la
  sustentación.
- **NFR2 — CPU primero (MUST, S6-P2, S8 WON'T).** Todas las funciones MUST y SHOULD funcionan en la
  máquina de desarrollo sin GPU; las suites de niveles 0 y 1 no exigen GPU. El perfil GPU es opcional y
  sus pruebas corren en una etapa separada, a demanda.
- **NFR3 — Interfaz no bloqueante (MUST, S6-P2).** No hay llamadas síncronas de punta a punta desde la
  interfaz al procesamiento de IA; la interfaz responde a la interacción mientras un turno se procesa.
  La latencia máxima por turno de texto y el *N* de la prueba de humo los fija NFR Requirements; para la
  voz (SHOULD) se aceptan 8–12 s por turno en CPU.
- **NFR4 — Calidad de la IA sobre el Golden Dataset (MUST, nivel 2, S11, P1).** Con temperatura 0 y
  semilla fija, sobre el escenario único, las 10 transcripciones y el caso de Hecho No Documentado:
  - detecta **al menos 5 de las 6** discrepancias sembradas (≥ 83 %) (P1);
  - emite **como máximo 1 alerta** en total sobre las 4 transcripciones alineadas (P1);
  - 100 % de trazabilidad factual de las afirmaciones de la CoT a pasajes del escenario;
  - 0 % de error de formato JSON;
  - permutación aplicada en el 100 % de las consultas *offline* y consistencia > 65 % al invertir el
    orden;
  - en el caso de Hecho No Documentado, 0 alertas, 0 preguntas y 1 Paquete de Contexto de Traspaso.

  El reporte JSON de la evaluación registra versión del dataset, *hash* del *prompt*, umbral, *digest*
  del modelo, perfil CPU/GPU y métricas.
- **NFR5 — Resistencia adversarial (MUST, nivel 2, S11 §3).** Escenario A: añadir el texto de
  inyección del PRD a cada transcripción del Golden Dataset no cambia el conjunto de alertas respecto a
  la versión sin inyección. Escenario B: el juez local es de una familia de modelos distinta a la que
  generó los datos sintéticos, y el reporte de evaluación lo declara. Escenario C: cubierto por NFR4.
- **NFR6 — Explicabilidad (MUST, S11 §2.3).** Dos evaluadores (el autor y un par del curso) califican la
  claridad de la CoT de las 10 transcripciones en escala Likert de 1 a 5; el promedio es ≥ 4.5.
- **NFR7 — MTTV (MUST, S10 §1).** El tiempo medio desde «Finalizar sesión» hasta «Finalizar y
  Consolidar» es < 10 minutos por caso del Golden Dataset, calculado con las marcas de hora que guarda
  el sistema. La línea base del cotejo manual queda como «[VERIFICAR] sin fuente directa».
- **NFR8 — Éxito del pipeline (MUST, S10 §2, P8).** En la máquina de CPU, al menos 50 sesiones de texto
  sobre el Golden Dataset ejecutadas en tandas de **3 sesiones concurrentes** terminan de punta a punta
  sin `OOMKilled` ni *timeout* en ≥ 98 % de los casos (como máximo 1 fallo cada 50).
- **NFR9 — Indexación del escenario (MUST, S5-CU1, P4).** Un documento de 1 MB queda indexado y listo en
  menos de 3 minutos en la máquina de CPU.
- **NFR10 — Seguridad de la aplicación (MUST).** Entradas validadas en las fronteras; contraseñas solo
  con hash (FR1.1); credenciales solo por referencia a Secrets; *prompts* del sistema como
  configuración de solo lectura; el usuario de base de datos del juez solo lee el marco de verdad; los
  logs contienen solo identificadores, nunca texto de testimonio ni nombres; toda E/S tiene *timeout*
  explícito; un error se devuelve como Problem Details (RFC 9457) con `code` estable y `detail` en
  español.
- **NFR11 — Integridad y auditoría (MUST, AUTONOMIA-03).** Los historiales de estado de alertas,
  consolidaciones, versiones de reporte y cambios de umbral solo admiten inserciones. *Criterio:* prueba
  de integración que intenta modificar o borrar una fila de historial y falla.
- **NFR12 — Datos sintéticos (MUST, S8 WON'T, `project.md`).** Ni el repositorio ni la CI contienen
  testimonios, audios, nombres ni expedientes reales.
- **NFR13 — Calidad del código (MUST, team-practices).** 80 % de líneas por servicio Python y por el
  frontend, y 100 % de ramas en los módulos guardia (umbral del Silencio Fáctico, validación y máquina
  de estados de la alerta, consolidación, anonimizador si se construye), medido en CI y bloqueante.
- **NFR14 — Idioma (MUST, team-practices).** Todos los textos visibles, mensajes de error y reportes
  están en español; los identificadores del código siguen el glosario único en inglés.
- **NFR15 — Observabilidad (SHOULD, S8 §5).** Métricas de CPU de los pods de IA, latencia por turno e
  indicador AIR en Prometheus y Grafana.

---

## 4. Restricciones

- **AUTONOMIA-01..05** (`docs/limite-autonomia.md`, `team.md`) son bloqueantes en todas las etapas.
  En particular, ningún plan de tareas aplica cambios al clúster sin aprobación humana registrada:
  el destino es un PR con evidencia.
- **Este trabajo no escribe código de aplicación:** el flujo se detiene en la Parte 1 (plan de tareas)
  de Code Generation de cada unidad.
- Kubernetes local; todo funciona en CPU; GPU solo como perfil opcional (hasta 4 GPU y 32 GB de RAM).
- Pila fijada: FastAPI (Python 3.12) para el backend, React con TypeScript estricto para el frontend,
  Whisper ligero (`tiny`/`base`) en CPU, juez cuantizado de ≤ 8B parámetros en CPU, *embeddings*
  multilingües locales, PostgreSQL + `pgvector` con CloudNativePG y Redis (S9).
- Monorepo, CI, imágenes en GHCR privado, migraciones como `Job` aparte y Secrets por referencia, según
  team-practices.
- Entrega alineada con los módulos 4–8 del curso y la sustentación de la sesión 16 (S13).

---

## 5. Supuestos

- La transcripción de audio es un paso externo ya probado; el MVP opera sobre texto plano en español
  (S8, S12-R3).
- El Golden Dataset (un escenario, 10 transcripciones y 1 caso de Hecho No Documentado) se construye con
  datos sintéticos antes de la evaluación de nivel 2 (S11 §1).
- El modelo con que se sintetizan los datos es de una familia distinta a la del juez local (S11-B).
- En la sustentación trabaja un solo analista; la concurrencia de 3 sesiones (NFR8) es una prueba de
  carga, no un uso real.
- Una marca de hablante es un prefijo de línea del tipo `Nombre:`; Functional Design fija el formato
  exacto (FR3.3).

---

## 6. Fuera de alcance

- Todo lo marcado WON'T en el PRD (S8 §4): voz en tiempo real por *streaming* (< 500 ms, gRPC o
  WebSockets); servidores GPU dedicados como requisito; el modelo LieXBerta completo (RoBERTa-base +
  XGBoost) y sus metas (87.50 % de *accuracy*), que son del TG2; datos judiciales reales; firma
  criptográfica por analista; recalibración automática de umbrales.
- El caso de uso 4 completo (alerta estilométrica con LieXBerta) y el riesgo 10 (calibración dialectal).
- La meta del codificador de tipos de pregunta (95 % de acuerdo, Kappa 0.93), que depende de un modelo
  RoBERTa entrenado; la sugerencia de pregunta (FR10.3) no tiene meta numérica en el MVP.
- Como **criterios de aceptación**, las métricas de adopción del PRD: uso semanal > 85 % y tasa de
  desestimación < 15 % en producción. Quedan como hipótesis de producto para el TG (P8).
- Argo Workflows y el procesamiento *batch* de audios largos descritos en el PVB.
- La caché semántica para APIs externas (S12-R8): no hay llamadas externas obligatorias en el MVP.

---

## 7. Preguntas abiertas para etapas posteriores

| Pregunta | Etapa que la cierra |
|---|---|
| Valor del umbral de similitud del Silencio Fáctico | NFR Requirements (benchmark sobre el Golden Dataset) |
| Modelo exacto del juez y de *embeddings*, y su *digest* | NFR Requirements |
| Latencia máxima por turno de texto en CPU y *N* de la prueba de humo | NFR Requirements |
| Número de pasajes recuperados por turno y estrategia de segmentación | Functional Design |
| Formato exacto de la marca de hablante al dividir una transcripción | Functional Design |
| Cómo detecta el sistema la pérdida de conexión que suspende una sesión | Functional Design |
| Política de contraseñas y duración de la sesión web | NFR Requirements |
| Nivel de accesibilidad de la interfaz (no lo fija el PRD) | User Stories / Refined Mockups |
| Distribución de Kubernetes, CNI y namespaces en cada máquina | Infrastructure Design |

---

## 8. Trazabilidad

| Requisito | Origen |
|---|---|
| FR1 | S8 MUST (inicio de sesión y roles), S9-B; P5 |
| FR2 | S5-CU1, S7-J1, S9-E; P3, P4 |
| FR3 | S8 MUST (texto), S5-CU2 (pasos 3–4), S6-P2; P2 |
| FR4 | S5-CU3, S6-P4, S9-D, S11 §2, S12-R7; AUTONOMIA-05 |
| FR5 | S7-J4, S8 MUST (umbral); AUTONOMIA-05 |
| FR6 | S6-P1, S8 MUST (edición de alertas), S12-R2, S12-R6; P5, P6; AUTONOMIA-03 |
| FR7 | S5-CU5, S7-J1 (paso 6), S8 MUST (consolidación y descarga); P7, Seguimiento 1; AUTONOMIA-03 |
| FR8 | S7-J3, S8 MUST (reanudación) |
| FR9 | S8 WON'T (recalibración), S10 §4; AUTONOMIA-01, AUTONOMIA-03 |
| FR10 | S8 SHOULD, S5-CU2, S11-C |
| FR11 | S8 COULD, S6-P3; AUTONOMIA-04 |
| FR12 | S8 §5, S7-J2, S13; AUTONOMIA-04 |
| NFR1 | S6-P3, S7-J2 (paso 3); AUTONOMIA-04 |
| NFR2, NFR3 | S6-P2, S8 WON'T (GPU); team-practices |
| NFR4 | S11 §1–2, S11-C; P1; team-practices (nivel 2) |
| NFR5 | S11 §3 (A, B) |
| NFR6 | S11 §2.3 |
| NFR7 | S10 §1 |
| NFR8 | S10 §2; P8 |
| NFR9 | S5-CU1; P4 |
| NFR10 | S12-R7; team-practices (Code Style, Deployment) |
| NFR11 | S6-P1; AUTONOMIA-03 |
| NFR12 | S8 WON'T (datos reales); `project.md` |
| NFR13, NFR14 | team-practices |
| NFR15 | S8 §5, S13 §4 |
