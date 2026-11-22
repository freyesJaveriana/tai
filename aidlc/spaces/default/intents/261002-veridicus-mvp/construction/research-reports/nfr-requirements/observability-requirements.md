# Requisitos de observabilidad — U12 research-reports

**Revisión 1 (2026-11-22): primera pasada.**
- **IDs.** Todo es **nuevo** y hereda el ID del NFR de Inception (NFR10, por los logs solo con IDs, y NFR15).
- **Alcance.** NFR15 (SHOULD) pide en Prometheus las métricas de los pods de IA, la latencia por análisis,
  los *tokens* por proveedor y la AIR. Ninguna es de U12, que no analiza. U12 se observa por sus logs y por
  la salud de `session-api` (C16). No añade métricas a C15.

**Insumos.** BR3.6, BR4.2 y BR4.3 de rules; F5 y F6 de functional-spec; NFR10 y NFR15 de requirements; C15 y
C16 de contract-summary; NFR15.1 de U1 (etiquetas cerradas de las métricas); Code Style de `team.md` (logs
sin datos sensibles, solo IDs).

## 1. Requisitos

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR10.17 | nuevo | Cada subida deja una línea de log estructurada (BR4.3). | Una línea JSON por `POST /research-reports`, con solo estos campos: `event` (`research_report.upload`), `user_id`, `outcome` (`accepted` o `rejected`), `http_status`, `code` (si se rechazó), `rule` del primer problema, `problem_count`, `research_report_id` (si se aceptó), `source_sha256` (salvo en `413`), `source_bytes` y `duration_ms`. Nivel `INFO` si se aceptó y `WARNING` si se rechazó. Ningún otro campo: la prueba compara el conjunto de claves | Nivel 1 |
| NFR10.18 | nuevo | El arranque deja constancia del catálogo de referencia (BR3.6). | El log de arranque de `session-api` lleva `catalog_sha256`, `price_table_version`, el número de perfiles y la versión vigente de C19. Si el arranque falla, el log nombra el archivo y la regla que falló, nunca su contenido | Nivel 0 |
| NFR10.19 | nuevo | Los logs de U12 no llevan contenido del archivo. | Lo comprueba la prueba del *canary* (NFR12.1 de `security-requirements.md`) sobre los logs de la aplicación y de Uvicorn. Además, una prueba de nivel 0 falla si un `logger` de U12 recibe como argumento el cuerpo, el documento JSON, el `filename` o el texto de una excepción del analizador o del validador | Nivel 0 y nivel 1 |
| NFR15.1 | nuevo | U12 no publica métricas nuevas. | C15 no cambia por U12, y el módulo ResearchReports no importa `prometheus_client`. Si más adelante se quiere un contador de subidas, entra como precisión a C15 con la etiqueta `outcome` de la lista cerrada de U1; nunca con valores del reporte | Nivel 0 (import-linter) |

## 2. Qué responde cada señal

| Pregunta | Dónde se mira |
|---|---|
| ¿Quién subió un reporte y cuándo? | La fila (`uploaded_by`, `uploaded_at`) y la línea de NFR10.17 |
| ¿Por qué se rechazó una subida? | `code`, `rule` y `problem_count` en la línea de NFR10.17, y el mismo SHA-256 que vio el investigador en M8 |
| ¿Con qué catálogo arrancó `session-api`? | `catalog_sha256` en el log de arranque (NFR10.18) |
| ¿Está disponible? | `/readyz` de `session-api` (C16) y la prueba de humo de U2 |

## 3. Retención y acceso a los logs

Los logs de U12 siguen la política de `session-api` que fija U2 (sin Loki en el MVP; los del contenedor se
leen con `kubectl logs` en la máquina del humano). Como solo llevan IDs, cifras y hashes, no tienen una
retención especial.
