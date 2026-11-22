# Requisitos de seguridad — U12 research-reports

**Revisión 1 (2026-11-22): primera pasada de una unidad nueva del cambio 01 (DT27).**
- **IDs.** Todo es **nuevo**. Cada requisito hereda el ID del NFR de Inception que detalla y le añade un
  número (`NFR12.1` detalla NFR12). Los números no se repiten entre los seis documentos de la unidad.
- **Preguntas.** Ninguna: todo lo fijan las fuentes (`nfr-requirements-questions.md` §3). Lo que esta etapa
  aplicó sin preguntar está en la sección 2 de ese archivo y en la tabla NFR-U12-xx (§7).

**Insumos.**
- Flujos F1–F6, errores §9, escenarios E1–E40, preguntas abiertas §11 y tabla FD-U12-01 a FD-U12-12 de
  `functional-design/functional-spec.md` (functional-spec, revisión 1).
- Reglas BR1.1–BR8.4 de `functional-design/rules.md` (rules) y entidades de `functional-design/entities.md`.
- FR1.2, FR1.3, FR9.2, FR13.5 y NFR1–NFR15 de `inception/requirements-analysis/requirements.md`
  (requirements, revisión 3; NFR9 «Retirado»).
- C1 (`/research-reports*`), C15, C16, C18, C19 y C25 de `inception/contract-design/contract-summary.md`
  (contract-summary, revisión 3).
- Lo que fijaron hoy otras unidades:
  - **U1:** `limits.exceeded` siempre `413`, C25 sin nulos, NFR10.7 (`x-veridicus-max-bytes`, `413` y
    `415`) y NFR12.3 (el *canary* de una palabra lo cierra U12).
  - **U2:** tres usuarios de base de datos.
  - **U3:** sesión web de 12 h con cierre a los 30 min, `system.unavailable` y la prueba común de auditoría.
  - **U4:** pila de `session-api` (D9, D11), suite `axe` y escaneo de vocabulario de la interfaz.
  - **U11:** NFR-U11-14, que suma a C19 v2 `blocking`, `origin` y la latencia p50 y p95 por papel.
- Reglas AUTONOMIA-01..05 de `team.md` y prohibiciones de `project.md`.

Las pruebas corren en **nivel 0** (cada PR, sin red ni GPU) salvo que la fila diga otra cosa. El **nivel 1**
usa PostgreSQL real en contenedor. Todos los reportes de prueba son **sintéticos**, generados por un
*script* versionado, y ninguno es un reporte de una corrida real sobre el corpus del piloto. Cada prueba
lleva su control negativo. Los comandos están en `tech-stack-decisions.md` §5.

## 1. Frontera de la unidad (AUTONOMIA-04)

| Componente | Dónde corre | Datos sin seudonimizar que maneja | Qué cruza la frontera del clúster |
|---|---|---|---|
| M8 (pantalla de AnalystConsole) | Navegador del investigador | Ninguno: cifras, hashes, versiones y nombres versionados | El archivo C19 **entra** desde la máquina del investigador (que lo trae de su máquina o de ZINE); nada sale |
| Rutas `/research-reports*` de ConsoleApi | `session-api`, dentro del clúster | Ninguno | Nada |
| Módulo ResearchReports | `session-api`, dentro del clúster | Ninguno | Nada: no llama a modelos, al anonimizador ni a internet |
| Tabla de reportes (y sus tablas hijas) | PostgreSQL (CloudNativePG), dentro del clúster | Ninguno | Nada |
| `ReferenceCatalog` (perfiles, precios, etiquetas) | Memoria de `session-api`, cargado de archivos de solo lectura | Ninguno | Nada |

## 2. Modelo de amenazas (STRIDE)

| # | Amenaza | STRIDE | Riesgo | Mitigación |
|---|---|---|---|---|
| T1 | Un `analista` o un `admin` usa las rutas de reportes | Elevation of privilege | Medio | NFR10.1 |
| T2 | Una subida forjada desde otra página (CSRF) | Spoofing | Medio | NFR10.2 |
| T3 | Un reporte con testimonio (frase o palabra suelta) queda guardado | Information disclosure | Alto | NFR12.1, NFR12.4 |
| T4 | El rechazo repite el valor ofensivo en la respuesta o en los logs | Information disclosure | Alto | NFR10.7, NFR10.8 |
| T5 | El nombre del archivo lleva testimonio y se guarda o se registra | Information disclosure | Medio | NFR10.8 |
| T6 | El cuerpo de la subida se escribe en disco (archivo temporal o búfer del Ingress) | Information disclosure | Medio | NFR10.4 |
| T7 | Un cuerpo enorme, un `Content-Length` falso o un cuerpo por trozos agota la memoria | Denial of service | Medio | NFR10.3 |
| T8 | Un JSON muy anidado, con números no finitos, con enteros enormes o con claves repetidas tumba o engaña al analizador | Denial of service, Tampering | Medio | NFR10.5 |
| T9 | Un número fuera del rango de la base o del navegador da un `500` o una cifra falsa en M8 | Tampering, DoS | Bajo | NFR10.6 |
| T10 | Un reporte guardado se edita o se borra | Tampering, Repudiation | Medio | NFR11.1, NFR11.3 |
| T11 | No se sabe quién subió un reporte | Repudiation | Bajo | NFR11.2 |
| T12 | El catálogo de referencia cambia en ejecución o se carga con un YAML inseguro | Tampering | Medio | NFR10.9 |
| T13 | Un valor guardado se interpreta como HTML en M8 | Tampering (XSS) | Bajo | NFR10.12 |
| T14 | M8 muestra una etiqueta de veracidad | Tampering (AUTONOMIA-03) | Bajo | NFR11.5 |
| T15 | ResearchReports abre un camino de red hacia fuera | Information disclosure | Bajo | NFR1.2 |
| T16 | Una dependencia con una vulnerabilidad conocida | Tampering | Bajo | NFR10.13 |

## 3. Requisitos

### NFR1 — Soberanía de datos

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR1.1 | nuevo | El diseño declara la frontera por componente. | La tabla de §1 está en este documento y en el README del módulo ResearchReports. Un componente nuevo de U12 entra con su fila en el mismo PR | Revisión del PR |
| NFR1.2 | nuevo | U12 no abre ningún camino de red hacia fuera del clúster. | Un contrato de import-linter prohíbe que el módulo ResearchReports y sus rutas importen `httpx`, `requests`, `urllib.request`, `libs.model_gateway` y `libs.anonymizer`; un módulo de prueba que los importa hace fallar el contrato. La `NetworkPolicy` de U2 no cambia por U12 | Nivel 0 |

### NFR10 — Seguridad de la aplicación

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR10.1 | nuevo | Solo el `investigador` usa las rutas de reportes (BR1.1, BR1.2). | 8 pruebas (2 roles rechazados × 4 rutas): `403` `auth.forbidden`, Problem Details en español y 0 filas nuevas. Sin cookie: `401`. La navegación de M8 se prueba con los tres roles en Vitest | Nivel 1 y Vitest |
| NFR10.2 | nuevo | La subida exige el token CSRF (BR1.3). | Sin `X-CSRF-Token` y con el de otra sesión: `403` `auth.csrf`, 0 filas, y el cuerpo **no se lee** (la prueba cuenta 0 bytes consumidos del flujo después de las cabeceras) | Nivel 1 |
| NFR10.3 | nuevo | El tope de bytes se aplica mientras se lee (BR2.2). | La lectura se corta al pasar `research_report_max_bytes` (8 388 608, NFR-U12-01): `413` `limits.exceeded`, sin SHA-256 y sin filas. Casos: archivo de tope + 1 bytes; `Content-Length` que dice menos que el cuerpo real; cuerpo por trozos sin `Content-Length`; `Content-Length` mayor que el tope (se rechaza antes de leer). En todos, el proceso no lee más de tope + 64 KiB (cabeceras del `multipart`) | Nivel 1 |
| NFR10.4 | nuevo | El archivo subido no toca el disco (BR5.1, «ni en disco»). | El `multipart` se analiza en memoria con un búfer acotado al tope (`tech-stack-decisions.md` D2). Una prueba sustituye `tempfile.SpooledTemporaryFile`, `tempfile.NamedTemporaryFile` y `open` en modo escritura por funciones que fallan y sube un archivo de 8 MiB: responde `201`. En el clúster, el Ingress de la ruta no guarda el cuerpo en disco (NFR-U12-05) | Nivel 1 e Infrastructure Design |
| NFR10.5 | nuevo | El JSON se analiza de forma estricta y acotada (BR2.3). | (a) La profundidad se comprueba **antes** de construir objetos, con un recorrido lineal de los bytes que ignora lo que está entre comillas: más de `research_report_max_json_depth` (8) niveles da `json_depth`. Un archivo de 8 MiB con `[` repetidos responde `422` en ≤ 1 s y sin `RecursionError`. (b) BOM o UTF-8 inválido: `encoding`. (c) Claves repetidas en un objeto: `json_duplicate_key` (control: una clave benigna y otra con el *canary*). (d) `NaN`, `Infinity`, `-Infinity` y todo número que se convierte en infinito (`1e400`): `json_non_finite`. (e) Un entero de más de 4 300 cifras (el `ValueError` de Python 3.12) da `out_of_range`, nunca un `500`. Todos con `422` `research.invalid_report` y 0 filas | Nivel 0 |
| NFR10.6 | nuevo | Toda cifra aceptada cabe en la base y se muestra exacta en el navegador (NFR-U12-03). | Todo entero del reporte (*tokens*, conteos, `seed`, `expected`, `found`) está entre 0 y 9 007 199 254 740 991 (2^53 − 1, salvo `seed`, que admite el negativo simétrico); `estimated_cost` es finito y ≤ 1 000 000 000. Fuera de rango: `out_of_range`, `422`. La suma de `input_tokens` de las llamadas no se recalcula (BR6.4 muestra lo del reporte) | Nivel 0 |
| NFR10.7 | nuevo | Ningún rechazo repite valores del archivo (BR4.1, F6). | El `detail` sale solo de textos fijos del catálogo, la ruta del primer problema (nombres del esquema e índices), el total y el SHA-256. Una prueba de nivel 0 recorre todos los `rule` de `ValidationProblem` y comprueba que cada `detail` es una plantilla del catálogo con huecos para ruta, total, línea y columna. El valor esperado de un `pattern` y los mensajes de `json` y de `jsonschema` nunca aparecen | Nivel 0 |
| NFR10.8 | nuevo | El nombre del archivo, el cuerpo y el texto de las excepciones no se guardan ni se registran (BR4.2). | Con el *canary* como nombre del archivo, como contenido inválido y dentro de una excepción del validador: 0 coincidencias en los logs capturados (aplicación, `uvicorn.access` y `uvicorn.error`) y en las columnas. El manejador único registra solo clase, `code`, ruta del primer problema e IDs. El registro de acceso de Uvicorn no lleva cuerpo ni cabeceras de la petición | Nivel 1 |
| NFR10.9 | nuevo | El catálogo de referencia es de solo lectura y se carga con los cargadores seguros de U1 (BR3.6). | `config/profiles.yaml` (validado por ExecutionProfiles), `config/prices.yaml` y las dos listas de etiquetas se leen con los cargadores de `veridicus_contracts` (YAML seguro, sin claves duplicadas). Si falta uno, no valida o trae una clave repetida, `session-api` no arranca y el log nombra el archivo, nunca su contenido. Una comprobación estática falla si un módulo fuera del cargador abre esos archivos en modo escritura. En el clúster se montan de solo lectura (Infrastructure Design) | Nivel 0 |
| NFR10.10 | nuevo | Todo error es Problem Details con un `code` estable y un `detail` en español. | Cada respuesta `403`, `404`, `409`, `413`, `415`, `422` y `503` de las rutas de U12 valida contra `Problem` de C1 y usa un `code` del catálogo de U1. Una petición que no es `multipart/form-data` da `415` `research.invalid_type` (NFR-U12-02). Sin parte `file`, o con otra parte además de `file`, da `422` `validation.invalid_request` | Nivel 1 |
| NFR10.12 | nuevo | M8 no interpreta como HTML ningún valor guardado. | M8 no usa `dangerouslySetInnerHTML` (`react/no-danger` como error, `team.md`). Una prueba Vitest dibuja un reporte cuyo `profile_name` del *fixture* del componente (sin pasar por la API) es `<img src=x onerror=alert(1)>` y comprueba que aparece como texto. Las cadenas que llegan de la API ya cumplen sus patrones, que no admiten `<` ni espacios | Vitest |
| NFR10.13 | nuevo | Dependencias fijadas y auditadas. | `services/session-api/uv.lock` y `frontend/package-lock.json` con *hashes*; `pip-audit` y `npm audit --audit-level=high` sin hallazgos `HIGH` o `CRITICAL` con corrección; Trivy sobre la imagen de `session-api` | CI |

### NFR11 — Integridad y auditoría

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR11.1 | nuevo | Un reporte guardado no se modifica ni se borra (BR1.4). | Con `veridicus_app`, un `UPDATE` y un `DELETE` sobre la tabla y cada tabla hija fallan con permiso denegado. El usuario del `Job` de retención no tiene `DELETE` sobre ellas (la marca `history` con `purgeable: false` y `owner_unit: U12` las saca de su lista). Lo comprueba la prueba común de auditoría de U3 | Nivel 1 |
| NFR11.2 | nuevo | Todo reporte guarda quién lo subió y cuándo (BR5.3, FR1.3). | `uploaded_by` y `uploaded_at` son `NOT NULL` en la tabla y en cada tabla hija (copia de los del padre). Un `INSERT` sin ellos falla | Nivel 1 |
| NFR11.3 | nuevo | La API no ofrece editar ni borrar reportes. | El OpenAPI generado no declara `PUT`, `PATCH` ni `DELETE` bajo `/research-reports` (E39) | Nivel 0 |
| NFR11.5 | nuevo | M8 no muestra etiquetas de veracidad (AUTONOMIA-03, BR6.7). | Todos los textos de M8 salen del catálogo de mensajes y entran en el escaneo de vocabulario de la interfaz de U4, con 0 coincidencias. M8 no muestra hallazgos, citas ni observaciones. «Cumple» y «no cumple» solo acompañan a una métrica con su umbral | Nivel 0 |

NFR11.4 (atomicidad) y NFR11.6 (subidas simultáneas) están en `reliability-requirements.md`.

### NFR12 — Datos reales fuera del repositorio

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR12.1 | nuevo | El *canary* de AC12.6.1 no queda en ningún lado (FR13.5, CD-03). | Matriz de casos con «CANARIO-7f3a»: dentro de un hallazgo; como nombre de un campo en la raíz y en una llamada; como valor de `profile_name`, `model`, `version`, `engine`, `effort_or_quantization`, `price_table_version` y `synthetic_set`; y como nombre del archivo. Todos responden `422` `research.invalid_report`, salvo el del nombre del archivo, que se acepta o se rechaza por su contenido. En cada caso: 0 filas con el *canary*, y una búsqueda del *canary* en la respuesta, en **todas** las columnas de texto de todas las tablas de `session-api` (enumeradas desde `information_schema.columns`) y en los logs capturados da **0 coincidencias** | Nivel 1 |
| NFR12.2 | nuevo | Ningún `interview_sha256` individual llega a la base (BR5.2). | Tras subir un reporte de 10 corridas, ninguno de sus 10 `interview_sha256` aparece en ninguna columna; `inputs_fingerprint` es igual con las entradas en otro orden y distinto con una entrada cambiada | Nivel 1 y nivel 0 |
| NFR12.3 | nuevo | Los reportes de prueba son sintéticos. | Los *fixtures* de U12 los genera `services/session-api/tests/fixtures/make_research_reports.py` con los perfiles y etiquetas de prueba. Ninguno sale de una corrida real sobre el corpus del piloto (`team.md`, Forbidden). La comprobación de U1 (`synthetic: true`) corre sobre ellos | Nivel 0 |
| NFR12.4 | nuevo | La base rechaza por sí misma una columna de texto libre (defensa en profundidad, NFR-U12-07). | Cada columna de texto de U12 lleva un `CHECK` con su patrón (hashes `^[a-f0-9]{64}$`, versiones semánticas, enum) o, para los nombres contrastados (`profile_name`, `model`, `version`, `engine`, `effort_or_quantization`, `price_table_version`, `story_fact_type`, `persona_profile`), longitud ≤ 128 y sin espacios. Una prueba de nivel 0 sobre la migración falla si una columna `text` o `varchar` de U12 no tiene `CHECK`; una de nivel 1 intenta insertar «dos palabras» con `veridicus_app` y falla | Nivel 0 y nivel 1 |

### NFR14 — Idioma

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR14.1 | nuevo | Los textos de M8 y los `detail` están en español y salen del catálogo. | Una prueba de nivel 0 falla si un componente de M8 tiene un literal visible fuera del catálogo de mensajes, o si un `detail` de U12 no es una plantilla del catálogo. Los identificadores siguen el glosario en inglés | Nivel 0 |

## 4. Correspondencia con AUTONOMIA

| Regla | Requisitos de U12 |
|---|---|
| AUTONOMIA-01 | No aplica cambios al clúster; la migración de la tabla entra por su `Job` y su PR (`project.md`). El catálogo de referencia cambia solo por PR (NFR10.9) |
| AUTONOMIA-02 | Cada requisito nombra su umbral; los comandos están en `tech-stack-decisions.md` §5 |
| AUTONOMIA-03 | NFR11.5 |
| AUTONOMIA-04 | §1; NFR1.1, NFR1.2; NFR12.1 (nada sale ni entra con testimonio) |
| AUTONOMIA-05 | No aplica: U12 no emite hallazgos |

## 5. Cumplimiento

- **Retención (VE-12).** La tabla no guarda datos de la persona entrevistada, por lo que la retención no la
  toca (BR1.4). `uploaded_by` es el identificador de un usuario del sistema, no de un testimonio.
- **Registro de acceso (VE-11).** M8 no abre sesiones ni reportes de revisión, así que no llama a
  `AccessLog` (BR4.3). La línea de log de cada subida cubre el quién y el cuándo.
- **Repositorio público (`project.md`).** Ningún reporte real entra al repositorio (NFR12.3).

## 6. Riesgos aceptados o transferidos

| Riesgo | Tratamiento |
|---|---|
| **Un nombre real que coincide con un valor versionado** (por ejemplo, un perfil llamado como una persona) | Transferido a la revisión del PR de `config/profiles.yaml` y de las listas de etiquetas: lo versionado es lo único que U12 acepta (P1 = A) |
| **El Ingress guarda el cuerpo en disco** si su configuración no se ajusta | Transferido a Infrastructure Design (NFR-U12-05). El riesgo es bajo, porque un reporte válido no lleva testimonio y uno inválido se rechaza |
| **Un investigador con sesión sube muchos archivos grandes** | Aceptado: hay un solo investigador en el MVP. Dos subidas simultáneas máximas caben en la memoria (NFR3.8). No hay límite de frecuencia |
| **Un investigador ve los reportes de otro** | Aceptado por diseño (BR6.5): solo hay cifras |

## 7. Precisiones a artefactos ya aprobados (NFR-U12-xx)

No edité ningún artefacto aprobado (regla de `project.md`). En la aprobación decides cuáles se llevan al
original, cada una en su propio commit. Todas salen de las fuentes; no hubo preguntas.

| ID | Artefacto aprobado | Precisión | Origen |
|---|---|---|---|
| NFR-U12-01 | `contract-summary.md` (C25) y U1 (catálogo de límites) | Cifras de U12: `research_report_max_bytes = 8388608` (`bytes`), `research_report_max_json_depth = 8` (`levels`) y una cifra nueva, `research_report_write_timeout_s = 15` (`s`), el plazo de la transacción de escritura (NFR10.14). Dimensionadas en `scalability-requirements.md` §1. Entran por PR de U1 antes del código de B12 | Preguntas abiertas 1 y 3 del Functional Design; FD-U12-12; regla de `project.md` sobre el catálogo único |
| NFR-U12-02 | `contract-summary.md` (C1, `POST /research-reports`) y U1 (catálogo de `code`) | Entra `415` `research.invalid_type` cuando la petición no es `multipart/form-data`, como pide NFR10.7 de U1 para toda subida `multipart` (simétrico a `import.invalid_type`). Sin parte `file`, o con otra parte, es `422` `validation.invalid_request`. El tipo de la parte `file` no se comprueba: lo decide el análisis del JSON | NFR10.7 de U1 |
| NFR-U12-03 | `rules.md` (BR2.3 y BR2.5) y `entities.md` | BR2.3 suma: un número que se convierte en infinito (`1e400`) es `json_non_finite`, y un entero de más de 4 300 cifras es `out_of_range`. BR2.5 suma los rangos de NFR10.6: enteros entre 0 y 2^53 − 1 (`seed` también negativo) y `estimated_cost` ≤ 10^9. C19 no fija máximos; sin ellos, la base o el navegador fallan o redondean | NFR10.5, NFR10.6 |
| NFR-U12-04 | `entities.md` (`ResearchReport`, `ModelCallRecord`), BR5.1 y `functional-spec.md` §6.3 | C19 v2 trae `blocking` y la latencia p50 y p95 por papel (NFR-U11-14), y `clarifications` (FD-U8-09). Los tres pasan el esquema. Se guardan `blocking` (booleano opcional, junto a `overall_passes`, que M8 muestra como «Bloqueante: sí / no») y la latencia por papel (enteros en milisegundos, en el registro de modelos de M8). `clarifications` no se guarda ni se muestra: ninguna historia de U12 la pide. Sin esta precisión, M8 mostraría «no cumple» sin decir si bloquea | NFR-U11-14; FD-U8-09; FR13.5 |
| NFR-U12-05 | Infrastructure Design de U2 y de U12 (Ingress de `session-api`) | La ruta `POST /api/v1/research-reports` acepta cuerpos de `research_report_max_bytes` + 64 KiB (`proxy-body-size`), para que el `413` lo dé `session-api` como Problem Details y no ingress-nginx en HTML. Además, no guarda el cuerpo en disco: búfer de petición ≥ ese tamaño o sin *buffering* de petición, como el Ingress `veridicus-voice` | NFR10.3, NFR10.4; BR5.1 |
| NFR-U12-06 | Infrastructure Design (empaquetado del catálogo, pregunta abierta 4 del Functional Design) | `config/profiles.yaml`, `config/prices.yaml` y `evaluation/labels/*.v1.yaml` llegan a `session-api` de solo lectura, desde la imagen o un `ConfigMap`, y su `catalog_sha256` sale en el log de arranque. Un cambio entra por PR y llega con el siguiente despliegue (FR9.2) | BR3.6; NFR10.9 |
| NFR-U12-07 | `entities.md` (restricciones de `ResearchReport`) | Cada columna de texto lleva un `CHECK` con su patrón o con longitud ≤ 128 y sin espacios (NFR12.4). Las listas se guardan en tablas hijas con columnas tipadas, no en un JSON: es lo que permite poner esos `CHECK` (D4 de `tech-stack-decisions.md`). La decisión final es de Code Generation | NFR12.4; `entities.md` (lo deja a Code Generation) |
