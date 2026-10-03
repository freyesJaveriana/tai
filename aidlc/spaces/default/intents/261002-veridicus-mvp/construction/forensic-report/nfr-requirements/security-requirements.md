# Requisitos de seguridad — U7 forensic-report

**Insumos.** Frontera AUTONOMIA-04 (§1), flujos F1–F7 y §7 «Errores en la frontera» de
`functional-design/functional-spec.md` (functional-spec); reglas BR1–BR8 de `functional-design/rules.md`
(rules) y entidades de `entities.md`; FR7 y NFR1, NFR10–NFR12 y NFR14 de
`inception/requirements-analysis/requirements.md` (requirements); C1, C8, C11 y C15 de
`inception/contract-design/contract-summary.md` (contract-summary); `nfr-requirements-questions.md`
(sin preguntas nuevas); reglas AUTONOMIA-01..05 de `team.md` y prohibiciones de `project.md`.

Cada requisito hereda el ID del NFR de Inception que detalla. Niveles de team-practices: nivel 0
(unitarias, contratos y políticas, cada PR), nivel 1 (integración con PostgreSQL real y el volumen real
en contenedor, cada PR), nivel 3 (E2E) y manual. Los comandos están en `tech-stack-decisions.md` §5. La
autenticación, la sesión web, el anti-CSRF, la autorización por rol y `AuditConvention` vienen de U3; la
comprobación de dueño vive en ConsoleApi (ADR-009); el escáner `scan(text, literal_sources)` es el de
`libs/integrity_policy` (U4); las rondas y decisiones son de U5 (C11). Aquí solo se exige que U7 los use
y se fijan sus pruebas.

## 1. Frontera de la unidad (AUTONOMIA-04)

| Componente | Dónde corre | Qué datos cruzan su frontera | Clasificación |
|---|---|---|---|
| ConsoleApi (rutas `/finalize`, `/reports`, `/correction-rounds`, descarte y `/download`) | API de `session-api`, dentro del clúster, bajo la `NetworkPolicy` de salida denegada de U2 | Peticiones del navegador; `ReportVersion` y el Markdown del reporte hacia el navegador del analista (C1). Es la entrega prevista dentro del clúster, no una salida a internet | Confidencial |
| ForensicReport (guardia, render, escaneo, persistencia, barrido) | Módulo de la API de `session-api`, dentro | Llamadas en proceso a InterviewSession, HumanReview y TruthFrame (C11) e IntegrityPolicy (C8); filas en PostgreSQL interno | Confidencial |
| Volumen persistente de reportes (PVC `veridicus-reports`) | Dentro del clúster, montado **solo** en el contenedor de la API de `session-api` | Archivos Markdown completos del caso (transcripción, CoT, notas) | Confidencial |
| PostgreSQL (CloudNativePG) | Dentro | `ReportVersion`: identificadores, SHA-256, tamaños, actor y hora; **sin texto del caso** | Interna |
| Métricas de U7 | `/metrics` del puerto interno de `session-api` | Solo contadores, histogramas y valores de enum (NFR10.10) | Interna |
| AnalystConsole (diálogos, vista del reporte, lista de versiones, copia de trabajo) | Navegador del analista, servido por `frontend` | Solo habla con ConsoleApi (ADR-004) | Confidencial |
| Arnés de MTTV (`evaluation/golden/mttv.py`) | Máquina de desarrollo, contra la API dentro del clúster o el entorno de contenedores | Solo `finalized_at`, `consolidated_at` e identificadores; nunca descarga reportes | Interna |

**Ningún componente de U7 hace una llamada fuera del clúster ni a un modelo.** El reporte es el
artefacto más sensible del sistema porque junta en un solo archivo todo el caso; aunque en el MVP los
datos son sintéticos (NFR12), se trata como si fueran reales.

## 2. Modelo de amenazas (STRIDE)

| # | Amenaza | STRIDE | Riesgo | Mitigación |
|---|---|---|---|---|
| T1 | Otro analista, un `admin` o una identidad de servicio finaliza, consolida, corrige o descarta | Elevation of privilege | Alto | NFR10.1 |
| T2 | Un `admin` o una identidad de servicio lee o descarga reportes (P4 = A) | Information disclosure | Alto | NFR10.2 |
| T3 | Petición falsificada desde otro sitio que finaliza, consolida o descarta | Tampering | Medio | NFR10.3 |
| T4 | Consolidación automática sin acción explícita del analista (AUTONOMIA-03) | Elevation of privilege | Alto | NFR11.2 |
| T5 | Consolidar con sugerencias pendientes o turnos en curso por una carrera entre la guardia y el bloqueo | Tampering | Alto | NFR10.13, NFR10.14 (reliability) |
| T6 | Alterar el archivo del reporte en el volumen después de consolidar | Tampering | Alto | NFR11.3, NFR11.4 |
| T7 | Reescribir o borrar una `ReportVersion` para ocultar una versión | Repudiation | Alto | NFR11.1 |
| T8 | Una corrección reescribe la versión anterior | Tampering | Alto | NFR11.5 |
| T9 | Recorrido de rutas o lectura de otro archivo del volumen desde `/download` | Information disclosure | Medio | NFR10.5 |
| T10 | Otro pod o proceso lee el volumen de reportes | Information disclosure | Alto | NFR10.6 |
| T11 | Texto del reporte en logs, métricas, errores o respuestas de rechazo | Information disclosure | Alto | NFR10.7, NFR10.8, NFR10.10 |
| T12 | Una etiqueta de veracidad en el reporte consolidado | Tampering | Alto | NFR10.9 |
| T13 | El navegador interpreta el Markdown descargado como HTML o lo guarda en caché | Information disclosure | Medio | NFR10.4 |
| T14 | Cambiar la transcripción o la salida de la IA desde la copia de trabajo | Tampering | Alto | NFR10.11 |
| T15 | Suplantar al actor o la hora enviando `consolidated_by`, `consolidated_at` o `finalized_at` en el cuerpo | Spoofing | Medio | NFR10.1, NFR7.3 |

## 3. Requisitos

### NFR1 — Soberanía de datos

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR1.1 | U7 no abre conexiones salvo a PostgreSQL y al volumen local. | El paquete `forensic_report` no importa clientes HTTP (`httpx`, `requests`, `urllib`), de Redis ni `model_gateway` (contrato de import-linter con control negativo: un módulo de prueba que importa `httpx` hace fallar el contrato); `session-api` queda bajo la `NetworkPolicy` de salida denegada de U2, que es la defensa de fondo. | Nivel 0 |
| NFR1.2 | El volumen de reportes no sale del clúster. | El PVC `veridicus-reports` usa una `StorageClass` local del clúster (la fija Infrastructure Design), se monta solo en el contenedor de la API de `session-api` y ningún manifiesto lo monta en otro pod, `Job` o `CronJob` salvo el de verificación de NFR10.20, en solo lectura. Política estática sobre el render de `helm template` (Kyverno CLI) con control negativo. | Nivel 0 |

### NFR10 — Seguridad de la aplicación

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR10.1 | Solo el analista dueño finaliza, consolida, corrige y descarta (BR1.1, BR2.1, BR6.1, ADR-009). | Las cuatro rutas declaran `x-veridicus-roles: [analista]` y `x-veridicus-owner-only: true`; ConsoleApi obtiene el dueño desde la sesión **en el servidor** antes de delegar en ForensicReport. Pruebas por ruta: otro analista → `403` (`session.not_owner`), `admin` y una identidad de servicio → `403` `auth.forbidden`, sin sesión web → `401`; en cada caso 0 filas en `ReportVersion`, 0 cambios de estado de sesión o ronda y 0 archivos en el volumen. El actor y la hora son siempre del servidor: un cuerpo con `consolidated_by`, `consolidated_at`, `finalized_at`, `actor_user_id` u otro campo no declarado responde `422` `validation.invalid_request` (`additionalProperties: false`). | Nivel 1 |
| NFR10.2 | Leen y descargan solo analistas (BR5.3, P4 = A). | `GET /sessions/{id}/reports` y `GET /reports/{id}/download` declaran `x-veridicus-roles: [analista]` sin `x-veridicus-owner-only` (precisión §6). Pruebas: el dueño y otro analista → `200`; `admin` → `403` `auth.forbidden`; identidad de servicio → `403`; sin sesión web → `401`. Ningún `403` envía bytes del reporte ni la cabecera `X-Veridicus-SHA256`. | Nivel 1 |
| NFR10.3 | Las rutas que escriben exigen el anti-CSRF de U3. | `POST /finalize`, `POST /reports`, `POST /correction-rounds` y el descarte: sin `X-CSRF-Token` o con uno distinto → `403` `auth.csrf`, 0 filas y 0 archivos. `GET` de lista y descarga no cambian estado (prueba que compara filas antes y después). | Nivel 1 |
| NFR10.4 | La descarga no se interpreta ni se guarda en caché. | Respuesta `200` con `Content-Type: text/markdown; charset=utf-8`, `Content-Disposition: attachment; filename="veridicus-reporte-<report_version_id>.md"` (nombre derivado solo del UUID), `X-Content-Type-Options: nosniff`, `Cache-Control: no-store` y `X-Veridicus-SHA256` con los 64 caracteres. La consola nunca inserta el Markdown como HTML: la vista del reporte lo muestra como texto (`react/no-danger` en error, team-practices) y una prueba Vitest con `<script>` y `<img onerror>` sembrados en una nota comprueba que no se ejecutan. | Nivel 1 y Vitest |
| NFR10.5 | `/download` solo lee el archivo registrado de esa versión (T9). | `report_version_id` se valida como UUID en la ruta (`422` si no lo es); la ruta del archivo se calcula como `<raíz del volumen>/<report_version_id>.md` y se compara con `storage_path` de la fila; el valor de la petición nunca se concatena a una ruta. Un `report_version_id` sin fila responde `409` `report.not_consolidated` (precisión §6). Pruebas con `..%2F`, rutas absolutas y un enlace simbólico plantado en el volumen: `422` o `409 report.integrity_mismatch`, nunca el contenido de otro archivo (la apertura usa `O_NOFOLLOW`). | Nivel 1 |
| NFR10.6 | El volumen solo lo lee el proceso de la API (T10). | El contenedor corre sin root (perfil `restricted`, NFR10.2 de U2) con `fsGroup` propio; el directorio de reportes tiene modo `0700` y cada archivo final `0400` (solo lectura del dueño, nunca se reescribe, NFR11.4); el proceso fija `umask 077` al arrancar. `/readyz` comprueba al arrancar que el directorio existe, es escribible y tiene esos permisos (NFR10.19). Prueba de nivel 1 que consolida y lee `stat()` del archivo y del directorio; política de nivel 0 de NFR1.2 sobre los montajes. | Nivel 0 y nivel 1 |
| NFR10.7 | Los logs de U7 solo llevan identificadores (BR7.2). | Campos permitidos: `session_id`, `report_version_id`, `round_id`, `user_id`, `version_number`, `byte_size`, `sha256`, `code`, nombre de archivo (siempre `<uuid>.md` o `<uuid>.md.tmp`), duraciones y conteos. Prueba de nivel 1: con una cadena centinela sembrada en un turno, una CoT, una nota, una reformulación y un pasaje, 0 coincidencias en los logs capturados de `session-api` en los caminos `200`, `201`, `403`, `409` (todos los `code` de U7), `422`, `500`, `503`, en el barrido y en una violación de restricción de la base (*engine* con `hide_parameters=True`, D5 de U5). | Nivel 1 |
| NFR10.8 | Los errores no devuelven texto del caso. | Cada rechazo sale como Problem Details (`application/problem+json`) con un `code` de C1 y el `detail` en español del catálogo de U1; `report.forbidden_vocabulary` trae la ubicación (ID de turno o de sugerencia y sección, BR3.3) y **nunca** el término ni el texto que lo rodea. Con la cadena centinela de NFR10.7, 0 coincidencias en los cuerpos de error. | Nivel 1 |
| NFR10.9 | El reporte consolidado no lleva etiquetas de veracidad (AUTONOMIA-03, BR3.3). | Antes del SHA-256, el Markdown completo pasa por `scan(text, literal_sources)` con C8. Son `literal_sources` (y por eso no se marcan): los turnos de la transcripción y los fragmentos (`literal_testimony_quote`), las citas y los pasajes de los paquetes (`literal_scenario_quote`), y las notas y reformulaciones (`analyst_text`) (precisión §6). Se escanean los rótulos, encabezados y textos de la plantilla, la CoT de la IA y los textos del sistema. Pruebas de nivel 0: «miente» en un texto del sistema o en una CoT hace fallar la consolidación con la ubicación; «falso» en un turno, en una cita o en una nota no; la plantilla vacía de `format_version` 1 da 0 coincidencias. Prueba de nivel 1: 0 filas y 0 archivos tras el rechazo, y la ronda sigue abierta. | Nivel 0 y nivel 1 |
| NFR10.10 | Las métricas de U7 no llevan texto. | Las etiquetas de NFR15.1 solo toman valores de su enum (`result`, `code`); no hay etiqueta `session_id` ni `report_version_id`. Prueba de nivel 0 que recorre las series registradas y valida cada etiqueta contra su patrón, y prueba de nivel 1 con la cadena centinela: 0 coincidencias en la salida de `/metrics`. | Nivel 0 y nivel 1 |
| NFR10.11 | La copia de trabajo solo cambia estados y notas (BR6.3). | Una petición que intenta cambiar transcripción, fragmento, cita, documento o CoT responde `422` `validation.invalid_request` con 0 filas; el SHA-256 de esos campos y el de los bytes de la versión vigente son iguales antes y después de corregir y consolidar la versión N+1 (NFR11.5). | Nivel 1 |

### NFR11 — Integridad y auditoría

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR11.1 | `ReportVersion` solo admite inserciones (BR4.4). | Tabla registrada en `AuditConvention` de U3; el usuario de la aplicación tiene solo `INSERT` y `SELECT`; `UPDATE`, `DELETE` y `TRUNCATE` fallan por permisos; `consolidated_by` y `consolidated_at` `NOT NULL`. Restricciones como segunda barrera: `UNIQUE (session_id, version_number)`, `UNIQUE (round_id)`, `UNIQUE (storage_path)`, `CHECK ((version_number = 1) = (supersedes_version_id IS NULL))`, `CHECK (sha256 ~ '^[a-f0-9]{64}$')`, `CHECK (byte_size > 0)` y claves foráneas a sesión, ronda, usuario, versión de escenario y versión reemplazada. Una prueba por restricción. | Nivel 1 (prueba común de U3 y pruebas propias) |
| NFR11.2 | Ninguna consolidación ocurre sin la acción explícita del analista dueño (AUTONOMIA-03, FR7.1). | La única entrada que llama `consolidate` es la ruta `POST /sessions/{id}/reports` de ConsoleApi: contrato de import-linter que prohíbe importar `forensic_report.application.consolidate` desde el trabajador de `session-api`, `semantic-agent`, `evaluation/` y cualquier módulo distinto de la ruta (control negativo en la CI). Cada versión registra quién (`consolidated_by`, principal autenticado) y cuándo (`consolidated_at`, reloj del servidor), y la vista de BR8.2 los muestra. | Nivel 0 y nivel 1 |
| NFR11.3 | El SHA-256 registrado es el de los bytes guardados y se comprueba en cada descarga (BR3.4, BR5.1). | Prueba de nivel 1: tras consolidar, `sha256sum` del archivo coincide con la fila y con la respuesta `201`. Se altera 1 byte del archivo, se trunca y se borra: las tres descargas responden `409` `report.integrity_mismatch` sin enviar bytes, con un `ERROR` que solo lleva el `report_version_id` y `+1` en `veridicus_report_downloads_total{result="integrity_mismatch"}`. | Nivel 1 |
| NFR11.4 | Un archivo final nunca se reescribe. | El archivo temporal se crea con `O_CREAT \| O_EXCL` y el renombrado final con `os.link` + `unlink` del temporal (falla si el destino existe) o `renameat2(RENAME_NOREPLACE)`; el archivo final queda en `0400`. Prueba de nivel 1: plantar un archivo con el nombre del `report_version_id` siguiente hace fallar la consolidación con `500` `report.storage_failed` (precisión §6) sin tocar el archivo plantado. | Nivel 1 |
| NFR11.5 | Corregir crea una versión nueva y deja la anterior intacta (BR6.5). | Tras consolidar la versión 2: la fila y el archivo de la versión 1 no cambian (mismo `stat().st_mtime`, mismo SHA-256 recalculado, misma fila), la versión 2 tiene `supersedes_version_id` = versión 1 y la lista marca la 2 como vigente. | Nivel 1 |
| NFR11.6 | Una copia descartada deja rastro y no cuenta (BR6.4). | La ronda pasa a `discarded` con `discarded_by` y `discarded_at` (C11 v1.1.0, X1 de functional-spec); sus decisiones siguen en `ReviewDecision` (solo inserción, NFR11.1 de U5) y ninguna `ReportVersion` la referencia. Un segundo descarte responde `409` `report.conflict`. | Nivel 1 |

### NFR12 — Datos sintéticos

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR12.1 | Los *fixtures* y reportes esperados de U7 son sintéticos. | El caso de 100 turnos, los reportes esperados (*golden files*) de `services/session-api/tests/forensic_report/` y los informes del arnés de MTTV usan el catálogo de nombres y las marcas sintéticas de U1; la comprobación de U1 sobre esas rutas da 0 hallazgos. Ningún reporte de una corrida real se versiona: `evaluation/out/` está en `.gitignore`. | Nivel 0 |

### NFR14 — Idioma

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR14.1 | El reporte y las pantallas de U7 están en español. | Los encabezados, rótulos y textos de la plantilla de `format_version` 1 y los textos de los diálogos (BR1.5, BR8.1–BR8.3) salen del catálogo de U1; la prueba de nivel 0 de U4 sobre literales visibles cubre los componentes de U7, y una prueba de nivel 0 recorre la plantilla y comprueba que cada texto fijo está en el catálogo. Fechas del reporte en ISO 8601 UTC (BR3.2); fechas de la consola en hora de Colombia (BR8.2). | Nivel 0 |

## 4. Trazabilidad de AUTONOMIA

| Regla | Requisitos de U7 |
|---|---|
| AUTONOMIA-01 | U7 no aplica nada al clúster: la tabla `ReportVersion` y sus permisos entran por la migración de su PR (`Job` aparte), el PVC y sus montajes por el chart de U2 (PR) y el `Job` de verificación de NFR10.20 es un manifiesto revisable que el humano aplica |
| AUTONOMIA-02 | Cada requisito tiene su criterio y su comando (`tech-stack-decisions.md` §5) |
| AUTONOMIA-03 | NFR10.9, NFR10.11, NFR11.1–NFR11.6; guardia de consolidación, persistencia y corrección con 100 % de ramas (NFR13.2); atomicidad (NFR10.12–NFR10.14) |
| AUTONOMIA-04 | §1, NFR1.1, NFR1.2, NFR10.6, NFR10.7, NFR10.8, NFR10.10 |
| AUTONOMIA-05 | No aplica directamente: U7 solo consolida lo que ya pasó la guardia del umbral de U4; el reporte muestra el umbral de la sesión (BR3.1) y los Hechos No Documentados con su paquete, nunca como alertas |

## 5. Riesgos aceptados

- **El volumen no está cifrado por la aplicación.** El reporte se guarda en claro en un PVC local del
  clúster; la protección es el acceso al nodo, los permisos de NFR10.6 y la `NetworkPolicy`. El cifrado
  en reposo del disco lo decide Infrastructure Design. En el MVP los datos son sintéticos (NFR12).
- **El SHA-256 detecta alteraciones, no las impide.** Quien tenga acceso de escritura al nodo puede
  cambiar el archivo y la fila a la vez; la fila es de solo inserción (NFR11.1) y el usuario de la
  aplicación no puede cambiarla, así que esa alteración exige credenciales de administración de la base.
- **La descarga queda en el equipo del analista.** Una vez descargado, el reporte sale del control del
  sistema; es la entrega prevista por FR7.4 y queda registrada en el log `report.downloaded` con quién
  y cuándo (NFR15.2).

## 6. Precisiones a artefactos ya aprobados

Estas decisiones precisan artefactos ya aprobados. No los edité; decides en la aprobación si se
actualizan.

| Artefacto | Qué precisa | Origen |
|---|---|---|
| `contract-design/contract-summary.md` (C11) y Functional Design de U7 (F2 paso 4, BR4.2) | La consolidación llama `ReviewRounds.open_round(uow, session_id, for_update=True)` **antes** de leer `pending_count` y `decisions`, de modo que la ronda queda bloqueada (`SELECT … FOR UPDATE`) desde la guardia hasta el *commit*; es la misma precisión que registró U5 (`security-requirements.md` §6 de U5, hallazgo R-02 de su revisión). Sin ella, la prueba de NFR10.14 falla | NFR10.13, NFR10.14; hallazgo R-03 de la revisión del Functional Design de U7 |
| Functional Design de U7 (BR3.3, `entities.md` `ReportContent.scan_exclusions`) | Los tramos excluidos del escaneo incluyen **todos los turnos de la transcripción** (testimonio y entrevistador, `literal_testimony_quote` de C8) y los pasajes de los Paquetes de Contexto de Traspaso (`literal_scenario_quote`), además de fragmentos, citas, notas y reformulaciones; la CoT de la IA y los textos de la plantilla sí se escanean. Así un compareciente que dice «falso» no bloquea la consolidación sin salida | NFR10.9; hallazgo R-01 de la revisión del Functional Design de U7; C8 `excluded_spans` |
| `contract-design/contract-summary.md` (C1 `ErrorCode`) | Añadir `report.storage_failed` (`500`): fallo de escritura, `fsync` o renombrado en el volumen, o destino ya existente; 0 filas y sin archivo final. Los *timeouts* de base y volumen responden `503` `system.unavailable` (precisión de U3). Junto con `report.not_consolidated` (X4 del Functional Design) entran en el mismo PR de U1 | NFR10.17, NFR11.4; §7 de functional-spec («code de sistema de la jerarquía de `libs/`») |
| `contract-design/contract-summary.md` (C1 `/reports/{id}/download`) | Declarar `x-veridicus-roles: [analista]` (X5), las cabeceras de NFR10.4 y las respuestas `403`, `409` (`report.integrity_mismatch`, `report.not_consolidated`), `422` y `503`. Un `report_version_id` sin fila responde `409` `report.not_consolidated`, porque C1 no tiene un `code` de «no encontrado» y no se añade ninguno | NFR10.2, NFR10.4, NFR10.5 |
| `contract-design/contract-summary.md` (C1 rutas de U7) | `POST /finalize`, `POST /reports`, `POST /correction-rounds` y el descarte (X6) declaran `403` (`auth.forbidden`, `session.not_owner`, `auth.csrf`), `422` (`validation.invalid_request`) y `503` (`system.unavailable`); hoy solo listan `201`/`409` | NFR10.1, NFR10.3, NFR10.17 |
| `contract-design/contract-summary.md` (C15) | Añadir las métricas de NFR15.1 (`veridicus_report_consolidations_total`, `veridicus_report_consolidation_seconds`, `veridicus_report_downloads_total`, `veridicus_report_orphans_removed_total`, `veridicus_session_mttv_seconds`). Entran por un PR de U1, como las de U3, U4 y U5 | NFR15.1, NFR15.4 |
| Functional Design de U7 (F7, BR4.3) | El barrido al arrancar solo borra archivos temporales o finales sin fila cuya antigüedad (`st_mtime`) supera `VERIDICUS_REPORT_ORPHAN_MIN_AGE_SECONDS` (300 s, mayor que el tope de la consolidación de NFR10.17 más el periodo de gracia del pod), y la API de `session-api` corre **1 réplica** con estrategia `Recreate` (el PVC es `ReadWriteOnce`). Así un pod que arranca no borra el archivo de una consolidación en vuelo | NFR10.16, NFR8.6; hallazgo R-02 de la revisión del Functional Design de U7 |
| Infrastructure Design (U2) | PVC `veridicus-reports` `ReadWriteOnce` de 1 GiB en una `StorageClass` local, montado solo en el contenedor de la API, con `fsGroup` del proceso; su respaldo va junto con el de CloudNativePG y la restauración se valida con el comando de NFR10.20 | NFR8.5, NFR10.6, NFR10.20 |
