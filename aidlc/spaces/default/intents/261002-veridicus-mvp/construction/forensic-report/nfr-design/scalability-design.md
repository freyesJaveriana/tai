# Diseño de escalado — U7 forensic-report (módulo ReviewReport)

**Revisión 2 (2026-11-22): segunda pasada por el cambio 01, la adenda 02 y el NFR Requirements de U7,
revisión 2.** Sustituye a la revisión 1 del 2026-10-03.
- **Qué cambia.**
  - La cota del reporte pasa de 2 MiB a `report_max_bytes` = 8 MiB.
  - El PVC pasa de 1 GiB a 2 GiB, con cuota propia.
  - Entran `ReportExport`, con su índice, y la purga de U13: los reportes dejan de crecer sin límite.
  - Las señales usan los *gauges* de la cuota y no `kubelet_volume_stats`.
- **Numeración.** §1–§5 conservan su número. Entra §6 (exportaciones).

**Insumos.**
- De esta unidad, en `nfr-requirements/`: `scalability-requirements.md` (scalability-requirements:
  NFR8.2–NFR8.6, NFR8.10), `performance-requirements.md` (performance-requirements), `security-requirements.md`
  (security-requirements), `reliability-requirements.md` (reliability-requirements),
  `observability-requirements.md` (observability-requirements) y `tech-stack-decisions.md`
  (tech-stack-decisions, D5, D8, D14, D15).
- F2, F3, F6, F8 y F10 de `functional-design/functional-spec.md` (functional-spec).
- C1, C11, C24 y C25 de `inception/contract-design/contract-summary.md` (contract-summary).
- De otras unidades: el diseño de U5 (bloqueo por sesión) y el de U2 (chart y políticas).

## 1. Modelo de capacidad

| Dimensión | Esperado | Probado | Cota de diseño |
|---|---|---|---|
| Analistas a la vez | 1 | 3 sesiones concurrentes | El bloqueo es por sesión: sesiones distintas no se esperan |
| Versiones por sesión | ≤ 3 | 10 | Índice `(session_id, version_number)` |
| Exportaciones por sesión | ≤ 10 | 100 | Índice `(report_version_id)` de `report_export` |
| Filas | ≤ 300 `ReportVersion` y ≤ 1 000 `ReportExport` | 1 000 y 10 000 | Índices de §3 |
| Tamaño de un reporte | 30–60 KB; ≈ 400 KB con 100 turnos | Caso máximo medido | ≤ 8 MiB (NFR8.5) |
| Volumen ocupado | ≈ 18 MB | — | Cuota de 2 GiB = 256 reportes del caso máximo |

U7 corre dentro de la API de `session-api`: no tiene `Deployment` propio ni autoescalado.

## 2. Concurrencia entre sesiones (NFR8.2)

- El único punto de serialización es la fila de **cada** sesión (el `bump`) y su ronda; dos sesiones nunca
  comparten un bloqueo. La exportación no toma la sesión (DS5), así que tampoco compite con las
  consolidaciones de otras sesiones.
- El *executor* del almacén tiene 2 hilos y cada escritura de 100 turnos dura ≤ 300 ms. Así, 3
  consolidaciones simultáneas esperan como mucho una escritura ajena.
- Las conexiones salen del *pool* de la API de U3. Cada consolidación usa una conexión ≤ 2 s en el caso
  normal y ≤ 8 s en el máximo.
- Verificación: prueba `perf` de nivel 1 con 3 hilos y una barrera, cada uno en otra sesión, 20
  repeticiones. Resultado esperado: 3 `201` por repetición, p95 ≤ 2 000 ms y 0 `503`.

## 3. Datos e índices (NFR8.3, NFR8.4, NFR8.5)

- **Índices.**
  - `report_version`: clave primaria `report_version_id`; únicos `(session_id, version_number)`, `(round_id)`
    y `(storage_path)`.
  - `report_export`: clave primaria `export_id` e índice `(report_version_id)`, que usan la purga y U13.

  La lista, la versión vigente (`ORDER BY version_number DESC LIMIT 1`) y la selección de la purga usan el
  primer índice único. Prueba de nivel 1 sobre `pg_indexes`, y `EXPLAIN` con las filas de NFR8.3: sin
  `Seq Scan` sobre las dos tablas.
- **Diez veces más (NFR8.3).** Variante de NFR3.2, NFR3.5 y NFR3.12 con 10 versiones previas, 100
  exportaciones en la sesión, 1 000 filas de `ReportVersion` y 10 000 de `ReportExport`. Metas p95:
  consolidación ≤ 1 500 ms, lista ≤ 100 ms y exportación ≤ 500 ms. Consolidar depende del tamaño de la ronda,
  no del número de versiones.
- **Tamaño acotado (NFR8.5).** Prueba de nivel 1 que renderiza el caso de 100 turnos y el caso máximo.
  Registra `byte_size` y falla en dos casos: si el máximo supera 8 MiB, o si los puntos de página suman
  ≥ 2 % de los bytes.
- **Riesgo aceptado.** El peor caso teórico es de 2,4 GiB (100 sesiones × 3 versiones máximas) y no cabe
  en la cuota de 2 GiB. Una consolidación que no cabe falla con `500 system.internal` y 0 filas (NFR10.15),
  y la regla del 80 % lo avisa antes. La retención de U13 libera el espacio de las sesiones vencidas.

## 4. Una réplica mientras el volumen sea `ReadWriteOnce` (NFR8.6)

- El chart declara `replicas: 1` y `strategy: Recreate` en el `Deployment` de la API. Una política Kyverno
  de nivel 0 sobre `helm template` falla con `replicas > 1` o `RollingUpdate` mientras el PVC
  `veridicus-reports` sea `ReadWriteOnce`, con un control negativo.
- La coordinación ya vive en la base: bloqueos de la sesión y de la versión, índices únicos y la fila que
  consulta el barrido. La cancelación cooperativa es local al proceso. Con varias réplicas solo cambiarían
  el volumen y el candado del barrido, que pasaría a un bloqueo asesor de la base.
- El `Job` de retención comparte el nodo único de Minikube. Monta el mismo PVC en escritura con el mismo
  UID; U13 nunca lanza dos purgas a la vez.

## 5. Señales para escalar

| Señal | Umbral | Acción (por PR, con su medición) |
|---|---|---|
| Uso del volumen | `veridicus_report_volume_used_bytes / veridicus_report_volume_quota_bytes > 0.8` durante 10 min (NFR15.3) | Acortar la retención (U13) o ampliar el PVC y la cuota (Infrastructure Design) |
| Latencia de la consolidación | p95 > 1 500 ms (caso normal) o > 6 s (máximo) | Revisar el render y el escaneo; medir por tramo (`performance-design.md` §1) |
| Latencia de la exportación | p95 > 500 ms con 100 turnos | Revisar la inserción de la marca y la lectura |
| Más réplicas | Más de un analista simultáneo sostenido | Volumen `ReadWriteMany` o almacén de objetos en el clúster, y barrido con bloqueo asesor. No cambia C1 |

## 6. Exportaciones (NFR8.10)

- Una exportación solo añade una fila de `report_export` (≈ 200 B). Los bytes nunca tocan el volumen
  (`security-design.md` §10).
- Verificación de nivel 1: tras 100 exportaciones, `veridicus_report_volume_used_bytes` y el listado de
  `reports/` no cambian.
