# Requisitos — Veridicus (analizador de incoherencias del TG)

**Revisión 2 — cambio 01 (DT27, 2026-10-30).** Esta versión reemplaza la aprobada el 2026-10-02; la
anterior queda en el historial de Git. Los ID que siguen vigentes se conservan; los que salen quedan
marcados **Retirado** en la sección 8 para que ninguna referencia posterior quede colgando.

**Precisiones de User Stories (2026-11-02).** Al aprobar la revisión 2 de User Stories, el humano decidió
traer aquí las decisiones de esa etapa que precisan requisitos (preguntas 10–16 de
`user-stories-questions.md` y las revisiones del equipo): FR3.6, FR4.2, FR4.9, FR6.1, FR6.4, FR7.1,
FR7.2, FR7.5, FR11.3, FR14.3, FR16.1, NFR12 y el nuevo **FR16.3**. Cada cambio cita su origen.

**Precisiones de Refined Mockups (2026-11-03).** Al aprobar la revisión 2 de Refined Mockups, el humano
decidió traer aquí el tercer rol `investigador` de FR1.2 (seguimiento 8 de `refined-mockups-questions.md`)
y el nuevo **FR13.5**, la consola de reportes del investigador (respuesta 10 y seguimiento 7).

**Insumos.** `specs/prd.md` (iteración 6, fuente única de requisitos), `pvb.md` (cede ante el PRD,
nota H6), `docs/limite-autonomia.md` (AUTONOMIA-01..05, con 04 y 05 reescritas), `docs/iteracion2.md`
(análisis de impacto del cambio 01 y decisiones P1–P18), el cambio 01 con su **contrato común del
analizador v0.1** (sección 4 del cambio; fuera del repositorio hasta que Contract Design lo copie), las
prácticas afirmadas en
`aidlc/spaces/default/intents/261002-veridicus-mvp/inception/practices-discovery/team-practices.md`
(team-practices), corregidas por el cambio 01 en `team.md`, y las respuestas de
`requirements-analysis-questions.md` (preguntas 1–8 y Seguimiento 1 de la primera pasada; preguntas
9–16 de la segunda).

El scope `classic` omite Ideation, así que no hay intent-statement ni scope-document; el proyecto es
greenfield, así que no hay business-overview, architecture ni code-structure. Cada requisito se traza a
un segmento del PRD (S1–S13), a una regla AUTONOMIA, a una decisión P1–P18 de `docs/iteracion2.md` o a
una respuesta de este análisis (preguntas 1–16).

**Prioridad.** MUST, SHOULD y COULD siguen el MoSCoW del PRD (S8). Los WON'T están en «Fuera de
alcance». Las decisiones del Trabajo de Grado se citan por su ID (DT…) y son `[INTERNO]`.

---

## 1. Análisis de la intención

- **Qué se busca.** Que un analista de verdad reciba, sobre la transcripción de un testimonio en
  español, las **contradicciones dentro del propio relato** sobre hechos centrales, cada una con **dos
  citas literales verificadas** de la transcripción, como sugerencias de revisión que solo él decide, sin
  que la IA juzgue la veracidad, las emociones ni el estilo de la persona (S1, S6-P1, S6-P4; DT15).
- **Para quién.** Analista de Verdad (usuario), Líder SRE/CISO (veto de soberanía) y Oficial de
  Cumplimiento Ético (veto de integridad del proceso) (S3). Además, el Trabajo de Grado *Diálogos para
  la Memoria*, que reutiliza el mismo analizador con el mismo contrato (DT17, DT20).
- **Por qué importa.** Reducir la relectura de entrevistas largas para encontrar contradicciones entre
  pasajes distantes, sin que ningún dato sin seudonimizar salga del clúster local (S2, S6-P3).
- **Tipo de trabajo.** Revisión de un producto greenfield aún sin código: multicomponente, complejidad
  estándar, profundidad **Standard**. Desde el cambio 01 se construye: tras la revisión de cada plan de
  tareas, el humano elige `Approve Plan` y la construcción sigue por Bolts.
- **Resultado del MVP.** Primero la **biblioteca del analizador con su línea de comandos** y un
  proveedor comercial, sobre transcripciones sintéticas (orden de entrega de `team.md`). Después, el
  flujo de texto en la consola: cargar o ingresar la transcripción → elegir el perfil → analizar →
  revisar → consolidar → descargar (S13 §5).

### Vocabulario del dominio

| Término | Significado en estos requisitos |
|---|---|
| Transcripción | Entrevista en turnos numerados (`n`), cada uno con hablante (`ENT` entrevistador, `TEST` testimoniante), texto, estado (`visible` / `plegado`) y, si viene del corpus, página inicial y final (FR3). |
| Origen | `corpus` (importada en el formato del contrato, con página) o `guiada` (escrita, pegada o dictada en la consola; página opcional) (P4, P5). |
| Contradicción (hallazgo) | Afirmación del relato que contradice otra del mismo relato sobre un hecho central, de uno de 7 tipos: `fecha`, `numero`, `lugar`, `persona`, `negacion`, `secuencia`, `otro`. No lo son la vaguedad, la emoción, los detalles periféricos ni las versiones de terceros (DT15). |
| Cita verificada | Texto literal de un turno, comprobado de forma determinista contra ese turno antes de que el hallazgo salga del analizador (FR4.4). |
| Sugerencia de revisión | Todo hallazgo en la consola; estados `pendiente`, `aceptada`, `editada`, `descartada`, que solo cambia un humano. |
| Modo final / incremental | Final: analiza la transcripción completa. Incremental: analiza hasta `hasta_turno` y solo busca contradicciones que involucren turnos desde `desde_turno` (contrato común). |
| Perfil de ejecución | Configuración aprobada por PR que fija proveedor y modelo de cada papel (juez, verificador) y si interviene el anonimizador; cada corrida guarda la configuración efectiva y su huella `config_sha256` (DT21). |
| Corrida | Una ejecución del analizador sobre una transcripción, con su registro de llamadas a modelos. |
| Anonimizador | Servicio siempre local que seudonimiza el texto antes de un proveedor externo y restaura las citas; falla cerrado (DT18, P9). |

---

## 2. Requisitos funcionales

### FR1 — Inicio de sesión y roles (MUST) · S8, S9-B, pregunta 5, P8

- **FR1.1** El sistema autentica con usuario y contraseña locales; la contraseña se guarda solo como hash
  de un algoritmo adaptativo con sal. *Criterio:* ninguna columna ni log contiene la contraseña en claro
  (prueba de integración que inspecciona la base y los logs tras crear un usuario).
- **FR1.2** Existen exactamente tres roles, `analista`, `admin` e `investigador`, con esta matriz
  (pregunta 5, P8; el rol `investigador` entra por Refined Mockups, seguimiento 8):

  | Acción | `analista` | `admin` | `investigador` |
  |---|---|---|---|
  | Gestionar usuarios | No | Sí | No |
  | Crear sesiones (importar o ingresar turnos) y elegir su perfil al crearlas | Sí | No | No |
  | Lanzar el modo final | Solo en sus propias sesiones | No | No |
  | Cambiar el estado de hallazgos y consolidar | Solo en sus propias sesiones | No | No |
  | Leer sesiones y reportes | Todas | Todas | No |
  | Subir y leer reportes de corridas y evaluaciones de la CLI (FR13.5) | No | No | Sí |
  | Crear o cambiar perfiles, proveedores o *prompts* | Nadie desde la consola: solo por PR (FR9.2) | Ídem | Ídem |

  *Criterio:* una prueba por cada celda «No» o «Solo propias» verifica que la API responde 403 con un
  Problem Details en español.
- **FR1.3** Toda acción que cambia estado (creación de sesión con su perfil, lanzamiento del modo final,
  cambio de estado de un hallazgo, consolidación, nueva versión de reporte) registra el usuario
  autenticado y la hora UTC. *Criterio:* ninguna de esas filas admite actor o hora nulos (restricción de
  base de datos y prueba de integración).

### FR2 — Escenario de control · **Retirado** (cambio 01)

No hay marco de verdad documental: el contraste con documentos externos es WON'T (S8 §4; DT24).

### FR3 — Sesión y entrada de la transcripción (MUST) · S5-CU1, S8, pregunta 2, P4, P5, P8, pregunta 13

- **FR3.1** Crear una sesión exige una entrevista (importada o guiada) y uno de los perfiles aprobados
  (FR14). La sesión queda ligada a ese perfil y a su `config_sha256` durante toda su vida; el perfil no
  cambia dentro de la sesión (P8).
- **FR3.2** En una sesión `guiada`, el analista envía el testimonio **turno a turno**: cada envío es un
  turno numerado en orden, con el hablante que el analista elige (`ENT` o `TEST`) y sin página (P4, P5).
  Los turnos del entrevistador se guardan como contexto y pueden citarse con aviso (FR4.4).
- **FR3.3** El analista también puede pegar texto libre; el sistema lo divide en turnos por línea vacía o
  por marca de hablante, con la misma especificación y los mismos ejemplos en la vista previa de la
  consola y en el servidor (pregunta 2, P5). *Criterio:* los ejemplos versionados de división producen
  los mismos turnos en ambas implementaciones.
- **FR3.4** Cada análisis se encola en Redis y se procesa de forma asíncrona; enviar un turno o lanzar
  el modo final nunca bloquea la interfaz, y cada turno muestra su estado (`en cola`, `procesando`,
  `analizado`, `error`) (S6-P2).
- **FR3.5** El analista pulsa «Finalizar sesión» para cerrar el ingreso de turnos; desde ese momento
  empieza la medición de MTTV (NFR7).
- **FR3.6** El analista puede **importar** una transcripción en el formato del contrato común
  (`entrevista`, `origen: corpus`, turnos con `n`, `hablante`, `pagina`, `pagina_fin`, `texto`,
  `estado`). Un archivo que no cumple el esquema se rechaza completo, con un mensaje en español, y no se
  crea la sesión (P5). Una transcripción importada nace **cerrada a turnos nuevos** y va directo al modo
  final (User Stories, pregunta 12). *Criterio:* pruebas con un archivo válido, uno con un turno sin
  `hablante` y uno con números de turno repetidos.
- **FR3.7** La consola y la CLI admiten al menos la entrevista más larga del corpus del piloto con margen;
  las cifras exactas (caracteres por transcripción, turnos, caracteres por turno, tamaño del reporte)
  viven en el catálogo único de límites y las fija NFR Requirements (pregunta 13). Una entrada por encima
  del límite se rechaza antes de encolarse.

### FR4 — Analizador de incoherencias (MUST) · S5-CU3, S6-P4, S8, S9-D, S11; AUTONOMIA-05; preguntas 9–11; P6, P12, P14

- **FR4.1** El analizador implementa el **contrato común** (DT17): recibe `transcripcion`, `modo`
  (`final` o `incremental`), `hasta_turno`, `desde_turno` y `perfil`, y devuelve `analizador`,
  `version`, `prompt_sha256`, el registro de modelos (FR15.3), `perfil`, `config_sha256`, `fecha`,
  `estado` y `hallazgos`. En modo incremental solo devuelve contradicciones en las que al menos una cita
  está en un turno igual o posterior a `desde_turno`. *Criterio:* toda salida valida contra el esquema
  versionado del contrato (prueba de contrato en nivel 0).
- **FR4.2** `estado: error` implica `hallazgos` vacío: nunca un resultado parcial. El error lleva un
  `codigo` estable (`salida_invalida`, `bloqueo_contenido`, `tiempo_agotado`, `proveedor` y uno propio
  para el fallo del anonimizador, propuesto `anonimizador`, cuyo nombre definitivo fija Contract Design),
  y la consola muestra «El analizador no pudo procesar este tramo. Revisión manual requerida» con ese
  código (S7-J4); ante el fallo del anonimizador añade «No se envió ningún dato fuera del clúster» (User
  Stories, revisión de calidad y diseño).
  *Criterio:* una prueba por código verifica la lista vacía (AUTONOMIA-05).
- **FR4.3** Un hallazgo tiene como campos obligatorios `hecho`, `tipo` (uno de los 7 valores), `cita_a`,
  `cita_b` (cada una con texto, turno y página si el turno la tiene) y `observaciones`; `actos` es
  opcional. No hay puntaje ni campo de veracidad. *Criterio:* una prueba por campo ausente y otra con un
  `tipo` fuera del enum verifican que el hallazgo se rechaza (AUTONOMIA-05).
- **FR4.4** Antes de que un hallazgo salga del analizador, una verificación determinista comprueba cada
  cita contra su turno con la **regla del piloto** (pregunta 10): solo se normalizan los espacios en
  blanco; « […] » separa fragmentos del mismo turno que deben aparecer en orden; una cita en un turno
  `ENT` o `plegado` se acepta con un aviso que la consola y el reporte muestran; en un turno sin página
  solo se verifica el turno. Si el texto pasó por el anonimizador, la cita se restaura primero y se
  verifica después (DT18). Una cita que no aparece invalida el hallazgo. *Criterio:* pruebas con una cita
  alterada, una cita en otro turno, una cita con « […] » fuera de orden y una cita seudonimizada que se
  restaura y se verifica (AUTONOMIA-05).
- **FR4.5** El **verificador** del perfil confirma siempre cada hallazgo candidato del juez, en una
  llamada aparte. La permutación (FR10.5) añade una segunda llamada con las dos citas en el orden
  inverso, y el candidato se conserva solo si se confirma en ambos órdenes (pregunta 9, P12). Un
  candidato descartado por cita no verificable o por el verificador no llega a la consola: queda en el
  registro de la corrida con el motivo. *Criterio:* prueba con un *fake* del `ModelGateway` cuyo
  verificador rechaza un candidato.
- **FR4.6** El testimonio se trata como dato: viaja como JSON dentro del mensaje, nunca como
  instrucción; las instrucciones del sistema son una configuración de solo lectura cuyo `prompt_sha256`
  se registra en cada corrida (S12-R7). Se mide en NFR5.
- **FR4.7** El analizador no marca como contradicción la vaguedad, la emoción, los detalles periféricos
  ni las versiones de terceros (DT15). Se mide con los casos trampa del conjunto sintético (NFR4).
- **FR4.8** Con modelos locales, el análisis es **fragmentado** por turnos con solapamiento (P14); el
  tamaño de ventana y el solapamiento los fija NFR Requirements. Solo se buscan contradicciones dentro de
  cada ventana; las más distantes son una limitación declarada: la corrida registra el modo fragmentado,
  la ventana y el solapamiento, y el reporte los muestra (pregunta 11).
- **FR4.9** En la consola, el modo incremental corre **una vez por envío**: un turno escrito o dictado
  da `desde_turno = hasta_turno = n`, y un bloque pegado da una sola corrida desde su primer turno (User
  Stories, pregunta 12). El modo final se lanza con un botón tras «Finalizar sesión» (o directamente en
  una transcripción importada, FR3.6); sus hallazgos se unen a los del incremental sin duplicar: un
  hallazgo es el mismo cuando coincide el **par no ordenado** de (turno, cita normalizada en espacios), y
  si ya estaba decidido conserva su estado y su historial. El modo final se puede **relanzar** mientras la
  sesión no esté consolidada; cuenta el último lanzado, y dos lanzamientos simultáneos dan un `202` y un
  `409` (P6; User Stories, pregunta 13). *Criterio:* prueba de integración con un hallazgo repetido en
  ambos modos que aparece una sola vez.

### FR5 — Silencio Fáctico y Paquete de Contexto de Traspaso · **Retirado** (cambio 01)

Su lugar lo toma la verificación determinista de las dos citas (FR4.4, AUTONOMIA-05).

### FR6 — Revisión humana de hallazgos (MUST) · S6-P1, S8, S12-R2, preguntas 5 y 6, AUTONOMIA-03

- **FR6.1** Todo hallazgo nace `pendiente`. Solo un humano lo cambia a `aceptada`, `editada` o
  `descartada`, y solo el analista dueño de la sesión (FR1.2). «Editada» significa que el analista
  escribe **su propia reformulación**; el hecho, el tipo, las citas y las observaciones de la IA no
  cambian (pregunta 6). Antes de consolidar, la decisión se puede cambiar entre `aceptada`, `editada` y
  `descartada`, con las mismas exigencias, pero nunca vuelve a `pendiente` (Seguimiento 5). Cada cambio
  guarda actor, hora, estado anterior y estado nuevo en un historial que no se borra.
- **FR6.2** La tarjeta del hallazgo muestra las dos citas en su contexto (turno, hablante y página), el
  tipo y el hecho; las observaciones se muestran plegadas. No se puede marcar un hallazgo como
  `aceptada` ni `editada` sin haber desplegado sus observaciones (pregunta 6). *Criterio:* prueba de
  interfaz y de API (la API rechaza el cambio si no consta el despliegue).
- **FR6.3** Descartar exige una nota no vacía; aceptar o editar admite una nota opcional (pregunta 6).
- **FR6.4** Ni la salida de la IA ni la interfaz contienen etiquetas de veracidad sobre el compareciente
  («mentiroso», «falso», «miente», «verdadero», puntaje binario de verdad). El escaneo cubre las
  observaciones de los hallazgos, las observaciones al conductor y los textos de la interfaz, y solo
  excluye las dos citas literales del testimonio, el texto que escribe el analista, que el reporte
  muestra como suyo (User Stories, Seguimiento 4), y la cadena versionada del aviso de VE-01, leída del
  mismo archivo (adenda 02, A-1; precisión DD-08 de Domain Design). *Criterio:* prueba automatizada que
  falla si aparece una de esas etiquetas (AUTONOMIA-03), y un control negativo que falla si «prueba»
  aparece fuera del aviso.
- **FR6.5** La interfaz recuerda, junto a cada hallazgo, que la IA es un asistente y que el criterio del
  analista prevalece (S12-R2).

### FR7 — Consolidación, reporte y descarga (MUST) · S5-CU5, S7-J1, S8, pregunta 7, Seguimiento 1, P6, P16

- **FR7.1** Solo el analista dueño puede ejecutar «Finalizar y Consolidar» (en la consola, el botón
  «Consolidar reporte»), y solo después de «Finalizar sesión» y de que el último modo final lanzado haya
  **terminado** (P6). El botón está deshabilitado mientras haya algún hallazgo `pendiente` (Seguimiento 1)
  o algún análisis en cola o en proceso. Un modo final o un tramo incremental terminados en `error`
  **no bloquean** la consolidación: el diálogo de confirmación lo avisa y ofrece relanzar el modo final
  (User Stories, pregunta 13). *Criterio:* la API rechaza la consolidación con hallazgos pendientes, sin
  modo final lanzado o con análisis en proceso, y la acepta con un modo final en `error`.
- **FR7.2** El reporte es un Markdown con: la transcripción completa por turnos (con hablante y página);
  **todas** las sugerencias con su estado final y nota (P16); por cada una, el hecho, el tipo, las dos
  citas con turno y página, los avisos de FR4.4 y las observaciones; el perfil, `config_sha256`,
  `prompt_sha256`, la versión del analizador y el registro de modelos de cada corrida (FR15.3); el modo
  fragmentado y su ventana, si se usó; «Tramo no evaluado» por cada tramo incremental en `error` y
  «Modo final no completado. Revisión manual requerida» si el último modo final terminó en `error`, cada
  uno con su código (User Stories, pregunta 13); y quién consolidó y cuándo.
- **FR7.3** El sistema guarda el reporte en el volumen persistente y registra su SHA-256. *Criterio:*
  recalcular el SHA-256 del archivo descargado coincide con el registrado.
- **FR7.4** El analista descarga el reporte consolidado desde la interfaz.
- **FR7.5** Tras consolidar, la sesión y sus hallazgos quedan **bloqueados**. Una corrección crea una
  **versión nueva** del reporte, con nuevo SHA-256 y nueva consolidación (quién y cuándo), que referencia
  a la anterior; la anterior se conserva intacta (pregunta 7). La corrección se hace con «Corregir
  reporte», que abre una copia de trabajo donde solo cambian estados y notas; consolidarla crea la
  versión nueva (User Stories, pregunta 7).

### FR8 — Reanudación de sesión (MUST) · S7-J3, S8

- **FR8.1** El estado de la sesión se persiste en PostgreSQL en cada turno.
- **FR8.2** Si la conexión del navegador se pierde con la sesión abierta, la sesión pasa a `suspendida`
  y nada procesado se pierde.
- **FR8.3** Al volver a entrar, el analista ve el aviso de sesión interrumpida y puede reanudar desde el
  último turno registrado. *Criterio:* prueba de integración que corta la conexión a mitad de una
  transcripción y verifica 0 turnos, hallazgos o cambios de estado perdidos tras reanudar.

### FR9 — Configuración bajo control humano (MUST) · S8 WON'T, S10 §4, P8, P13; AUTONOMIA-01, AUTONOMIA-03

- **FR9.1** El sistema nunca cambia su configuración, sus perfiles ni sus *prompts* por sí mismo.
- **FR9.2** Perfiles, proveedores, *prompts*, tabla de precios (FR15.4) y límites (FR3.7) viven en
  archivos versionados y solo cambian por PR; la fusión del PR es la aprobación registrada (quién y
  cuándo) (P8, AUTONOMIA-01). *Criterio:* la API no ofrece ninguna operación que los modifique.
- **FR9.3** (SHOULD) Prometheus/Grafana muestran la razón de descartes por sesión (AIR) y alertan si una
  sesión supera el 25 % de hallazgos consecutivos descartados, como señal para revisar el *prompt* o el
  perfil por PR. No hay propuesta automática de cambios (P13).

### FR10 — Funciones SHOULD · S8

- **FR10.1** Indicadores de procesamiento en la interfaz («Procesando audio…», «Analizando
  contradicciones…») con cronómetro de latencia, y el avance del modo final.
- **FR10.2** Grabación por demanda (*push-to-talk*) en WAV/MP3 enviada por HTTP POST asíncrono y
  transcrita con Whisper ligero en CPU dentro del clúster; el turno resultante es `guiada`, sin página, y
  sigue el mismo camino que FR3.2 (P4). Se agrega cuando el flujo de texto funciona de punta a punta.
- **FR10.3** En modo incremental, el analizador puede proponer al analista **aclaraciones neutras**
  (`observaciones_conductor`) con vocabulario cerrado: `tipo: aclaracion_neutra`, un tema y los turnos.
  Nunca llevan el contenido de la contradicción ni llegan al compareciente sin la decisión del analista,
  y ningún MUST depende de ellas (DT23). *Criterio:* el esquema rechaza cualquier otro campo, y una
  prueba verifica que el tema no contiene el texto de ninguna de las dos citas (meta de 0 %, S10 §3).
- **FR10.4** Audio por demanda de la pregunta (TTS ligero en CPU), solo al pulsar «Escuchar audio».
- **FR10.5** Permutación en línea: activable por perfil, el verificador evalúa cada candidato con las dos
  citas en ambos órdenes y lo conserva solo si lo confirma en los dos, sin bloquear la interfaz (P12,
  FR4.5). En la evaluación es obligatoria (NFR4).

### FR11 — Historial de sesiones y anonimizador · S8, S6-P3; AUTONOMIA-04; P9, P10, pregunta 15

- **FR11.1** **Retirado** (cambio 01): el clasificador afectivo pasa a WON'T (DT15).
- **FR11.2** (COULD) Historial de sesiones en un panel lateral.
- **FR11.3** (**MUST**, antes COULD) **Anonimizador** con el diseño de DT18: corre siempre dentro del
  clúster; NER local más reglas; marcas coherentes en toda la entrevista (p. ej., `[PERSONA_3]`); tabla
  de correspondencia solo en memoria del clúster, nunca en logs ni en disco; restauración de las citas
  antes de verificarlas (FR4.4); y detección de marcas alteradas por el modelo, que invalida el hallazgo.
  Solo es obligatorio delante de destinos externos; con un perfil todo local no interviene (P9). Es un
  módulo de la biblioteca del analizador y entra en la **primera rebanada**, con la línea de comandos
  (User Stories, pregunta 10). Si falla,
  la llamada no sale y el tramo queda en `estado: error` (falla cerrado). *Criterios:* sobre el conjunto
  sintético, el 100 % de las entidades sembradas (nombres, lugares y números de expediente, con y sin
  tilde) sale seudonimizado: una sola fuga hace fallar la prueba (pregunta 15); una prueba verifica que,
  con el anonimizador caído, no sale ninguna llamada; otra, que una marca alterada invalida el hallazgo.
- **FR11.4** (MUST) El anonimizador impone la lista de dominios de los proveedores configurados y
  rechaza cualquier otro destino (P10). *Criterio:* prueba con un destino fuera de la lista.

### FR12 — Plataforma en el clúster · S8 §5, S13; P10

- **FR12.1** (MUST) PostgreSQL relacional con el operador CloudNativePG, sin `pgvector`; Redis como cola
  asíncrona.
- **FR12.2** (MUST) Manifiestos o chart con `resources.requests` y `resources.limits` en cada pod.
  *Criterio:* política de manifiestos (Kyverno CLI) que falla si falta alguno.
- **FR12.3** (MUST) Una `NetworkPolicy`, entregada como artefacto revisable, que niega la salida a
  internet a todos los pods salvo al anonimizador, y a este solo por el puerto 443 y DNS; la lista
  blanca de CoreDNS acompaña a la de FR11.4 (P10, AUTONOMIA-04). *Criterio:* política estática en
  nivel 0.
- **FR12.4** (MUST) Credenciales y claves de API de los proveedores en Kubernetes Secrets que crea el
  humano; los manifiestos y el archivo de perfiles solo los referencian.
- **FR12.5** (MUST) Cada servicio expone un *endpoint* de salud que responde 200 cuando está listo
  (lo usa la prueba de humo de team-practices).
- **FR12.6** (SHOULD) Despliegue GitOps con Argo CD; Prometheus y Grafana con el panel AIR.
- **FR12.7** (COULD) Autoescalado con KEDA según la longitud de la cola; perfil GPU opcional para la
  demostración. La calidad de los modelos locales grandes se mide en ZINE (FR16), no en el clúster
  local (DT26).

### FR13 — Biblioteca y línea de comandos del analizador (MUST) · S8, S9-D, S11 §4; DT26; P3, P7, P11

- **FR13.1** El núcleo del analizador es una **biblioteca de Python** sin dependencias de Redis,
  Kubernetes ni base de datos. El trabajador `semantic-agent` es una envoltura delgada que la llama desde
  la cola (P3). *Criterio:* comprobación de importaciones (import-linter) que falla si la biblioteca
  importa Redis, un cliente de Kubernetes o un controlador de base de datos.
- **FR13.2** Una **línea de comandos** analiza una transcripción o un directorio de transcripciones en el
  formato del contrato con un perfil dado, en modo final por defecto, y escribe un archivo de salida del
  contrato por entrevista en el directorio que se le indique. Termina con código 0 solo si todas las
  corridas terminan, aunque alguna tenga `estado: error`, y con otro código ante un argumento o archivo
  inválido.
- **FR13.3** La línea de comandos tiene un modo de **evaluación** que compara los hallazgos con la lista
  de contradicciones esperadas del conjunto sintético y escribe un reporte JSON con las métricas de NFR4
  (pregunta 14).
- **FR13.4** Las corridas sobre el corpus del piloto se hacen en la máquina local y escriben sus
  resultados en un directorio ignorado por Git (P7, P11). *Criterio:* `.gitignore` cubre ese directorio
  y una comprobación de nivel 0 falla si Git rastrea algún archivo dentro de él.
- **FR13.5** La consola tiene una pantalla de **solo consulta** para el rol `investigador` (FR1.2). En
  ella se suben los reportes JSON de corrida o de evaluación que produce la línea de comandos (máquina
  local o ZINE) y se validan contra su esquema. Se guardan **solo metadatos y cifras**: perfil,
  `config_sha256`, `prompt_sha256`, versiones del analizador y del conjunto, registro de modelos, *tokens*,
  costo y métricas. Los reportes se listan, se ven en detalle y se comparan de dos en dos; la pantalla no
  lanza análisis. Nunca guarda texto de transcripciones, hallazgos ni citas (NFR12). *Criterio:* una
  prueba de integración sube un reporte con un texto *canary* y comprueba que no aparece en ninguna
  columna de texto ni en los logs; otra prueba comprueba que los roles `analista` y `admin` reciben `403`
  en esas rutas (Refined Mockups, respuesta 10 y seguimiento 7; historias US12.6 y US12.7).

### FR14 — Perfiles de ejecución (MUST) · S5-CU1, S8, S11-B; DT21; P8, P9, pregunta 12

- **FR14.1** Un perfil fija, por papel (juez y verificador), proveedor, modelo, versión y parámetros
  (esfuerzo, temperatura o cuantización), si la permutación en línea está activa, el proveedor alterno
  opcional y, para modelos locales, el modo fragmentado (FR4.8). Hay al menos un perfil comercial
  (p. ej., `comercial-piloto`) y uno todo local (`todo-local`).
- **FR14.2** Cada corrida guarda la configuración efectiva y su huella `config_sha256`; dos corridas con
  la misma configuración tienen la misma huella.
- **FR14.3** Un servicio no arranca si el archivo de perfiles es inválido, si un perfil con destino
  externo no tiene el anonimizador delante (AUTONOMIA-04) o si falta la clave de API que referencia. La
  línea de comandos y la biblioteca validan el perfil igual: en esos casos terminan con código ≠ 0
  **antes** de cualquier llamada (User Stories, pregunta 10). *Criterio:* prueba de arranque, y de la
  línea de comandos, con un control negativo por cada caso.
- **FR14.4** Juez y verificador son de familias de modelos distintas. Es obligatorio en los perfiles de
  evaluación, cuya validación rechaza la misma familia. Un perfil de demostración puede usar la misma
  familia solo si lo declara explícitamente, y la consola y el reporte lo muestran como aviso
  (pregunta 12).
- **FR14.5** Al crear la sesión, la consola lista solo los perfiles aprobados e indica, por papel, si usa
  un proveedor comercial y que el texto pasa por el anonimizador (P8).

### FR15 — Interfaz de modelos (MUST) · S9-D, S12-R8, S12-R10; DT21; P15, pregunta 16

- **FR15.1** El puerto `ModelGateway` genera con papel, mensajes y esquema de salida. Tiene adaptadores
  nativos para Anthropic, Google y OpenAI (salida JSON forzada, esfuerzo y caché de *prompts* del
  proveedor) y uno compatible con la API de OpenAI para modelos locales (vLLM, llama.cpp, Ollama).
- **FR15.2** El bloqueo de contenido, el tiempo agotado y el error del proveedor son errores tipados.
  Si el perfil prevé un proveedor alterno, el analizador lo usa y lo registra; si no, la corrida termina
  en `estado: error` (FR4.2).
- **FR15.3** Cada llamada registra papel, proveedor, modelo, versión, esfuerzo o cuantización, motor,
  semilla si el proveedor la admite, *tokens* de entrada y salida, fecha y si fue al proveedor alterno
  (P15). El registro solo admite inserciones (NFR11).
- **FR15.4** Cada corrida y cada reporte de evaluación suman los *tokens* y un costo estimado según una
  tabla de precios versionada por PR. No hay tope automático en el MVP (pregunta 16).

### FR16 — Evaluación por lotes en ZINE (MUST) · S11 §4; DT26; AUTONOMIA-01

- **FR16.1** Los scripts `sbatch` y el paquete de entrada para correr la línea de comandos contra un
  modelo local servido con API compatible con OpenAI en el clúster ZINE son artefactos revisables que el
  humano lanza; ningún plan de tareas envía trabajos a ZINE (AUTONOMIA-01). En Git solo van los
  scripts `sbatch`, el script que arma el paquete y un **manifiesto** con nombres y SHA-256, sin
  contenido; el paquete se arma en un directorio ignorado por Git, y una comprobación de nivel 0 falla si
  Git rastrea algo de ese directorio (User Stories, pregunta 11).
- **FR16.2** Cada resultado de ZINE registra modelo, cuantización (Q8 o BF16 para medir capacidades),
  motor y versión, y usa solo corpus público del piloto o el conjunto sintético. *Criterio:* el paquete
  de entrada valida contra el esquema del contrato y no contiene archivos fuera de esas dos fuentes.
- **FR16.3** (**MUST**) Antes de Domain Design se **validan los modelos locales** en el clúster Ing.
  Sistemas con seis mediciones: velocidad del modelo local en un nodo, funciones de la API del servidor
  local (esquema JSON o gramática, `seed`, caché del *prompt*), *tokens* de la entrevista más larga
  frente al contexto, repetibilidad en CPU, instalación sin internet y un verificador de otra familia.
  Se hacen mientras la tarea 4L corre en segundo plano; si su medición `--array=8` no termina en el plazo
  que fija el humano, el reporte se revisa con sus cifras parciales. Los `.sbatch` de validación y el
  reporte (solo cifras) viven en `docs/validacion-zine/` por commit directo; los `.sbatch` de producción
  (FR16.1) entran por PR. Los escribe el agente y los lanza el humano (AUTONOMIA-01). *Criterio:* el
  reporte registra, por medición, el comando exacto, el ID del trabajo SLURM, el nodo y el SHA-256 del
  modelo, y lleva la línea de revisión del humano en un commit anterior al inicio de Domain Design (User
  Stories, preguntas 14, 15 y 16; US14.1).

---

## 3. Requisitos no funcionales

- **NFR1 — Soberanía de datos (MUST, AUTONOMIA-04, S6-P3).** Ningún audio crudo, transcripción sin
  seudonimizar, nombre de víctima ni identificador real del proceso sale del clúster local. Un proveedor
  externo solo recibe texto que pasó por el anonimizador, y si este falla la llamada no sale. El diseño
  declara, por componente, si corre dentro o fuera del clúster y qué datos cruzan esa frontera.
  *Criterio:* las pruebas de FR11.3, FR11.4, FR12.3 y FR14.3, más la verificación manual de la
  `NetworkPolicy` en el clúster antes de la sustentación.
- **NFR2 — CPU primero (MUST, S6-P2, S8 WON'T).** Todas las funciones MUST y SHOULD funcionan en la
  máquina de desarrollo sin GPU con el perfil `todo-local`; las suites de niveles 0 y 1 no exigen GPU.
  El perfil GPU es opcional y sus pruebas corren en una etapa separada, a demanda.
- **NFR3 — Interfaz no bloqueante (MUST, S6-P2).** No hay llamadas síncronas de punta a punta desde la
  interfaz al procesamiento de IA; la interfaz responde mientras un análisis se procesa. Las latencias por
  turno y por modo final, y el *N* de la prueba de humo, se recalculan en NFR Requirements con juez,
  verificador, anonimizador y red (conflicto C3); para la voz (SHOULD) se aceptan 8–12 s de
  transcripción por turno en CPU.
- **NFR4 — Calidad de la IA sobre el conjunto sintético (MUST, nivel 2, S10 §3, S11; P11, P14, P15,
  preguntas 11 y 14).** El conjunto sintético versionado en `evaluation/` trae relatos con contradicciones
  internas sembradas de los 7 tipos, relatos coherentes y casos trampa (vaguedad, emoción, detalle
  periférico, versión de terceros), cada muestra con la lista exacta de contradicciones esperadas y sus
  dos citas. La línea de comandos en modo evaluación (FR13.3) mide, con cualquier perfil:
  - **100 %** de citas verificadas en los hallazgos emitidos;
  - **0 %** de error de formato JSON;
  - permutación aplicada en el **100 %** de las consultas *offline* y consistencia **> 65 %** al invertir
    el orden;
  - precisión y sensibilidad, contando un acierto cuando el hallazgo cita **el mismo par de turnos** que
    una contradicción esperada (sin importar el orden); el acuerdo de tipo se reporta aparte, y todo
    hallazgo en un relato coherente o en un caso trampa es un falso positivo (pregunta 14);
  - acuerdo entre **3 corridas** del mismo perfil (P15);
  - en modo fragmentado, sensibilidad según la distancia entre las dos citas (pregunta 11).

  Los umbrales de precisión, sensibilidad y acuerdo, y la composición del conjunto, los fija NFR
  Requirements. El reporte JSON registra la versión del conjunto, `prompt_sha256`, el perfil con su
  `config_sha256`, los modelos por llamada, *tokens*, costo estimado y las métricas. La corrida sobre las
  10 entrevistas del piloto, fuera de Git, es una prueba de humo frente a sus 4 contradicciones y no mide.
  La precisión frente a un panel humano se mide en el repositorio principal del TG (DT09).
- **NFR5 — Resistencia adversarial (MUST, nivel 2, S11 §3).** Escenario A: añadir el texto de inyección
  del PRD a cada transcripción del conjunto no cambia el conjunto de hallazgos respecto a la versión sin
  inyección. Escenario B: las transcripciones sintéticas se generan con una familia distinta a la del juez
  y a la del verificador, que a su vez son de familias distintas (FR14.4), y el reporte de evaluación
  declara la familia de cada papel. Escenario C: permutación de las dos citas (FR4.5, NFR4).
- **NFR6 — Explicabilidad (MUST, S11 §2.3).** Dos evaluadores (el autor y un par del curso) califican la
  claridad de las observaciones de los hallazgos sobre el conjunto sintético en escala Likert de 1 a 5;
  el promedio es ≥ 4.5.
- **NFR7 — MTTV (MUST, S10 §1).** El tiempo medio desde «Finalizar sesión» hasta «Finalizar y
  Consolidar» es < 10 minutos por transcripción del conjunto sintético, calculado con las marcas de hora
  que guarda el sistema. La línea base del cotejo manual queda como «[VERIFICAR] sin fuente directa».
- **NFR8 — Éxito del pipeline (MUST, S10 §2, pregunta 8).** En la máquina de CPU, al menos 50 sesiones de
  texto sobre el conjunto sintético, en tandas de **3 sesiones concurrentes**, terminan de punta a punta
  (incluido el modo final) sin `OOMKilled` ni *timeout* en ≥ 98 % de los casos (como máximo 1 fallo cada
  50). El reporte declara el perfil usado.
- **NFR9 — Indexación del escenario.** **Retirado** (cambio 01).
- **NFR10 — Seguridad de la aplicación (MUST).** Entradas validadas en las fronteras; contraseñas solo
  con hash (FR1.1); credenciales y claves de API solo por referencia a Secrets (FR12.4); *prompts* del
  sistema como configuración de solo lectura; un destino externo exige el anonimizador o el servicio no
  arranca (FR14.3); la tabla de correspondencia del anonimizador nunca se registra ni se persiste; los
  logs contienen solo identificadores, nunca texto de testimonio ni nombres; toda E/S tiene *timeout*
  explícito; un error se devuelve como Problem Details (RFC 9457) con `code` estable y `detail` en
  español.
- **NFR11 — Integridad y auditoría (MUST, AUTONOMIA-03).** Los historiales de estado de hallazgos,
  consolidaciones, versiones de reporte, corridas y registro de llamadas a modelos solo admiten
  inserciones. *Criterio:* prueba de integración que intenta modificar o borrar una fila de cada
  historial y falla.
- **NFR12 — Datos reales fuera del repositorio (MUST, S8 WON'T, `project.md`, P7).** Ni el repositorio
  ni la CI contienen testimonios, audios, nombres ni expedientes reales, ni fragmentos o codificaciones del
  piloto; las pruebas y los *fixtures* usan transcripciones sintéticas. Las entrevistas del piloto solo se
  procesan en la máquina local (CLI o consola en Minikube) y en el clúster ZINE, empaquetadas fuera de Git
  (FR16.1); del clúster solo salen cifras, y los resultados quedan fuera de Git (FR13.4; User Stories,
  pregunta 11).
- **NFR13 — Calidad del código (MUST, team-practices).** 80 % de líneas por servicio Python, por la
  biblioteca del analizador y por el frontend, y 100 % de ramas en los módulos guardia (verificación de
  citas, validación y máquina de estados del hallazgo, consolidación del reporte, anonimizador), medido en
  CI y bloqueante.
- **NFR14 — Idioma (MUST, team-practices).** Todos los textos visibles, mensajes de error y reportes
  están en español; los identificadores del código siguen el glosario único en inglés.
- **NFR15 — Observabilidad (SHOULD, S8 §5).** Métricas de CPU de los pods de IA, latencia por análisis,
  *tokens* por proveedor y razón de descartes (AIR) en Prometheus y Grafana.

---

## 4. Restricciones

- **AUTONOMIA-01..05** (`docs/limite-autonomia.md`, `team.md`) son bloqueantes en todas las etapas.
  Ningún plan de tareas aplica cambios al clúster ni envía trabajos a ZINE sin aprobación humana
  registrada: el destino es un PR o un artefacto revisable.
- **Construcción por Bolts tras `Approve Plan`**, que elige solo el humano después de revisar el plan de
  tareas de cada unidad; en Construction, «Review each checkpoint» (`team.md`).
- **Repositorio público:** nada de `/insumos` entra al repositorio, salvo el contrato común y los ID de
  decisión del TG.
- **Contrato común** v0.1 del cambio 01: su fuente de verdad es el repositorio principal del TG; Veridicus
  lo implementa primero y Contract Design lo fija aquí.
- Kubernetes local (Minikube) para el producto; clúster ZINE (SLURM, solo CPU) solo para medir la calidad
  de modelos locales por lotes. Todo funciona en CPU; GPU solo como perfil opcional (hasta 4 GPU y 32 GB
  de RAM).
- Pila: FastAPI (Python 3.12), biblioteca del analizador en Python 3.12, React con TypeScript estricto,
  Whisper ligero (`tiny`/`base`) en CPU, juez local cuantizado de demostración en CPU [VERIFICAR:
  Qwen2.5-7B Q4 del diseño de NFR aprobado], proveedores comerciales por papel tras el anonimizador,
  PostgreSQL con CloudNativePG y Redis (S9).
- Monorepo, CI, imágenes en GHCR privado, migraciones como `Job` aparte y Secrets por referencia, según
  team-practices.
- Entrega alineada con los módulos 6–8 del curso y la sustentación de la sesión 16 (S13).

---

## 5. Supuestos

- La transcripción de audio es un paso externo ya probado; el MVP opera sobre texto en español (S8,
  S12-R3).
- El conjunto sintético se construye antes de la primera evaluación de nivel 2, con un modelo generador
  de una familia distinta a la del juez y a la del verificador (S11-B).
- El contrato común puede cambiar al aprobarse en el repositorio principal; un cambio entra a Veridicus
  como cambio de requisitos.
- El acceso a ZINE llega a finales de octubre de 2026; hasta entonces, el modo local se prueba con un
  modelo pequeño en la máquina del investigador.
- En la sustentación trabaja un solo analista; la concurrencia de 3 sesiones (NFR8) es una prueba de
  carga, no un uso real.
- Una marca de hablante en el texto pegado es un prefijo de línea del tipo `Nombre:`; Functional Design
  fija el formato exacto (FR3.3).
- El riesgo de reidentificación por el contenido del relato no desaparece con la seudonimización (DT18);
  el PRD lo declara.

---

## 6. Fuera de alcance

- Todo lo marcado WON'T en el PRD (S8 §4): voz en tiempo real por *streaming*; servidores GPU dedicados
  como requisito; la clasificación afectiva o estilométrica, incluidos LieXBerta y el clasificador
  afectivo ligero (DT15); el contraste frente a un marco de verdad documental (escenarios, *embeddings*,
  `pgvector`, umbral de similitud, Hecho No Documentado, Paquete de Contexto de Traspaso), que es otro
  analizador posible del TG (DT24); datos judiciales reales; firma criptográfica por analista; cambio
  automático de configuración.
- Con modelos locales, las contradicciones entre turnos más distantes que la ventana del modo
  fragmentado (pregunta 11): limitación declarada y medida.
- La precisión del analizador frente a un panel humano y la lista de referencia del TG: se miden en el
  repositorio principal (DT09).
- Un tope automático de *tokens* o de costo (pregunta 16).
- Como **criterios de aceptación**, las métricas de adopción del PRD: uso semanal > 85 % y tasa de
  desestimación < 15 % en producción. Quedan como hipótesis de producto para el TG (pregunta 8).
- La codificación de tipos de pregunta (95 % de acuerdo) y toda pregunta confrontativa al compareciente
  (DT23).
- Argo Workflows y el procesamiento *batch* de audios largos descritos en el PVB.

---

## 7. Preguntas abiertas para etapas posteriores

| Pregunta | Etapa que la cierra |
|---|---|
| Umbrales de precisión, sensibilidad y acuerdo entre 3 corridas; composición del conjunto sintético | NFR Requirements |
| Tamaño de ventana y solapamiento del modo fragmentado | NFR Requirements |
| Cifras del catálogo de límites (caracteres, turnos, tamaño del reporte) | NFR Requirements |
| Latencias por turno y por modo final con juez, verificador y anonimizador; *N* de la prueba de humo (C3) | NFR Requirements |
| Modelos concretos de cada perfil y modelo local de demostración | NFR Requirements |
| Esquema exacto del contrato común, del perfil y del registro de llamadas | Contract Design |
| Si la biblioteca del analizador es una unidad propia y su orden de Bolts (P3) | Units Generation / Delivery Planning |
| Formato exacto de la marca de hablante al dividir texto pegado | Functional Design |
| Cómo detecta el sistema la pérdida de conexión que suspende una sesión | Functional Design |
| Política de contraseñas y duración de la sesión web | NFR Requirements |
| ~~Nivel de accesibilidad de la interfaz (no lo fija el PRD)~~ Cerrada en User Stories: WCAG 2.1 AA (SHOULD) con axe, flujo de texto solo con teclado y estados no solo por color (Seguimiento 3) | User Stories |
| Distribución de Kubernetes, CNI y lista blanca de CoreDNS en cada máquina | Infrastructure Design |

---

## 8. Trazabilidad

| Requisito | Estado en la revisión 2 | Origen |
|---|---|---|
| FR1 | Cambia (matriz y auditoría) | S8 MUST (inicio de sesión y roles), S9-B; pregunta 5; P8 |
| FR2 | **Retirado** | S8 WON'T (contraste documental), DT24 |
| FR3 | Cambia; entran FR3.6 y FR3.7 | S5-CU1, S8 MUST (texto), S6-P2; pregunta 2; P4, P5, P8; pregunta 13 |
| FR4 | Se reescribe | S5-CU3, S6-P4, S9-D, S11 §2–3, S12-R7, S7-J4; AUTONOMIA-05; preguntas 9–11; P6, P12, P14; contrato común |
| FR5 | **Retirado** | Cambio 01 §2; AUTONOMIA-05 reescrita |
| FR6 | Se mantiene con ajustes | S6-P1, S8 MUST (edición de alertas), S12-R2, S12-R6; preguntas 5 y 6; AUTONOMIA-03 |
| FR7 | Cambia (contenido del reporte, modo final) | S5-CU5, S7-J1 (paso 6), S8 MUST; pregunta 7, Seguimiento 1; P6, P16; AUTONOMIA-03 |
| FR8 | Se mantiene | S7-J3, S8 MUST (reanudación) |
| FR9 | Cambia (sin umbral; configuración por PR; AIR como señal) | S8 WON'T (cambio automático), S10 §4; P8, P13; AUTONOMIA-01, AUTONOMIA-03 |
| FR10 | Cambia FR10.1, FR10.3 y FR10.5 | S8 SHOULD, S5-CU2, S11-C; DT23; P4, P12 |
| FR11 | FR11.1 **retirado**; FR11.3 sube a MUST; entra FR11.4 | S8, S6-P3, S12-R5; AUTONOMIA-04; DT18; P9, P10; pregunta 15 |
| FR12 | Cambia FR12.1, FR12.3, FR12.4 y FR12.7 | S8 §5, S7-J2, S13; AUTONOMIA-04; P10 |
| FR13 | Nuevo; FR13.5 entra por Refined Mockups (2026-11-03) | S8 MUST (analizador), S9-D, S11 §1 y §4; DT26; P3, P7, P11; pregunta 14; Refined Mockups, respuesta 10 y seguimiento 7 |
| FR14 | Nuevo | S5-CU1, S8 MUST (perfiles), S11-B; DT21; AUTONOMIA-04; P8, P9; pregunta 12 |
| FR15 | Nuevo | S9-D, S12-R8, S12-R10; DT21; P15; pregunta 16 |
| FR16 | Nuevo; FR16.3 entra por User Stories (2026-11-02) | S8 WON'T (GPU: ZINE), S11 §4; DT26; AUTONOMIA-01; User Stories, preguntas 11 y 14–16 |
| NFR1 | Se reescribe | S6-P3, S7-J2 (paso 3); AUTONOMIA-04 |
| NFR2, NFR3 | Se mantienen (latencias por recalcular) | S6-P2, S8 WON'T (GPU); team-practices |
| NFR4 | Se reescribe | S10 §3, S11 §1–2, S11-C; P11, P14, P15; preguntas 11 y 14; team-practices (nivel 2) |
| NFR5 | Cambia (escenarios B y C) | S11 §3 (A, B, C); pregunta 12 |
| NFR6 | Se mantiene (sobre las observaciones) | S11 §2.3 |
| NFR7 | Se mantiene (conjunto sintético) | S10 §1 |
| NFR8 | Cambia (modo final, perfil declarado) | S10 §2; pregunta 8 |
| NFR9 | **Retirado** | Cambio 01 §2 |
| NFR10 | Cambia | S12-R7; AUTONOMIA-04; team-practices (Code Style, Deployment) |
| NFR11 | Cambia (corridas y registro de modelos) | S6-P1; AUTONOMIA-03; DT21 |
| NFR12 | Cambia (piloto en la máquina local y en ZINE, fuera de Git) | S8 WON'T (datos reales); `project.md`; P7; User Stories, pregunta 11 |
| NFR13 | Cambia (módulos guardia) | team-practices; `team.md` Testing Posture |
| NFR14 | Se mantiene | team-practices |
| NFR15 | Cambia (*tokens*, AIR como señal) | S8 §5, S13 §4; P13 |
