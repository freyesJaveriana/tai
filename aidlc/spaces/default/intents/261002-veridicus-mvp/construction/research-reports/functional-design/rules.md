# Reglas de negocio — U12 research-reports

**Revisión 1 (2026-11-22), primera pasada.** Unidad nueva del cambio 01 (DT27); no hay reglas previas.
Respuestas P1 = A (contraste con lo versionado), P2 = A (solo agregados de `runs[]`) y P3 = A (`origin` en
C19 v2), y los doce puntos de la sección 2 de `functional-design-questions.md`.

**Insumos.** Los mismos de `entities.md`:
- `inception/units-generation/unit-of-work.md` (unit-of-work) y `unit-of-work-story-map.md`
  (unit-of-work-story-map);
- `inception/requirements-analysis/requirements.md` (requirements);
- `inception/domain-design/components.md` (components);
- `inception/contract-design/contract-summary.md` (contract-summary);
- M8 de `inception/refined-mockups/mockups.md` y los diseños de U1, U3, U4 y U11.

Los niveles de prueba (N0, N1, N3) siguen `team.md` (Testing Posture). Los `code` y las claves de
mensaje que aún no están en C1 ni en `interaction-spec.md` se proponen en la tabla de precisiones de
`functional-spec.md` (§10). Las pruebas de BR2.1, BR3.1–BR3.5, BR4.1 y BR4.2 protegen NFR12 y se
escriben primero y en rojo, como las de los contratos de datos (Testing Posture, Ordering).

## Reglas (fuente de verdad)

```yaml
rules:
  # BR1 — Acceso a las rutas de reportes
  - id: BR1.1
    statement: Solo el rol investigador usa las rutas /research-reports*; los demás reciben 403 sin filas nuevas.
    category: authorization
    applies_to: [ResearchReport]
    trigger: Cada petición a GET o POST /research-reports, GET /research-reports/{id} y GET /research-reports/compare
    logic: SI el principal es analista o admin ENTONCES 403 con code auth.forbidden, Problem Details en español y 0 filas nuevas; SI es investigador ENTONCES ConsoleApi delega en ResearchReports. La matriz la aplica ConsoleApi con x-veridicus-roles de C1, como en el resto de la consola.
    violation: Una prueba de nivel 1 por ruta y por rol rechazado (2 roles × 4 rutas).
    source: FR1.2; FR13.5; AC12.6.3
  - id: BR1.2
    statement: Solo el investigador ve la entrada «Reportes» de la navegación y la pantalla M8; el analista y el admin no la ven.
    category: authorization
    applies_to: [ResearchReport]
    trigger: Al dibujar la cabecera y la navegación de la consola
    logic: SI el rol de /me es investigador ENTONCES la navegación muestra solo «Reportes» (M8, su inicio según la regla de destino de U3); SI es analista o admin ENTONCES no aparece «Reportes» y una ruta escrita a mano hacia M8 lleva a su propio inicio sin pedir datos a la API.
    violation: Prueba Vitest de la navegación con los tres roles.
    source: FR1.2; AC12.6.3; mockups M8 (seg. 8)
  - id: BR1.3
    statement: La subida exige el token CSRF de la sesión web.
    category: authorization
    applies_to: [ResearchReport]
    trigger: POST /research-reports
    logic: SI falta el token o no coincide ENTONCES 403 con code auth.csrf, sin leer el archivo y sin filas nuevas.
    violation: Prueba de nivel 1 sin token y con un token de otra sesión.
    source: C1 (parámetro CsrfToken); NFR10
  - id: BR1.4
    statement: Un reporte guardado no se edita ni se borra desde la aplicación; la tabla es history y no purgable.
    category: constraint
    applies_to: [ResearchReport]
    trigger: Migración de la tabla y enumeración del OpenAPI
    logic: SI el OpenAPI declara PUT, PATCH o DELETE bajo /research-reports ENTONCES falla la prueba de nivel 0; la tabla lleva la marca veridicus-audit con kind history, purgeable false y owner_unit U12, así que veridicus_app solo tiene SELECT e INSERT y veridicus_retention no la borra.
    violation: Prueba de nivel 0 sobre el OpenAPI y prueba común de auditoría de U3 (nivel 1) sobre la tabla.
    source: Punto 6 de la sección 2; ADR-014; convención de auditoría de U3 (ADR-003)

  # BR2 — Validación de la subida
  - id: BR2.1
    statement: La subida se valida entera antes de escribir; el primer paso que falla corta la validación y no se escribe nada.
    category: validation
    applies_to: [ResearchReport, UploadOutcome]
    trigger: POST /research-reports
    logic: "Orden fijo: (1) tope de bytes (BR2.2); (2) SHA-256 del archivo y duplicado (BR2.8); (3) UTF-8 y JSON estricto (BR2.3); (4) esquema C19 vigente (BR2.4); (5) coherencia por tipo (BR2.5) y campos de llamadas locales (BR2.6); (6) contraste con lo versionado (BR3.1–BR3.5); (7) validez de la medición (BR2.7). SI un paso falla ENTONCES responde con su código y no se escribe ninguna fila; SI todos pasan ENTONCES la fila y sus listas se escriben en una sola transacción y responde 201 con ResearchReportDetail. Dentro de los pasos 4 a 7 se recogen todos los problemas para dar el total, y se informa el primero en el orden del archivo."
    violation: Prueba de nivel 1 con un fixture inválido por paso que cuenta 0 filas nuevas, y prueba con un fallo simulado de la base a mitad de la escritura que deja 0 filas.
    source: FR13.5; CD-03; punto 1 de la sección 2; AC12.6.1
  - id: BR2.2
    statement: Un archivo que supera research_report_max_bytes se rechaza con 413 sin leerse entero.
    category: validation
    applies_to: [UploadOutcome]
    trigger: POST /research-reports
    logic: SI el cuerpo supera research_report_max_bytes de contracts/limits.v1.yaml (una variable de entorno solo puede bajarlo) ENTONCES 413 con code limits.exceeded, la lectura se corta al pasar el tope y no se calcula el SHA-256. La cifra la fija NFR Requirements.
    violation: Prueba de nivel 1 con un archivo de tope + 1 bytes.
    source: C25; C1 (413); regla de project.md sobre el catálogo único de límites
  - id: BR2.3
    statement: El archivo es UTF-8 válido y JSON estricto.
    category: validation
    applies_to: [UploadOutcome, ValidationProblem]
    trigger: Paso 3 de BR2.1
    logic: SI el archivo no es UTF-8 válido o empieza con BOM (rule encoding), no es JSON (json_syntax, con línea y columna), repite una clave en un mismo objeto (json_duplicate_key), trae NaN, Infinity o -Infinity (json_non_finite) o pasa de la profundidad máxima de anidamiento (json_depth) ENTONCES 422 con code research.invalid_report. La profundidad máxima la fija NFR Requirements en el catálogo de límites (FD-U12-12).
    violation: Prueba de nivel 0 con un fixture por caso.
    source: Punto 1 de la sección 2; AC12.6.1
  - id: BR2.4
    statement: El reporte cumple exactamente la versión vigente de C19 con el registro de esquemas de U1.
    category: validation
    applies_to: [ResearchReport, ValidationProblem]
    trigger: Paso 4 de BR2.1
    logic: SI schema_version no es la versión de C19 que veridicus_contracts publica como vigente (v2 si se aprueba FD-U11-09; si no, v1) ENTONCES problema schema_version; SI el reporte no valida contra ese esquema y model-call.v1.yaml (campo desconocido → not_allowed_field, campo obligatorio ausente → missing_field, tipo, rango o patrón) ENTONCES 422 con code research.invalid_report. Un hallazgo, una cita o cualquier texto dentro del reporte cae aquí, porque C19 no tiene esos campos.
    violation: Prueba de nivel 1 de AC12.6.1 (canary «CANARIO-7f3a» dentro de un hallazgo) y fixtures de nivel 0 report.testimony-in-model.json, report.testimony-in-price-table.json y uno con schema_version de otra versión.
    source: C19; P12 de Contract Design; CD-03; regla de U1 del reporte sin texto libre; punto 2 de la sección 2; AC12.6.1
  - id: BR2.5
    statement: El contenido es coherente con su tipo y consigo mismo.
    category: validation
    applies_to: [ResearchReport, RunSummary, MetricValue]
    trigger: Paso 5 de BR2.1
    logic: SI kind es evaluation y falta dataset_version ENTONCES missing_field; SI kind es run y trae metrics, bias_table, dataset_version o dataset_sha256 ENTONCES kind_mismatch; SI un run con status ok trae error_code, o uno con status error no lo trae ENTONCES inconsistent_counts; SI en C19 v2 una métrica trae threshold sin passes o al revés ENTONCES inconsistent_counts. En todos los casos 422 con code research.invalid_report.
    violation: Prueba de nivel 0 con un fixture por caso.
    source: C19 (descripciones «Solo evaluation»); punto 4 de la sección 2
  - id: BR2.6
    statement: Toda llamada con provider local declara version, effort_or_quantization y engine.
    category: validation
    applies_to: [ModelCallRecord, ValidationProblem]
    trigger: Paso 5 de BR2.1
    logic: SI una llamada tiene provider local y le falta version, effort_or_quantization o engine ENTONCES 422 con code research.invalid_report, problema missing_field con la ruta del campo, y M8 muestra «Falta el campo <campo>» (clave research.missing_field). En las llamadas comerciales esos campos siguen siendo opcionales, como en C19.
    violation: Prueba de nivel 0 con tres fixtures, uno sin cada campo, y uno comercial sin los tres que pasa.
    source: Punto 3 de la sección 2; mockups M8 §10.1; criterio de rechazo de US14.3 llevado a la consola
  - id: BR2.7
    statement: Un reporte con una llamada local cuya cuantización no es Q8_0 ni BF16 se guarda marcado como no válido para medir capacidades.
    category: calculation
    applies_to: [ResearchReport]
    trigger: Paso 7 de BR2.1
    logic: measurement_valid = falso SI alguna llamada con provider local tiene effort_or_quantization distinto de Q8_0 y de BF16; verdadero en otro caso. SI el reporte trae la marca de validez de C19 v2 y no coincide con este cálculo ENTONCES 422 con code research.invalid_report y problema inconsistent_validity. La marca nunca impide guardar.
    violation: Prueba de nivel 0 con Q4_K_M (se guarda con measurement_valid falso), con Q8_0 (verdadero) y con una marca v2 que contradice las llamadas (422).
    source: Punto 3 de la sección 2; regla de cuantización del modo de puntuación de U11
  - id: BR2.8
    statement: Un archivo ya subido (mismo SHA-256) no se guarda dos veces.
    category: constraint
    applies_to: [ResearchReport]
    trigger: Paso 2 de BR2.1 y al escribir la fila
    logic: SI ya existe un ResearchReport con el mismo source_sha256 ENTONCES 409 con code research.duplicate, M8 muestra «Este reporte ya está subido» y 0 filas nuevas. Dos subidas simultáneas del mismo archivo las resuelve la unicidad de source_sha256 en la base; la que pierde también responde 409.
    violation: Prueba de nivel 1 de AC12.6.2 (dos subidas seguidas) y prueba de nivel 1 con dos subidas concurrentes que deja exactamente 1 fila.
    source: AC12.6.2; C1 (409)

  # BR3 — Contraste con lo versionado (P1 = A)
  - id: BR3.1
    statement: profile_name es un perfil del archivo de perfiles aprobado por PR.
    category: validation
    applies_to: [ResearchReport, ReferenceCatalog]
    trigger: Paso 6 de BR2.1
    logic: SI profile_name no es una clave de ReferenceCatalog.profiles ENTONCES 422 con code research.invalid_report y problema value_not_recognized en profile_name («valor no reconocido en profile_name»).
    violation: Prueba de nivel 1 con el canary «CANARIO-7f3a» como profile_name, que da 422, 0 filas y 0 apariciones en los logs.
    source: Respuesta P1 = A; NFR12; AC12.6.1
  - id: BR3.2
    statement: Cada llamada coincide con lo que el perfil declara para su papel o para su alterno.
    category: validation
    applies_to: [ModelCallRecord, ReferenceCatalog]
    trigger: Paso 6 de BR2.1
    logic: "El destino es fallback_provider del perfil SI la llamada tiene fallback_provider verdadero; si no, judge para el papel judge, y verifier para verifier y verifier_permuted. SI el perfil no tiene ese destino, o provider o model no son iguales a los del destino ENTONCES value_not_recognized. Para version, effort_or_quantization y engine: SI el destino declara el valor (version; parameters.effort o parameters.quantization; parameters.engine) ENTONCES el de la llamada, si viene, es igual; SI el destino no lo declara ENTONCES la llamada no lo trae, salvo version en un proveedor comercial (BR3.3). Todo desajuste da 422 con code research.invalid_report y la ruta del campo."
    violation: Prueba de nivel 1 con el canary en model, en version y en engine de una llamada (422, 0 filas, 0 apariciones en logs), y prueba de nivel 0 con un reporte real de la CLI sobre el perfil comercial-piloto y otro sobre un perfil local, que pasan.
    source: Respuesta P1 = A; C18 (destinos y parameters); NFR12; AC12.6.1
  - id: BR3.3
    statement: En una llamada comercial cuyo perfil no declara version, la versión es el modelo o el modelo seguido de segmentos que empiezan por dígito.
    category: validation
    applies_to: [ModelCallRecord]
    trigger: Paso 6 de BR2.1
    logic: SI provider no es local, el destino no declara version y la llamada trae version ENTONCES version es igual a model, o es model seguido de uno o más segmentos que empiezan por un separador (-, @ o .) y un dígito y siguen con letras, dígitos o puntos (p. ej. gpt-x-2025-08-06, modelo@20250514); SI no ENTONCES value_not_recognized. Así cabe la versión que informa el proveedor (U10) y no cabe un nombre propio.
    violation: Prueba de nivel 0 con model-2025-08-06 (pasa), model@20250514 (pasa), model-CANARIO (422) y una version sin relación con model (422).
    source: Respuesta P1 = A; regla de U10 que llena version con lo que informa el proveedor; precisión FD-U12-11
  - id: BR3.4
    statement: price_table_version, si viene, es la versión de la tabla de precios vigente.
    category: validation
    applies_to: [ResearchReport, ReferenceCatalog]
    trigger: Paso 6 de BR2.1
    logic: SI totals.price_table_version viene y no es igual a ReferenceCatalog.price_table_version ENTONCES 422 con code research.invalid_report y value_not_recognized en totals.price_table_version.
    violation: Prueba de nivel 1 con el canary como price_table_version (422, 0 filas, 0 apariciones en logs).
    source: Respuesta P1 = A; C18 (tabla de precios); AC12.6.1
  - id: BR3.5
    statement: Cada synthetic_set de la tabla de sesgo es <tipo_hecho>__<perfil_persona> con las dos etiquetas en sus listas versionadas.
    category: validation
    applies_to: [BiasCount, ReferenceCatalog]
    trigger: Paso 6 de BR2.1
    logic: SI synthetic_set no tiene exactamente un separador doble guion bajo, o su primera parte no está en story_fact_types, o la segunda no está en persona_profiles ENTONCES 422 con code research.invalid_report y value_not_recognized en bias_table[i].synthetic_set; SI pasa ENTONCES se guarda partido en story_fact_type y persona_profile.
    violation: Prueba de nivel 1 con el canary como synthetic_set (422, 0 filas, 0 apariciones en logs) y prueba de nivel 0 con una etiqueta fuera de cada lista.
    source: Respuesta P1 = A; FD-U11-07; listas cerradas de etiquetas del conjunto sintético de U11; AC12.6.1
  - id: BR3.6
    statement: ConsoleApi carga el catálogo de referencia al arrancar; sin él, session-api no arranca.
    category: policy
    applies_to: [ReferenceCatalog]
    trigger: Arranque de session-api
    logic: SI falta config/profiles.yaml, config/prices.yaml o una de las dos listas de etiquetas, o alguno no valida contra su esquema ENTONCES el arranque falla con un log que nombra el archivo (nunca su contenido); SI cargan ENTONCES el log de arranque lleva catalog_sha256. El catálogo es de solo lectura; cambia solo por PR y con un nuevo despliegue.
    violation: Prueba de nivel 0 de arranque sin cada archivo.
    source: Code Style de team.md (configuración faltante impide arrancar); FR9.2; US8.3

  # BR4 — Sin eco del archivo
  - id: BR4.1
    statement: Ni la respuesta ni los logs repiten valores del archivo ni nombres de campos que el esquema no conoce.
    category: policy
    applies_to: [UploadOutcome, ValidationProblem]
    trigger: Todo rechazo de POST /research-reports
    logic: "El detail del Problem Details se arma solo con textos fijos del catálogo, la ruta del primer problema (nombres de campo del esquema e índices; un campo desconocido se nombra como «campo no permitido» en su objeto padre), el total de problemas y el SHA-256 del archivo. Forma: «<ruta>: <texto de la regla>. Hay N problemas más». Nunca entran el valor encontrado, el valor esperado de un patrón, el mensaje del analizador de JSON ni el del validador de esquemas."
    violation: Prueba de nivel 1 de AC12.6.1 que busca «CANARIO-7f3a» en la respuesta, en todas las columnas de texto y en los logs capturados, con el canary como valor de un hallazgo, como nombre de un campo desconocido y en cada campo de BR3.1–BR3.5; y prueba de nivel 0 de que todo detail sale del catálogo.
    source: Punto 1 de la sección 2; NFR12; FR13.5; AC12.6.1
  - id: BR4.2
    statement: El nombre del archivo y el cuerpo de la petición no se guardan ni se registran, y las excepciones no llevan contenido del archivo.
    category: policy
    applies_to: [UploadOutcome]
    trigger: POST /research-reports
    logic: SI el código de la subida guarda o registra el filename del multipart, el cuerpo o una excepción del analizador o del validador con su texto ENTONCES falla la prueba; el manejador único de Problem Details registra solo code, ruta del primer problema y IDs.
    violation: Prueba de nivel 1 que sube el canary como nombre de archivo y como contenido inválido y no lo encuentra en columnas ni en logs.
    source: NFR12; Code Style de team.md (logs solo con IDs); AC12.6.1
  - id: BR4.3
    statement: Cada subida queda en el log con quién, el resultado y el SHA-256 del archivo.
    category: policy
    applies_to: [UploadOutcome]
    trigger: Al responder POST /research-reports
    logic: Se registra una línea con user_id, research_report_id (si se aceptó), code (si se rechazó), regla del primer problema, total de problemas, source_sha256 y bytes. M8 no abre sesiones ni reportes de revisión, así que no llama al registro de acceso de EthicsGovernance.
    violation: Prueba de nivel 1 que comprueba la línea de log de una subida aceptada y de una rechazada.
    source: Punto 7 de la sección 2; FR1.3

  # BR5 — Qué se guarda
  - id: BR5.1
    statement: Solo se guardan los campos de ResearchReport; nada del archivo se guarda en bruto.
    category: constraint
    applies_to: [ResearchReport]
    trigger: Al escribir un reporte aceptado
    logic: Se copian solo los campos de entities.md; el archivo subido no se guarda (ni en la base ni en disco). La respuesta 201 es ResearchReportDetail armado desde la fila guardada.
    violation: Prueba de nivel 1 de AC12.6.1 y prueba de nivel 0 de que la migración no declara columnas de texto libre ni del archivo.
    source: FR13.5; NFR12; ADR-014; AC12.6.1
  - id: BR5.2
    statement: De runs[] solo se guardan agregados y una huella del conjunto de entradas, nunca un interview_sha256 individual.
    category: calculation
    applies_to: [RunSummary]
    trigger: Al escribir un reporte aceptado
    logic: run_count, status_counts, error_code_counts, findings_total y discard_counts salen de sumar runs[]. inputs_fingerprint = SHA-256 de los interview_sha256 ordenados de menor a mayor, sin quitar repetidos, unidos con un salto de línea y codificados en UTF-8.
    violation: Prueba de nivel 0 de la huella (mismo valor con las entradas en otro orden, otro valor con una entrada distinta) y prueba de nivel 1 de que ningún interview_sha256 del archivo aparece en la base.
    source: Respuesta P2 = A; NFR12
  - id: BR5.3
    statement: Todo reporte guardado registra quién lo subió y cuándo, sin nulos.
    category: constraint
    applies_to: [ResearchReport]
    trigger: INSERT en la tabla
    logic: uploaded_by es el user_id del principal y uploaded_at la hora UTC del servidor; actor_kind es user y actor_system es nulo. SI alguno de los dos falta ENTONCES la base rechaza la fila.
    violation: Prueba común de auditoría de U3 (nivel 1) sobre la tabla.
    source: FR1.3; punto 7 de la sección 2; convención de auditoría de U3
  - id: BR5.4
    statement: El origen del reporte lo escribe la CLI en C19 v2; con C19 v1 no hay origen.
    category: calculation
    applies_to: [ResearchReport]
    trigger: Al escribir un reporte aceptado
    logic: SI el reporte trae origin (local o zine) ENTONCES se guarda tal cual; SI no lo trae (C19 v1) ENTONCES origin es nulo y M8 muestra «No informado» en la columna, en el filtro y en el título. La consola nunca lo deduce del perfil ni de las llamadas.
    violation: Prueba de nivel 0 con un reporte v2 de cada origen y Vitest del «No informado».
    source: Respuesta P3 = A; mockups M8 §10.1; precisión FD-U12-07

  # BR6 — Lista y detalle (M8)
  - id: BR6.1
    statement: Lo que el reporte no trae se muestra como «No informado», nunca como 0.
    category: policy
    applies_to: [MetricValue, BiasCount, ResearchReport]
    trigger: Al dibujar el detalle y la lista de M8
    logic: SI una métrica no tiene MetricValue, un grupo de la tabla de sesgo (un valor de una lista de etiquetas o un fact_type) no tiene filas, o origin es nulo ENTONCES se muestra «No informado» (clave metric.not_reported); un 0 solo aparece cuando el reporte trae 0.
    violation: Prueba Vitest de AC12.6.4 con un reporte sin precision, otro con precision 0 y otro sin un grupo de la tabla de sesgo.
    source: AC12.6.4; mockups M8 §10.2 (revisión 3)
  - id: BR6.2
    statement: «Cumple» o «no cumple» se muestra con el umbral que trae el reporte, nunca recalculado.
    category: policy
    applies_to: [MetricValue]
    trigger: Al dibujar las métricas del detalle
    logic: SI la métrica trae threshold y passes ENTONCES se ve la cifra, «cumple» o «no cumple» en texto y el umbral con la palabra «umbral del reporte»; SI no los trae ENTONCES solo la cifra. La consola nunca compara contra evaluation/thresholds.v1.yaml.
    violation: Prueba Vitest con una métrica con passes falso cuyo valor cumple el umbral actual (se ve «no cumple») y otra sin umbral.
    source: Punto 4 de la sección 2; mockups M8 §10.2
  - id: BR6.3
    statement: Un reporte con measurement_valid falso muestra el aviso «no válida para medir capacidades».
    category: policy
    applies_to: [ResearchReport]
    trigger: Al dibujar el detalle y la lista
    logic: "SI measurement_valid es falso ENTONCES el detalle muestra «⚠ Cuantización <valor>: no válida para medir capacidades» con el valor de la llamada local que la causa, y la lista lleva el icono con el texto «no válida»; el aviso es texto e icono, no solo color."
    violation: Prueba Vitest con Q4_K_M.
    source: Punto 3 de la sección 2; mockups M8 §10.2
  - id: BR6.4
    statement: Cifras, huellas y fechas tienen una sola forma de mostrarse.
    category: calculation
    applies_to: [ResearchReport, ModelCallRecord, MetricValue]
    trigger: Al dibujar M8
    logic: "Huella = config_sha256 en sus 12 primeros caracteres con «Copiar» (copia los 64) y anuncio «SHA-256 copiado»; prompt_sha256 igual. Fechas en hora de Colombia con el formato de fecha de U1. verified_quotes, json_format_errors, reversed_order_consistency, permutation_coverage y completed_runs como porcentaje entero; precision, recall, three_run_agreement y type_agreement con 2 decimales y coma decimal; anonymizer_leaks como entero. El registro de modelos se agrupa por papel y proveedor (verifier_permuted aparte), con llamadas y tokens sumados; el costo solo se muestra en la fila Total, con el estimated_cost del reporte y la moneda de la tabla de precios, o «sin precio» si es nulo."
    violation: Prueba Vitest de cada formato y del agrupado, y una de «sin precio».
    source: Punto 10 de la sección 2; mockups M8 §10.2; criterio de costo de US12.5; precisión FD-U12-09
  - id: BR6.5
    statement: Todo investigador ve todos los reportes subidos, con quién los subió y cuándo.
    category: authorization
    applies_to: [ResearchReport]
    trigger: GET /research-reports y GET /research-reports/{id}
    logic: La lista devuelve todos los reportes, ordenados por uploaded_at descendente, con el usuario que lo subió y la fecha; no hay filtro por dueño. Los filtros Tipo, Perfil y Origen se aplican en la consola sobre la lista. Un research_report_id que no existe da 404 con code research.not_found.
    violation: Prueba de nivel 1 con dos investigadores que ven los reportes del otro y prueba del 404.
    source: Punto 5 de la sección 2; FR1.2; FR13.5 («en un solo lugar»); precisiones FD-U12-04 y FD-U12-05
  - id: BR6.6
    statement: La tabla de sesgo se muestra solo como conteos agrupados.
    category: calculation
    applies_to: [BiasCount]
    trigger: Al dibujar el detalle de una evaluación
    logic: "Tres tablas de conteos esperados y encontrados: por tipo de hecho del relato (cada valor de story_fact_types), por perfil de la persona (cada valor de persona_profiles) y por tipo de contradicción (los 7 fact_type). Cada celda suma las filas de BiasCount del grupo; un grupo sin filas es «No informado» (BR6.1)."
    violation: Prueba Vitest con una tabla de sesgo que deja un perfil sin filas.
    source: Punto 10 de la sección 2; FD-U11-07; mockups M8 §10.2 (revisión 3)
  - id: BR6.7
    statement: M8 no tiene controles de configuración ni lanza análisis, y sus textos son fijos.
    category: policy
    applies_to: [ResearchReport]
    trigger: Al dibujar M8 y en la enumeración del OpenAPI
    logic: SI M8 muestra un control que cambie perfiles, proveedores, prompts, precios, límites o umbrales, o un botón que lance un análisis ENTONCES falla la prueba; todos los textos de M8 salen del catálogo de mensajes y entran en el escaneo de vocabulario de la interfaz de U4.
    violation: Prueba Vitest de M8 que enumera sus controles y prueba de nivel 0 del catálogo.
    source: US8.3; FR13.5; FR9.2; AUTONOMIA-03 (escaneo de la interfaz)

  # BR7 — Comparación de dos reportes (SHOULD)
  - id: BR7.1
    statement: «Comparar seleccionados» se habilita con exactamente dos reportes marcados.
    category: validation
    applies_to: [ComparisonView]
    trigger: Al marcar o desmarcar reportes en la lista
    logic: SI hay 0, 1, 3 o más marcados ENTONCES el botón queda con aria-disabled verdadero, enfocable, y su motivo «Marca dos reportes para compararlos» por aria-describedby; SI hay exactamente 2 ENTONCES se habilita, aunque sean de tipos distintos (el aviso sale al comparar, BR7.2).
    violation: Prueba Vitest de AC12.7.1 con 0, 1, 2 y 3 marcados, y del foco con Tab.
    source: AC12.7.1; AC5.6.4; mockups M8 §10.1
  - id: BR7.2
    statement: Solo se comparan dos reportes distintos, existentes y del mismo tipo.
    category: validation
    applies_to: [ComparisonView]
    trigger: GET /research-reports/compare?a&b
    logic: "SI a es igual a b ENTONCES 422 con code validation.invalid_request; SI alguno no existe ENTONCES 404 con code research.not_found; SI kind difiere ENTONCES 409 con code research.not_comparable y M8 muestra «Reportes de tipo distinto: no se pueden comparar» (clave research.not_comparable_kind); SI no ENTONCES 200 con los dos detalles en el orden a, b."
    violation: Prueba de nivel 1 de cada caso.
    source: C1 (409 research.not_comparable); punto 8 de la sección 2; precisiones FD-U12-04 y FD-U12-08
  - id: BR7.3
    statement: Las cifras se comparan solo si los dos reportes usaron el mismo conjunto; si no, solo los metadatos.
    category: calculation
    applies_to: [ComparisonView]
    trigger: Al armar la comparación en la consola
    logic: "En dos evaluaciones, el conjunto coincide SI los dos traen dataset_sha256 y son iguales, o SI alguno no lo trae y dataset_version es igual. En dos corridas, coincide SI inputs_fingerprint es igual. SI coincide ENTONCES se comparan metadatos, métricas, conteos de corridas, tokens y costo; SI no ENTONCES solo las filas de metadatos (tipo, origen, perfil, config_sha256, prompt_sha256, analizador, conjunto, fecha) y el aviso «Conjuntos distintos: las métricas no son comparables» (clave research.not_comparable)."
    violation: Prueba Vitest de AC12.7.2 con dos evaluaciones de distinto dataset_version, con mismo dataset_version y distinto dataset_sha256, y con dos corridas de distinta huella de entradas.
    source: AC12.7.2; punto 9 de la sección 2; respuesta P2 = A
  - id: BR7.4
    statement: Cada fila de la comparación marca «=» o «≠» en texto, y la diferencia numérica lleva su signo.
    category: calculation
    applies_to: [ComparisonView]
    trigger: Al armar la comparación en la consola
    logic: "La columna Marca es «=» SI los dos valores, tal como se muestran (BR6.4), son iguales o los dos son «No informado» o «sin precio»; si no, «≠». La columna Diferencia, en las filas numéricas, es reporte 2 menos reporte 1 con signo «+» o «−» (porcentajes en puntos porcentuales, «p. p.»), «0» si son iguales, y «—» si un lado es «No informado» o «sin precio»; nunca se resta contra un valor ausente. Las filas no numéricas no tienen diferencia."
    violation: Prueba Vitest de AC12.7.3 con una métrica que baja, otra que sube, una igual y un costo «sin precio» en un lado.
    source: AC12.7.3; punto 9 de la sección 2; mockups M8 §10.3; precisión FD-U12-08

  # BR8 — Accesibilidad de M8
  - id: BR8.1
    statement: M8 y su diálogo de subida entran en la suite axe de U4 con WCAG 2.1 AA y 0 violaciones serious o critical.
    category: constraint
    applies_to: [ResearchReport, ComparisonView]
    trigger: Nivel 3, antes de etiquetar una entrega
    logic: SI axe reporta una violación serious o critical en la lista, el diálogo de subida (vacío, con error y con éxito), el detalle de una corrida, el de una evaluación o la comparación ENTONCES la suite falla.
    violation: Prueba de nivel 3 en rojo.
    source: AC5.6.1; B12 (punto 4); mapa de historias (US5.6)
  - id: BR8.2
    statement: Todo M8 se usa solo con teclado y con el foco siempre visible.
    category: constraint
    applies_to: [ResearchReport, ComparisonView]
    trigger: Nivel 3
    logic: SI subir un archivo, cerrar el diálogo con Escape, filtrar, marcar dos reportes, comparar, abrir un detalle, volver a la lista o copiar una huella exige ratón, o el foco se pierde ENTONCES la prueba falla; al cerrar el diálogo el foco vuelve a «Subir reporte JSON».
    violation: Prueba de nivel 3 en rojo.
    source: AC5.6.2
  - id: BR8.3
    statement: Tipo, origen, cumplimiento, validez y marcas de la comparación se identifican por texto o icono además del color.
    category: constraint
    applies_to: [ResearchReport, MetricValue, ComparisonView]
    trigger: Nivel 0, Vitest
    logic: SI «cumple», «no cumple», «no válida», «=», «≠», el tipo o el origen se distinguen solo por color ENTONCES la prueba falla.
    violation: Prueba Vitest en rojo.
    source: AC5.6.3
  - id: BR8.4
    statement: Los anuncios en vivo de M8 son solo respuesta a una acción del usuario.
    category: policy
    applies_to: [UploadOutcome]
    trigger: Al terminar una subida, al copiar una huella y al comparar
    logic: aria-live anuncia una vez el resultado de validar el archivo (aceptado, duplicado o el primer problema con el total), «SHA-256 copiado» y el aviso de no comparables; nunca anuncia cada fila de la lista ni cada métrica.
    violation: Prueba Vitest que cuenta los anuncios de una subida y de una comparación.
    source: AC5.6.5; regla única de anuncios de mockups (revisión 02, R-09)
```

## Resumen

| Grupo | Reglas | Qué protege |
|---|---|---|
| BR1 Acceso | BR1.1–BR1.4 | Solo el investigador; CSRF; sin edición ni borrado |
| BR2 Validación de la subida | BR2.1–BR2.8 | Validar todo antes de escribir; tope; JSON estricto; C19 vigente; coherencia; llamadas locales; validez de la medición; duplicados |
| BR3 Contraste con lo versionado | BR3.1–BR3.6 | Que una palabra suelta no quepa en un campo con patrón (P1 = A) |
| BR4 Sin eco | BR4.1–BR4.3 | Que el *canary* no llegue a respuestas ni logs (AC12.6.1) |
| BR5 Qué se guarda | BR5.1–BR5.4 | Solo metadatos y cifras; agregados de `runs[]` (P2 = A); quién y cuándo; origen (P3 = A) |
| BR6 Lista y detalle | BR6.1–BR6.7 | «No informado»; cumple con el umbral del reporte; aviso de cuantización; formatos; visibilidad; sesgo; sin configuración |
| BR7 Comparación | BR7.1–BR7.4 | Dos marcados; mismo tipo; mismo conjunto; «=» o «≠» con signo |
| BR8 Accesibilidad | BR8.1–BR8.4 | `axe`, teclado, texto además del color y anuncios |
