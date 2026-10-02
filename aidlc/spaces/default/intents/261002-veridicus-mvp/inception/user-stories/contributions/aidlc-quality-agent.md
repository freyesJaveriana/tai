**Collaborator:** aidlc-quality-agent

## Contribution

Ángulo: comprobabilidad de los criterios de aceptación. Reviso el borrador de `stories.md` contra
`requirements.md`, team-practices (niveles 0–3, dobles de prueba, mapa AUTONOMIA) y las respuestas P1–P8.
No reabro ninguna decisión del Q&A; las propuestas solo vuelven medibles los criterios ya decididos.

### 0. Convenciones propuestas para todo `stories.md`

- **C1. Etiqueta de nivel en cada AC.** Cada criterio termina con su nivel: `[N0]` (unitaria, contrato,
  política estática, con *fakes* deterministas del LLM y de los *embeddings*), `[N1]` (integración con
  PostgreSQL + `pgvector` y Redis reales, LLM y *embeddings* aún *fake*), `[N2]` (Golden Dataset con el
  modelo real, temperatura 0 y semilla fija), `[N3]` (Playwright E2E o humo) o `[Manual]`. Un criterio que
  depende del comportamiento real del LLM **nunca** lleva `[N0]` ni `[N1]` solo: se parte en una variante
  determinista (con *fake*) y otra `[N2]`.
- **C2. «El sistema no lo permite» / «la API rechaza» siempre nombra el estado HTTP y un `code` estable de
  Problem Details en español.** Propuesta de reparto, para que Functional Design la confirme: `401` sin
  autenticación; `403` rol o propiedad; `409` conflicto de estado (sesión finalizada o consolidada, alertas
  pendientes, CoT no desplegada); `413` tamaño; `415` formato; `422` validación (codificación, nota vacía,
  campos inmutables). Cada AC de rechazo afirma: estado HTTP, `code` y que **no cambió ninguna fila**
  (conteo antes = conteo después).
- **C3. Vocabulario prohibido y glosario versionados.** La lista de AC5.5.1 vive en un archivo de
  `contracts/` (con variantes de género, número y tiempo: «mentiroso/a/os/as», «miente», «mintió», «falso/a/os/as»,
  «verdadero/a», «veraz», «verdad: sí/no»), y tanto las pruebas como el escaneo la leen de ahí.
- **C4. Toda prueba guardia tiene un control negativo.** Para cada política estática o escáner (vocabulario,
  `NetworkPolicy`, `requests/limits`, Secrets, migraciones, CI sin despliegue) existe un *fixture* que
  viola la regla y la prueba verifica que el chequeo **falla** sobre él. Sin eso, una política vacía pasaría.

### 1. Épica 1 — Escenario de control

- **AC1.1.1 (reescrito)** Given un archivo Markdown UTF-8 de exactamente 1 048 576 bytes (1 MiB; el tamaño
  exacto lo confirma Functional Design, pero el AC fija el número), When lo cargo, Then responde éxito, se
  guardan ≥ 1 pasajes en `pgvector` con la versión del escenario y el estado es «listo para contrastación». `[N1]`
  (el tiempo < 3 min es NFR9, diferido).
- **AC1.1.2 (partido en cuatro casos con su código)** Given (a) 1 048 577 bytes → `413`; (b) un archivo con
  extensión `.md` cuyo contenido empieza por `%PDF` → `415`; (c) un archivo Latin-1 que contiene bytes no
  válidos en UTF-8 (p. ej. `0xE9` de «é»; un Latin-1 solo ASCII sería UTF-8 válido y no prueba nada) → `422`;
  (d) un archivo de 0 bytes → `422`. Then mensaje en español y **0 pasajes** guardados para ese intento. `[N0]` validación + `[N1]` conteo de filas.
- **AC1.1.4 (reescrito)** Given un *fake* de *embeddings* que falla en el pasaje *k* > 1, When termina la
  indexación, Then hay 0 pasajes de esa versión en la base (transacción completa o nada), la versión queda en
  `error` y no aparece seleccionable en el catálogo. `[N1]`
- **AC1.2.2 (reescrito)** Given cualquier versión, When envío `PUT`, `PATCH` o `DELETE` sobre un pasaje o una
  versión, Then responde `405` o `404` (la ruta no existe en el OpenAPI) **y** el usuario de base de datos de
  la aplicación no tiene `UPDATE` ni `DELETE` sobre la tabla de pasajes (una sentencia directa falla). `[N0]` enumeración del OpenAPI + `[N1]` permisos.
- **AC1.2.4 (nuevo, pregunta al lead)** Given un documento con el mismo SHA-256 que una versión existente,
  When lo cargo como versión nueva, Then el comportamiento queda definido (rechazo `409` o versión nueva);
  hoy ningún AC lo fija.
- **AC1.3.3 (nuevo)** Given una versión en indexación (`procesando`), When abro el catálogo, Then se ve pero
  no se puede elegir, y `POST /sessions` con su ID responde `409`. `[N1]`

### 2. Épica 2 — Sesión e ingreso

- **AC2.1.2 (reescrito para que sea ejecutable)** Given una sesión S1 creada con umbral T1 y el servicio
  reiniciado con umbral T2 ≠ T1, When se evalúa en S1 una afirmación con similitud entre T1 y T2, Then el
  resultado corresponde a T1; y una sesión S2 creada después guarda T2. `[N1]` (cubre «umbral leído de
  configuración» del mapa AUTONOMIA-05).
- **AC2.1.4 (nuevo, celdas «No» de FR1.2)** Given un usuario `admin`, When intenta enviar un turno, pegar
  una transcripción o «Finalizar sesión», Then `403` con Problem Details en español y 0 filas nuevas. `[N1]`
- **AC2.1.5 (nuevo, propuesta)** Given una sesión de otro analista, When intento enviar un turno o
  finalizarla, Then `403`. La matriz de FR1.2 no lo dice de forma explícita; lo propongo por coherencia con
  la propiedad de FR6.1 y FR7.1 — el lead decide si entra.
- **AC2.2.1 (añadido)** Given 10 envíos concurrentes a la misma sesión, When terminan, Then los turnos
  quedan numerados 1..10 sin huecos ni duplicados. `[N1]`
- **AC2.2.2 (reescrito; «responde sin esperar» no es medible)** Given un juez *fake* que bloquea el
  procesamiento hasta que la prueba lo libera, When envío un segundo turno y consulto una alerta existente,
  Then el `POST` del turno responde `202` y el `GET` de la alerta `200` **antes** de liberar el juez. `[N1]`
  La latencia máxima por turno la fija NFR Requirements (NFR3) y no entra en este AC.
- **AC2.2.3** sin cambios; nivel `[N0]` (contrato del mensaje de la cola), con un mensaje mal formado que el
  consumidor rechaza sin crear filas.
- **AC2.3.2 (partido)** (a) Given una transcripción del Golden Dataset y el juez *fake*, When la proceso
  pegada y turno a turno, Then los conjuntos de resultados son iguales comparando la tupla (número de turno,
  fragmento, ID de documento, calificación, tipo de resultado) y excluyendo IDs y horas. `[N1]` (b) La misma
  igualdad con el modelo real. `[N2]`
- **AC2.4.1 (añadido)** Given una sesión finalizada, When envío otro turno, Then `409` y 0 turnos nuevos; y la
  hora de inicio de MTTV es no nula y en UTC. `[N1]`

### 3. Épica 3 — Validación y alertas

- **AC3.1.1 (niveles)** `[N0]` en la función de decisión del dominio con recuperador y juez *fake*; `[N1]`
  con vectores sembrados en `pgvector` real de similitud coseno conocida; `[N2]` sobre el Golden Dataset
  (NFR4). Debe nombrar cómo se define la similitud (p. ej. `1 − distancia coseno` de `<=>`) para que el
  borde de AC4.1.x sea reproducible.
- **AC3.1.2 (ampliado)** «Falta» incluye ausente, `null`, cadena vacía y solo espacios; y un ID de documento
  que no pertenece a la versión de escenario de la sesión también se rechaza. Cuatro pruebas por campo como
  mínimo `[N0]` contrato + restricción `NOT NULL`/`CHECK` en base `[N1]`.
- **AC3.1.4 (partido; hoy depende del LLM real)** (a) Given una CoT cuyo esquema exige referencias a pasajes,
  When una referencia apunta a un pasaje fuera de la versión de la sesión, Then la salida se rechaza y no hay
  alerta. `[N0]` (b) 100 % de trazabilidad factual de la CoT sobre el Golden Dataset. `[N2]`
- **AC3.2.1 (casos enumerados)** El juez *fake* devuelve: (a) texto que no es JSON; (b) JSON sin un campo
  obligatorio; (c) una calificación fuera del enum (p. ej. `"falso"`); (d) tres afirmaciones de las que una
  está mal formada; (e) *timeout*. Then 0 alertas para todo el turno (sin alerta parcial en el caso d), turno
  en `error` y un `code` estable distinto para formato inválido y para *timeout*. `[N0]`
- **AC3.2.3 (nuevo)** Given un turno en `error` reenviado dos veces, When termina, Then no hay alertas
  duplicadas (idempotencia por turno). `[N1]`
- **AC3.3.1 (re-nivelado)** La prueba de inyección del Escenario A es `[N2]` sobre **todas** las
  transcripciones (NFR5), no sobre un turno; con un *fake* no prueba nada. Variante `[N0]`: el constructor del
  *prompt* coloca el testimonio solo en el campo de datos delimitado y nunca en la sección de instrucciones.
- **AC3.3.2 (reescrito, sin «inspecciono»)** (a) La política de manifiestos falla si el *prompt* del sistema
  no está montado `readOnly: true` desde un `ConfigMap`. `[N0]` (b) Con el usuario de base de datos del juez,
  `INSERT`/`UPDATE`/`DELETE` sobre cualquier tabla y `SELECT` sobre tablas fuera del marco de verdad fallan. `[N1]`

### 4. Épica 4 — Silencio Fáctico (AUTONOMIA-05)

- **AC4.1.1 (borde fijado)** Borde de tres puntos `umbral − δ`, `umbral` y `umbral + δ`, con δ = 10⁻⁶ en
  `[N0]` (recuperador *fake*) y δ = 0,01 en `[N1]` (vectores sembrados en `pgvector`).
- **AC4.1.6 (nuevo, la prueba guardia central)** Given un juez *fake* forzado a calificar **toda** afirmación
  como «incongruente» y una similitud de `umbral − δ`, When se evalúa el turno, Then 0 alertas, 0 preguntas
  sugeridas y 1 Paquete de Contexto de Traspaso. `[N0]` y `[N1]`. Sin esta prueba, AC4.1.1 podría pasar solo
  porque el juez *fake* nunca devuelve «incongruente».
- **AC4.1.7 (nuevo)** Given similitud `umbral + δ` y calificación «congruente», Then 0 alertas y 0 paquetes. `[N0]`
- **AC4.1.8 (pregunta al lead, no reabre P4)** Given similitud en o sobre el umbral y el juez califica
  «no documentada», Then ¿entra al paquete o no produce nada? P4 define «no documentada» por debajo del
  umbral; este caso no tiene regla y la máquina de decisión necesita 100 % de ramas.
- **AC4.1.3 (bordes)** Para el turno 1, 2 y 3, el paquete trae 0, 1 y 2 turnos previos; desde el turno 4,
  exactamente 3. Si el escenario tiene menos de 3 pasajes, trae todos los que hay. Los pasajes van ordenados
  por coeficiente descendente. El texto del aviso se compara carácter por carácter. Paquete `[N0]`, aviso en
  la interfaz `[N0]` (Vitest) y `[N3]`.
- **AC4.1.5 (niveles)** `[N2]` sobre el Golden Dataset y `[N3]` en `frontend/e2e/smoke.spec.ts`.
- **AC4.2.1 / AC4.2.2 (casos enumerados)** Nombre de la variable fijado (p. ej.
  `VERIDICUS_SIMILARITY_THRESHOLD`, según glosario). Casos: ausente, vacía, `abc`, `NaN`, por debajo del mínimo
  y por encima del máximo → el cargador de configuración falla `[N0]` y el proceso termina con código ≠ 0 sin
  escribir el valor ni texto sensible en el log `[N1]`; los valores en el mínimo y en el máximo se aceptan
  `[N0]`. El rango válido lo fija NFR Requirements, pero el AC exige probar sus dos extremos.

### 5. Épica 5 — Revisión humana (AUTONOMIA-03)

- **AC5.1.1 (ampliado)** Aplica a `aceptada` **y** a `editada` (FR6.2). La API responde `409` si no consta
  el evento de despliegue de la CoT y `200` después de registrarlo. Interfaz `[N0]` (Vitest), API `[N1]`. Dejar
  explícito que «descartada» no exige despliegue (FR6.2 no lo pide), para que nadie lo pruebe al revés.
- **AC5.1.4 (nuevo)** Given la tabla de transiciones de la alerta que fije Functional Design, When pido una
  transición fuera de ella (p. ej. volver a `pendiente`), Then `409`. Necesario para el 100 % de ramas de la
  máquina de estados. `[N0]`
- **AC5.1.3 (concretado)** El recordatorio es un texto fijo del glosario y una prueba Vitest verifica que
  aparece en cada tarjeta de alerta. `[N0]`
- **AC5.2.1 (añadido)** Una reformulación vacía o solo de espacios → `422`. `[N0]`
- **AC5.2.2 (reescrito)** El SHA-256 de (fragmento, cita, ID de documento, CoT) es idéntico antes y después
  de editar; y una petición que intenta cambiar alguno de esos campos responde `422` sin cambiar nada. `[N1]`
- **AC5.3.1 (reescrito)** Nota ausente, vacía o solo de espacios → `422` y la alerta sigue `pendiente`. `[N0]` + `[N1]`
- **AC5.5.1 (reescrito)** Given la lista de C3, When corre el escaneo, Then 0 coincidencias (sin distinguir
  mayúsculas ni tildes, por palabra completa) en: salida del juez sobre *fixtures* `[N0]` y sobre todo el
  Golden Dataset `[N2]`; cadenas de la interfaz `[N0]`; reporte Markdown generado `[N1]`; interfaz renderizada
  `[N3]`. Se excluyen solo los campos de cita literal (fragmento del testimonio y cita del escenario).
  **Control negativo:** una CoT *fixture* que dice «el compareciente miente» hace fallar el escaneo, y la
  palabra «falso» dentro de una cita literal no lo hace. Pregunta al lead: ¿la reformulación del analista
  (texto humano) se escanea o se excluye?
- **AC5.5.2 (reescrito)** El esquema de la alerta tiene `additionalProperties: false` y su lista de campos es
  exactamente la acordada; un JSON con un campo extra (p. ej. `is_truthful`) se rechaza. `[N0]`
- **AC5.5.3** El enum de calificación tiene exactamente tres valores. `[N0]`

### 6. Épica 6 — Consolidación (AUTONOMIA-03)

- **AC6.1.1 (ampliado)** También se rechaza (`409`) consolidar una sesión no finalizada (FR7.1 lo exige y
  ningún AC lo cubre).
- **AC6.1.5 (nuevo, hueco entre AC2.4.2 y FR7.5)** Given una sesión finalizada con algún turno en `en cola` o
  `procesando`, When intento consolidar, Then `409`; si no, una alerta que llega después quedaría dentro de una
  sesión bloqueada. Pregunta al lead: ¿cómo aparecen en el reporte los turnos en `error`? `[N1]`
- **AC6.1.6 (nuevo)** Given dos peticiones de consolidación simultáneas, Then exactamente una `200` y otra
  `409`, y un solo reporte con un solo SHA-256. `[N1]`
- **AC6.1.7 (nuevo)** Given un usuario `admin` o una identidad de servicio (trabajador, agente), When intenta
  consolidar, Then `403`: solo un analista humano dueño consolida. `[N1]` (celda «No» de FR1.2 para `admin`).
- **AC6.1.3** `[N1]` recalculando el SHA-256 del archivo guardado; en el clúster, `[N3]`.
- **AC6.2.1** API `[N1]` y descarga real con Playwright `[N3]`. **AC6.2.2** → `404` o `409` con `code`.
- **AC6.3.1 / AC6.3.2** «No lo permite» → `409` (sesión consolidada) y `422` (campo no editable en la copia
  de trabajo), sin cambios en filas. **AC6.3.3** añade: los bytes del reporte anterior recalculan el mismo
  SHA-256 tras crear la versión nueva. `[N1]`

### 7. Épica 7 — Reanudación

- **AC7.1.1 (medible)** Given el mecanismo de detección que fije Functional Design (pendiente según
  `requirements.md`), When se corta la conexión, Then la sesión pasa a `suspendida` en ≤ *T* s, con *T* fijado
  allí. `[N1]`
- **AC7.1.3 (ampliado)** Conteos de turnos, alertas y filas de historial iguales antes del corte y después
  de reanudar, **y 0 duplicados**: con un trabajador que muere a mitad de un turno, ese turno se procesa
  exactamente una vez (la cola de Redis entrega al menos una vez). `[N1]`
- **AC7.1.4 (nuevo)** Reanudar la sesión de otro analista → `403`. `[N1]`

### 8. Épica 8 — Acceso y administración

- **AC8.1.0 (nuevo)** Given cada ruta del OpenAPI salvo inicio de sesión y salud, When llamo sin token, Then
  `401`. `[N1]`
- **AC8.1.2 (reescrito)** Usuario inexistente y contraseña errónea producen el mismo estado y el mismo cuerpo
  byte a byte. `[N1]`
- **AC8.1.3 (reescrito)** Con una contraseña única sembrada, una búsqueda en todas las columnas de texto y en
  los logs capturados da 0 coincidencias, y el hash tiene el prefijo de un algoritmo adaptativo con sal. `[N1]`
- **AC8.1.4 (reescrito)** Un `INSERT` con actor u hora nulos falla en cada tabla de FR1.3. `[N1]`
- **AC8.1.5 (nuevo, NFR11 y mapa AUTONOMIA-03)** Given una fila de historial de estados de alerta, de
  consolidación, de versiones de reporte o de umbral de sesión, When intento `UPDATE` o `DELETE` con el
  usuario de la aplicación, Then falla. `[N1]` Ninguna historia lo cubre hoy, y es la base de auditoría de
  AUTONOMIA-03.
- **AC8.1.6 (nuevo, AUTONOMIA-04 sin depender del COULD)** Given un turno con un *canary* único sembrado,
  When termina su procesamiento, Then el *canary* no aparece en ningún log capturado de ningún servicio. `[N1]`
- **AC8.2.3 (ampliado)** El token vigente de un usuario desactivado recibe `401` en su siguiente petición. `[N1]`
- **AC8.3.2 (re-nivelado)** Es evidencia de proceso, no prueba del sistema: `[Manual]`, con el `git log` del
  PR adjunto como evidencia.
- **AC8.3.3 (concretado)** El OpenAPI no tiene ninguna ruta que escriba el umbral `[N0]` (esto cubre la celda
  «Aplicar un cambio de umbral: `analista` No» de FR1.2), y Playwright recorre la consola con ambos roles sin
  encontrar el control `[N3]`.
- **AC8.3.4 (concretado)** Regla estática (Semgrep o import-linter) que falla si un módulo fuera del cargador
  de configuración escribe el ajuste, con su control negativo. `[N0]`

### 9. Épica 9 — Plataforma

- **AC9.1.1 (concretado)** Los pods con datos sin anonimizar se identifican por una etiqueta obligatoria de
  clasificación; la política falla si un pod no tiene la etiqueta o si un pod sensible no está cubierto por
  una `NetworkPolicy` de salida denegada. Con control negativo. `[N0]`
- **AC9.1.2 (concretado)** `[Manual]`: desde cada pod sensible, `curl -m 5` a un *host* público termina con
  código ≠ 0, **y** el mismo pod sí alcanza PostgreSQL y Redis del clúster (control positivo: la política no
  rompe todo). Solo lectura, sin `apply` (AUTONOMIA-01).
- **AC9.1.3 (re-nivelado)** `[Manual]` en la compuerta de Infrastructure Design: cada componente de `deploy/`
  aparece en la tabla de fronteras (dentro/fuera del clúster, datos que cruzan).
- **AC9.1.4 (nuevo, AUTONOMIA-04)** La configuración rechaza al arrancar cualquier URL de LLM o de
  *embeddings* que no sea interna del clúster mientras no exista el anonimizador. `[N0]`
- **AC9.2.1 (ampliado)** Con PostgreSQL caído, el *endpoint* de salud **no** responde 200. `[N1]`
- **AC9.2.2** El *N* del *spec* de humo queda pendiente de NFR Requirements; el AC lo referencia. `[N3]`
- **AC9.3.2 (reescrito)** Política que falla si una variable con nombre que contiene `PASSWORD`, `TOKEN`,
  `KEY` o `SECRET` usa `value` literal en vez de `secretKeyRef`/`envFrom`; y `gitleaks` termina con código 0.
  Ambos con control negativo. `[N0]`
- **AC9.4.2 (concretado)** Política que falla si un `Deployment` o un `initContainer` ejecuta el comando de
  migraciones; las migraciones solo existen como `Job`. `[N0]`
- **AC9.5.1 (nuevo, mapa AUTONOMIA-01)** Given `.github/workflows/` y `scripts/`, When corre la comprobación
  estática, Then ninguno contiene `kubectl apply`, `helm install`, `helm upgrade`, `terraform apply` ni
  migraciones contra el clúster, y ningún *workflow* referencia un `kubeconfig`. Con control negativo. `[N0]`
  El mapa de team-practices lo exige y ninguna historia lo cubre.

### 10. Épicas 10 y 11 — SHOULD y COULD

- **AC10.2.2 (reescrito)** Con un transcriptor *fake* que tarda 12 s, el `POST` del audio responde `202` y la
  interfaz acepta otro envío antes de que termine. `[N1]` + `[N0]` Vitest.
- **AC10.3.1 (partido)** `[N0]`: el constructor del *prompt* de la pregunta recibe solo pasajes del marco de
  verdad recuperados. La calidad de la pregunta no tiene meta numérica (`requirements.md`), así que no hay AC `[N2]`.
- **AC10.3.2** `[N0]` en el módulo guardia, y vale aunque FR10.3 no se construya (AUTONOMIA-05 «ni pregunta»).
- **AC10.4.1** «Sin pulsarlo no se genera audio» → el *fake* de TTS registra 0 llamadas. `[N0]`
- **AC10.5.1 (partido)** `[N0]`: con un juez *fake* que discrepa solo en un orden, no se registra alerta; la
  permutación nunca produce alerta por debajo del umbral. `[N2]`: consistencia > 65 % (NFR4).
- **AC10.6.1 (pregunta al lead)** «Más del 25 % de alertas consecutivas descartadas o ignoradas» necesita
  ventana (¿cuántas alertas?) y una definición de «ignorada». Con eso: `promtool test rules` con 25 % exacto
  (no alerta) y 25 % + 1 alerta (alerta). `[N0]`
- **AC10.7.1** Política estática: la `Application` de Argo CD no tiene *prune* sobre CloudNativePG y sus PVC.
  `[N0]` La sincronización real es `[Manual]`.
- **AC11.3.1 (ampliado)** Si el anonimizador falla, no se hace la llamada externa (falla cerrado). `[N0]`, con
  100 % de ramas.

### 11. Matriz de cobertura AUTONOMIA (para la sección de trazabilidad de `stories.md`)

| Regla | Prueba del mapa de team-practices | AC que la cubre | Hueco que esta contribución cierra |
|---|---|---|---|
| 01 | Ningún *workflow* ni *script* aplica cambios `[N0]` | — | AC9.5.1 |
| 03 | Máquina de estados con actor y hora | AC5.1.2, AC5.2.1, AC5.3.2 | AC5.1.4, AC8.1.5 (solo inserciones) |
| 03 | Consolidación explícita con SHA-256 | AC6.1.1–AC6.1.4, AC6.3.3 | AC6.1.5, AC6.1.6, AC6.1.7 |
| 03 | Esquema sin campos de veracidad | AC5.5.2 | `additionalProperties: false` |
| 03 | Escaneo de vocabulario `[N0][N1][N3]` | AC5.5.1 (sin nivel) | niveles, lista versionada y control negativo |
| 04 | *Payload* del anonimizador `[N0]` | AC11.3.1 (COULD) | AC8.1.6 y AC9.1.4 como MUST |
| 04 | `NetworkPolicy` estática `[N0]` + manual | AC9.1.1, AC9.1.2 | control negativo y control positivo |
| 05 | Alerta rechazada sin cada campo | AC3.1.2 | vacío o solo espacios; ID fuera de la versión |
| 05 | Umbral leído de configuración | AC4.2.x, AC2.1.2 | AC2.1.2 ejecutable; extremos del rango |
| 05 | Prueba por debajo del umbral `[N0][N1][N2]` | AC4.1.1, AC4.1.5 | AC4.1.6 (juez forzado a «incongruente») |

### 12. Celdas «No» y «Solo propias» de FR1.2 (cada una exige su prueba `403`)

| Celda | AC |
|---|---|
| `analista` gestiona usuarios | AC8.2.2 |
| `admin` crea sesión / ingresa testimonio / finaliza | AC2.1.3 + AC2.1.4 (nuevo) |
| `admin` cambia estado de alertas | AC5.4.3 |
| `admin` consolida | AC6.1.7 (nuevo) |
| `admin` corrige reporte | AC6.3.4 |
| `analista` cambia alertas de otra sesión | AC5.4.1 |
| `analista` consolida o corrige otra sesión | AC6.1.4, AC6.3.4 |
| `analista` aplica cambio de umbral | AC8.3.3 (no existe la ruta) |

## Positions

- AGREE: Formato Given/When/Then con IDs `ACx.y.z` y trazabilidad a FR — cada criterio se puede convertir en una prueba con nombre.
- AGREE: Decisión por afirmación de P4 en AC4.1.1–AC4.1.4 — es una regla determinista que se prueba en `[N0]` con bordes exactos.
- AGREE: Dejar diferidos los NFR de calidad de IA, MTTV, cobertura y latencia (P3) — sus umbrales viven en NFR Requirements y en el nivel 2, no en las historias.
- OBJECT: AC sin etiqueta de nivel que dependen del LLM real (AC2.3.2, AC3.1.4, AC3.3.1, AC10.3.1, AC10.5.1) — en los niveles 0 y 1 el LLM es *fake* y esos AC se deben partir en una variante determinista y otra `[N2]`.
- OBJECT: Cobertura incompleta de AUTONOMIA-05 — falta la prueba con el juez forzado a «incongruente» por debajo del umbral (AC4.1.6), sin la cual AC4.1.1 puede pasar en vacío.
- OBJECT: Cobertura incompleta de AUTONOMIA-03 — falta solo inserción en historiales (NFR11), la consolidación concurrente y el rechazo a consolidar por `admin` o por una identidad de servicio.
- OBJECT: AUTONOMIA-04 depende solo de una historia COULD (US11.3) — sin anonimizador hacen falta como MUST la prueba del *canary* en logs (AC8.1.6) y el rechazo de URL externas (AC9.1.4).
- OBJECT: AUTONOMIA-01 sin AC — el mapa exige la comprobación estática de que ningún *workflow* ni *script* aplica cambios al clúster (AC9.5.1).
- OBJECT: La matriz 403 de FR1.2 está incompleta — falta `admin` al ingresar testimonio, al finalizar y al consolidar.
- OBJECT: Criterios vagos según AUTONOMIA-02 — AC2.2.2 y AC10.2.2 («responde sin esperar»), AC1.2.2 («no existe o responde con error»), AC5.3.1 y AC6.3.1 («no lo permite»), AC9.3.2 y AC9.1.3 («los reviso») no nombran estado HTTP, comando o umbral.
- OBJECT: Borde de 1 MB sin definir en bytes y *fixture* Latin-1 ambiguo (AC1.1.1, AC1.1.2) — un Latin-1 solo ASCII es UTF-8 válido y la prueba pasaría sin probar nada.
- OBJECT: Se puede consolidar con turnos aún en proceso (entre AC2.4.2 y FR7.5) — sin AC6.1.5 puede llegar una alerta a una sesión bloqueada.
- OBJECT: Casos sin regla que impiden el 100 % de ramas en el módulo guardia — «no documentada» en o sobre el umbral (AC4.1.8), ventana y «ignorada» del AIR (AC10.6.1), escaneo de la reformulación del analista y turnos en `error` en el reporte; los dejo como preguntas para el lead, sin reabrir P4–P8.
