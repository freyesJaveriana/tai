# Diseño de escalabilidad — U12 research-reports

**Revisión 1 (2026-11-22): primera pasada.** Todo es nuevo.

**Insumos.** `nfr-requirements/scalability-requirements.md` (scalability-requirements: §1, NFR3.9–NFR3.11 y
§3) y `performance-requirements.md` (performance-requirements, NFR3.8) de esta unidad; BR2.2, BR2.3 y BR6.5
de `functional-design/functional-spec.md` (functional-spec); C1 y C25 de
`inception/contract-design/contract-summary.md` (contract-summary); pool de la API de U3 y separación de
procesos de U4.

## 1. Forma del despliegue

- U12 no tiene proceso propio: vive en la API de `session-api`, con **1 réplica** en el MVP (una sola
  máquina y un solo investigador, supuesto de requirements §5). No hay autoescalado.
- La API no guarda estado entre peticiones: el `ReferenceCatalog` es inmutable y se carga al arrancar, y los
  huecos de subida son locales al proceso. Con más réplicas, cada una tendría sus 2 huecos y el mismo
  catálogo (el despliegue es uno solo); la unicidad de `source_sha256` sigue en la base.

## 2. Topes que acotan el trabajo

| Cifra | Valor | De dónde | Qué acota |
|---|---|---|---|
| `research_report_max_bytes` | 8 388 608 | C25 (NFR-U12-01) | Bytes por subida y memoria por hueco |
| `research_report_max_json_depth` | 8 | C25 (NFR-U12-01) | Profundidad del análisis |
| `research_report_write_timeout_s` | 15 | C25 (NFR-U12-01) | Duración de T3 |
| `research_report_read_timeout_s` | 30 | C25 (NFRD-U12-02) | Tiempo que un cliente puede ocupar un hueco leyendo |
| Huecos de subida | 2 | Constante `UPLOAD_SLOTS` de `research_reports/application/` | Subidas simultáneas por proceso |
| Espera de un hueco | 5 s | Constante `UPLOAD_SLOT_WAIT_S` | Cola de subidas |

Las cifras de C25 se leen con `limits.load` y el entorno solo puede bajarlas (NFRD-U1-09). Los huecos no son
una cifra de C25: salen de lo que NFR3.8 mide (dos subidas máximas), y cambiarlos exige volver a medir NFR3.8 en
el mismo PR.

## 3. *Bulkhead* de subidas (NFR3.10)

- Un `anyio.Semaphore(2)` por proceso, tomado **después** de T1, del tipo y del tope previo, y **antes** de
  leer el cuerpo. Si no hay hueco en 5 s, `503` `system.unavailable` con `cause: upload_slots` y
  `Retry-After: 10` (NFRD-U12-04): ni lee, ni escribe, ni ocupa una conexión.
- El hueco se suelta en un `finally` en todos los caminos: `201`, rechazo, plazo vencido y corte del cliente.
- Pruebas de nivel 1: dos subidas máximas distintas a la vez terminan en `201` dentro de 2 × el p95 de NFR3.2
  y dentro de NFR3.8; una tercera con las dos ocupadas recibe `503` en ≤ 5,5 s y 0 bytes leídos; dos subidas
  del mismo archivo dejan exactamente 1 fila (E8, NFR11.6).

## 4. Volumen de la lista (NFR3.9)

- C1 no pagina `GET /research-reports`. La consulta lee solo las columnas de `ResearchReportSummary` por el
  índice `(uploaded_at DESC)` (`performance-design.md` §3), y la consola virtualiza desde 200 filas.
- **Disparador.** La revisión de B12 incluye una consulta de conteo. Si se acerca a 1 000, la paginación
  entra por PR de U1 sobre C1 antes del reporte 1 001. Mientras tanto la lista sigue completa: nunca se
  trunca en silencio.

## 5. Almacenamiento (NFR3.11)

- Solo filas tipadas y estrechas (`security-design.md` §7); el JSON no se guarda.
- La prueba de nivel 1 mide `pg_total_relation_size` de las cuatro tablas antes y después de subir cada
  *fixture*: ≤ 1,5 × `source_bytes` por reporte, y el *fixture* del peor caso estimado ≤ 4 MiB en el
  archivo (comprueba la estimación de scalability-requirements §1).
- Con 1 000 reportes típicos, ≤ 1,5 GiB. Infrastructure Design lo suma al volumen de PostgreSQL
  (`logical-components.md` §5).

## 6. Conexiones

U12 no abre conexiones nuevas: usa el pool de la API de U3 (5 + 5). Cada subida toma una conexión en T1, T2
y T3, por milisegundos salvo T3 (≤ 15 s). Con 2 huecos, U12 retiene como mucho 2 conexiones a la vez y solo
en T3.

## 7. Qué se degrada primero

| Señal | Qué pasa | Qué se hace |
|---|---|---|
| Tercera subida simultánea | `503` con `Retry-After` | El investigador reintenta; si fuera habitual, se mide de nuevo NFR3.8 antes de subir `UPLOAD_SLOTS` por PR |
| Más de 1 000 reportes | La lista pasa de NFR3.4 | Paginación por PR de U1 (§4) |
| Reporte legítimo de más de 8 MiB | `413` | Se sube la cifra por PR de U1 tras medir NFR3.8 |
| Memoria de la API cerca de su límite | Riesgo de `OOMKilled` para todas las unidades de `session-api` | Hallazgo que se corrige por PR (lotes al armar filas, plan B de `performance-design.md` §2); nunca se sube el límite en silencio |
