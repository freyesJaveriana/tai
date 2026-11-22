# Preguntas de Functional Design — U12 research-reports

- **Unidad:** U12 `research-reports` (tipo `service`), directorio `u12-research-reports`. Prioridad MUST, con
  US12.7 SHOULD. Tamaño M. Bolt B12, después de la demo (P11 = A de Delivery Planning).
- **Componentes:** ResearchReports (dueño de la entidad `ResearchReport`), las rutas `/research-reports*`
  de ConsoleApi y la pantalla M8 de AnalystConsole.
- **Historias:** US12.6 (AC12.6.1–AC12.6.4) → US12.7 (AC12.7.1–AC12.7.3).
- **Depende de:** U1 contracts (C19 y el registro de esquemas), U3 identity-access (rol `investigador`,
  token y llegada a M8) y U4 text-flow (base de la consola y suite `axe`).
- **Situación:** unidad nueva del cambio 01, sin diseño previo. Primera pasada.

Contesta debajo de cada `[Answer]:` con la letra o con tu texto. Son 3 preguntas. Todo lo demás lo
resuelve el diseño con la propuesta de la sección 2, y puedes corregirlo en la aprobación.

---

## 1. Lo que ya está decidido y no se vuelve a preguntar

| Tema | Decisión | Fuente |
|---|---|---|
| Qué es la pantalla | Es de solo consulta para el rol `investigador`. Sube, lista, muestra en detalle y compara de dos en dos los reportes JSON de la CLI (máquina local o ZINE). No lanza análisis | FR13.5; mockups M8 (seg. 7); unit-of-work U12 |
| Qué se guarda | Solo metadatos y cifras: perfil, `config_sha256`, `prompt_sha256`, versiones del analizador y del conjunto, registro de modelos, *tokens*, costo, métricas y tabla de sesgo. Nunca texto de transcripciones, hallazgos ni citas | FR13.5; NFR12; ADR-014; `project.md` (M8) |
| Reporte con texto o fuera del esquema | Se rechaza con `422` `research.invalid_report` y no se guarda nada. Un reporte de la CLI no tiene campos de texto libre | CD-03; ADR-014; C19 (P12); BR10.1 de U1 |
| AC12.6.1 (*canary*) | Se cierra aquí, con la propuesta de FD-U1-05: el *canary* da `422`, 0 filas y 0 apariciones en los logs. Eso sustituye al `201` con «se descartó». El mensaje `research.upload_ok` deja de decir «se descartó» (DP-01). Ambos ajustes van a la tabla de precisiones de esta etapa | FD-U1-05; DP-01; CD-03 |
| Duplicados | Se detectan por el SHA-256 del archivo subido (`source_sha256`). La segunda subida da `409` `research.duplicate` («Este reporte ya está subido») y no crea filas | AC12.6.2; C1 |
| Roles | Solo el `investigador` usa `/research-reports*`. El `analista` y el `admin` reciben `403` y no ven «Reportes». El `investigador` recibe `403` en sesiones y en reportes de sesión, y llega a M8 al iniciar sesión (lo fija U3) | FR1.2; AC12.6.3; AC8.1.1; AC8.2.4; U3 BR1.7 y BR4.6 |
| Rutas | `GET` y `POST /research-reports`, `GET /research-reports/{id}` y `GET /research-reports/compare?a&b` (SHOULD). La subida es `multipart/form-data` con token CSRF. Hay `413` por tamaño y `409` `research.not_comparable` para tipos distintos | C1 (OpenAPI); contract-summary |
| Esquema del reporte | Es el de U1: `contracts/cli/report.schema.v1.yaml` y `model_calls/model-call.v1.yaml`, cerrado, con cadenas acotadas por `enum` o por `pattern` sin espacios. Si se aprueba, C19 v2 (FD-U11-09) añade `dataset_sha256`, valores por corrida, umbrales y `passes`, y la validez de la medición | C19; FD-U1-03; FD-U11-09 |
| Tope de tamaño | Es `research_report_max_bytes` en `contracts/limits.v1.yaml`. La cifra la fija NFR Requirements | C25; `project.md` (catálogo único de límites) |
| Métrica ausente | Se muestra «No informado», nunca 0. Lo mismo vale para un grupo de la tabla de sesgo que el reporte no trae | AC12.6.4; mockups M8 §10.2 (rev. 3) |
| Comparación | El botón se habilita con exactamente 2 reportes marcados. Con conjuntos distintos solo se comparan metadatos y aparece «Conjuntos distintos: las métricas no son comparables». Cada fila lleva «=» o «≠» en texto, y las diferencias numéricas llevan su signo | AC12.7.1–AC12.7.3 |
| Retención | Los datos no tienen testimonio, así que el Job de retención de U13 no los toca | ADR-014; components (ResearchReports) |
| Sin configuración | M8 no tiene ningún control de configuración | US8.3 |
| Accesibilidad | M8 entra en la suite `axe` de U4. Se anuncia el resultado de validar el archivo | US5.6; mockups (regla de anuncios); B12 punto 4 |

## 2. Lo que el diseño resolverá sin preguntar

Las precisiones a artefactos aprobados van a la tabla de precisiones de `functional-spec.md`. No se edita
ningún original.

1. **Validación en un solo paso, sin eco.** El orden es: tope de bytes, UTF-8, JSON estricto (sin claves
   duplicadas, sin `NaN` ni `Infinity`, con profundidad acotada), esquema C19 con el registro de U1 y reglas
   propias. Lo primero que falla da `422` y no se escribe nada. El `detail` del Problem Details y los logs
   **nunca repiten valores del archivo**. Tampoco repiten nombres de campos desconocidos, porque un nombre
   de propiedad también puede ser el *canary*. El `detail` solo nombra la regla y la ruta, con índices y
   nombres de campo del esquema; un campo que el esquema no conoce aparece como «campo no permitido». Se
   añaden el número total de problemas, como en M7, y el SHA-256 del archivo. Así se cumple la parte «0
   apariciones en los logs» de AC12.6.1.
2. **Una sola versión aceptada.** Se acepta la versión de C19 que el paquete `veridicus_contracts` publique
   como vigente: v2 si se aprueba FD-U11-09, y si no, v1. Cualquier otra `schema_version` da `422`. La CLI
   aún no existe, así que no hay reportes antiguos que migrar.
3. **Campos de llamada obligatorios para modelos locales.** En las llamadas con `provider: local`, la
   consola exige `version`, `effort_or_quantization` y `engine`. Si falta uno, responde `422` con «Falta el
   campo <campo>» (`research.missing_field`, M8 §10.1, AC14.3.1). En las llamadas comerciales esos campos
   siguen siendo opcionales, como en C19. Si la cuantización no es `Q8_0` ni `BF16`, el detalle muestra
   «no válida para medir capacidades». Se usa la marca de validez de C19 v2 si viene; si no, se calcula
   con la regla de BR12.7 de U11.
4. **Cumple o no cumple.** Las métricas con umbral muestran el `passes` y el umbral **que trae el
   reporte**, es decir, el que se aplicó cuando se corrió. No se recalculan contra el `thresholds` actual.
   Un reporte sin esos datos muestra solo la cifra.
5. **Visibilidad.** Todo `investigador` ve todos los reportes subidos, con «subido por» y la fecha. FR1.2
   da el permiso por rol, sin dueño, y el objetivo es tener las cifras «en un solo lugar».
6. **Sin borrado ni edición.** El contrato no tiene esas rutas. Un reporte subido por error se queda; no
   tiene testimonio. Si hiciera falta borrar, sería una ruta nueva por PR de U1.
7. **Registro de quién y cuándo.** La subida aceptada guarda `uploaded_by` y `uploaded_at` (FR1.3). Un
   rechazo queda en el log con el ID del usuario, el `code` y el SHA-256 del archivo, nunca con su
   contenido. M8 no abre sesiones ni reportes de revisión, así que no escribe en el registro de acceso de
   EthicsGovernance.
8. **Comparación de tipos distintos.** Una corrida frente a una evaluación da `409`
   `research.not_comparable`, como dice C1, que se aprobó después de las maquetas. La consola muestra
   «Reportes de tipo distinto: no se pueden comparar». En el diseño, el botón sigue habilitado con dos
   marcados (AC12.7.1) y el aviso sale al comparar. La diferencia con M8 §10.3 va a la tabla de
   precisiones.
9. **Qué se compara.** En dos evaluaciones, las métricas se comparan solo si el conjunto coincide: por
   `dataset_sha256` si viene en C19 v2, y si no, por `dataset_version`. En dos corridas se comparan las
   cifras agregadas (pregunta 2) cuando el conjunto de entradas coincide; si no coincide, solo se comparan
   los metadatos. El costo con «sin precio» en uno de los lados da «—», nunca una resta.
10. **Huella y presentación.** La huella es `config_sha256` acortado a 12 caracteres, con «Copiar». Las
    fechas van en hora de Colombia con el formato de U1. Los totales del registro de modelos se agrupan
    por papel y proveedor. La tabla de sesgo se muestra solo como conteos por `fact_type` y
    `synthetic_set` (FD-U11-07: `<tipo_hecho>__<perfil_persona>`). Los datos del perfil que C19 no trae
    (modo, ventanas) se omiten y no se inventan.
11. **Mensajes.** El catálogo `research.*` de `interaction-spec.md` se completa con `research.invalid_report`
    y `research.not_comparable_kind`. La nueva redacción de `research.upload_ok` es «Reporte subido. Solo
    contiene metadatos y cifras.» Los dos cambios van como precisiones, en propuesta.
12. **`ResearchReportDetail` de C1.** Lo que se guarde de `runs` (pregunta 2) y del origen (pregunta 3)
    entra como precisión al esquema de C1, en el PR de U1 que ya lleva C19 v2.

---

## 3. Preguntas

### P1. *Canary* de una sola palabra en un campo con patrón

**Contexto.** FD-U1-05 (hallazgo R-06) deja abierto un caso. Una palabra sin espacios, como `CANARIO-7f3a`
puesta en `model`, `version`, `engine`, `price_table_version` o `synthetic_set`, cumple el `pattern` y pasa
el esquema. Si llega así, se guarda en una columna. El *canary* de AC12.6.1 va «en un hallazgo», es decir,
en un campo que C19 no admite, y eso ya da `422`. La pregunta es qué hacer con una palabra suelta en un
campo permitido. Sería, por ejemplo, un nombre real escrito a mano en el reporte. Hoy ResearchReports solo
depende de IntegrityPolicy. La opción A usaría el catálogo de perfiles aprobados, que ConsoleApi ya lee
para M3 y le pasaría a ResearchReports, así que no aparece una arista nueva entre unidades.

- A. **(Recomendada)** Contrastar las cadenas con lo versionado. `profile_name` debe ser un perfil del
  archivo aprobado por PR. En cada llamada, `provider`, `model`, `version`, `engine` y
  `effort_or_quantization` deben coincidir con lo que ese perfil declara para el papel o para su alterno.
  `price_table_version` debe existir en la tabla de precios, y `synthetic_set` debe estar en las listas
  de BR13.3 de U11. Si algo no coincide, la respuesta es `422` con «valor no reconocido en <campo>» y no se
  guarda nada. Costo: no se puede subir un reporte de un perfil que todavía no entró por PR, incluido uno
  de ZINE.
- B. Aceptar el riesgo residual y declararlo. Solo se valida el esquema. Un escenario visible documenta que
  una palabra suelta en `model` se guarda, con su prueba, y se apoya en que la base vive en el clúster
  local y no en el repositorio. Costo: NFR12 queda cubierto para frases, no para palabras sueltas.
- C. Contrastar solo `profile_name`, `provider` y `model` con el catálogo de perfiles. `version`, `engine`,
  la cuantización y las etiquetas quedan como riesgo residual declarado. Es un término medio que deja
  abiertos 5 campos.
- D. No guardar ninguna cadena con patrón, solo los `enum`, los números y los hashes. Costo: se pierden
  el modelo, la versión y el motor del registro, que FR13.5 y M8 §10.2 piden mostrar.
- X. Other (please specify)

[Answer]: A **Mode:** guided

### P2. Qué se guarda de las corridas por entrevista (`runs[]`)

**Contexto.** C19 trae por entrevista `interview_sha256`, `status`, `error_code`, el número de hallazgos,
los descartes por motivo y las llamadas. La entidad `ResearchReport` (components) y `ResearchReportDetail`
(C1) no nombran `runs`; guardan llamadas, totales, métricas y tabla de sesgo. Pero M8 §10.2 pide que una
corrida muestre «su estado, su código si falló, … el número de hallazgos y de citas rechazadas». Además, el
`interview_sha256` de una entrevista real del piloto es un identificador estable de esa entrevista. No se
puede revertir, pero permite enlazar reportes entre sí.

- A. **(Recomendada)** Guardar solo agregados, sin hashes individuales. Se guarda el número de corridas, el
  conteo por `status` y por `error_code`, el total de hallazgos, los descartes por motivo y una sola **huella
  del conjunto de entradas**: el SHA-256 de los `interview_sha256` ordenados. Con esa huella se sabe si dos
  corridas usaron las mismas entrevistas, sin guardar cuáles fueron. Entra como precisión a C1 y a la
  entidad.
- B. Guardar una fila por entrevista, con `interview_sha256`, estado, código, hallazgos y descartes. Así se
  puede comparar entrevista por entrevista, a cambio de guardar un identificador estable por entrevista
  real.
- C. Guardar solo lo que hoy declaran C1 y la entidad (llamadas, totales, métricas, tabla de sesgo) y
  descartar `runs`. M8 §10.2 pierde el estado, el código y los conteos de una corrida, y eso iría como
  precisión a M8.
- D. Igual que A, pero sin la huella del conjunto de entradas. Dos corridas solo serían comparables en
  metadatos y totales.
- X. Other (please specify)

[Answer]: A **Mode:** guided

### P3. De dónde sale el «Origen» (CLI local o ZINE)

**Contexto.** M8 §10.1 tiene la columna y el filtro «Origen» (CLI local / ZINE), y §10.2 y §10.3 lo usan en
el título. C19 no tiene ese campo. C19 v2 todavía está abierto como cambio mayor por PR de U1 antes del
código de B11 (FD-U11-09), así que añadir un campo ahora cuesta poco. Más tarde costaría otra versión
mayor.

- A. **(Recomendada)** Lo escribe la CLI en C19 v2, con un campo `origin` de valores `local` y `zine`. Es
  `zine` cuando corre bajo SLURM (variable `SLURM_JOB_ID`) o en `evaluate --puntuar` sobre salidas de ZINE,
  y `local` en los demás casos. Es determinista y no depende de la persona. Va como precisión a FD-U11-09
  y a C19, para decidir en la aprobación de U11 y de esta unidad.
- B. Lo declara el investigador al subir el archivo, con un selector obligatorio (`local` / `zine`) que se
  guarda como `enum`. No toca U1 ni U11, pero depende de que la persona lo elija bien.
- C. Se quita «Origen» de M8 (columna, filtro y títulos) como precisión a la maqueta. El origen se
  infiere a ojo por el perfil.
- D. Se deduce del registro de llamadas (por ejemplo, todas con `provider: local` y una cuantización
  declarada se toman como ZINE). No toca contratos, pero una corrida local con modelo local quedaría mal
  clasificada.
- X. Other (please specify)

[Answer]: A **Mode:** guided
