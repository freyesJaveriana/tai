# Diseño de escalado — U7 forensic-report

**Insumos.** `nfr-requirements/performance-requirements.md` (performance-requirements),
`security-requirements.md` (security-requirements), `scalability-requirements.md`
(scalability-requirements), `reliability-requirements.md` (reliability-requirements),
`observability-requirements.md` (observability-requirements) y `tech-stack-decisions.md`
(tech-stack-decisions, D1–D12) de esta unidad; flujos F2, F3, F6 y F7 de
`functional-design/functional-spec.md` (functional-spec); C1 y C11 de
`inception/contract-design/contract-summary.md` (contract-summary); respuestas P1 = A y P2 = A de
`nfr-design-questions.md`; diseño de U5 (bloqueo por sesión) y de U2 (chart y políticas).

## 1. Modelo de capacidad

| Dimensión | Esperado | Probado | Cota de diseño |
|---|---|---|---|
| Analistas a la vez | 1 | 3 sesiones concurrentes | El bloqueo es por sesión: sesiones distintas no se esperan |
| Versiones por sesión | ≤ 3 | 10 | Índice `(session_id, version_number)` |
| Filas de `ReportVersion` | ≤ 300 | 1 000 | Índices únicos (§3) |
| Tamaño de un reporte | 30–60 KB | ≈ 470 KB y peor caso | ≤ 2 MiB (NFR8.5) |
| Volumen ocupado | ≈ 18 MB | — | PVC de 1 GiB; peor caso 600 MiB |

U7 corre dentro de la API de `session-api`; no tiene `Deployment` propio ni autoescalado.

## 2. Concurrencia entre sesiones (NFR8.2)

- El único punto de serialización es la fila de **cada** sesión (`bump`) y su ronda; dos sesiones nunca
  comparten bloqueo. El *executor* del almacén tiene 2 hilos y cada escritura dura ≤ 300 ms, así que
  3 consolidaciones simultáneas esperan como mucho una escritura ajena.
- Las conexiones de base salen del *pool* de la API de U3; cada consolidación usa una conexión durante
  ≤ 2 s.
- Verificación: prueba `perf` de nivel 1 con 3 hilos y barrera, cada uno en otra sesión, 20
  repeticiones: 3 `201` por repetición, p95 ≤ 2 000 ms, 0 `503`.

## 3. Datos e índices (NFR8.3, NFR8.4, NFR8.5)

- **Índices.** Clave primaria `report_version_id`; únicos `(session_id, version_number)`, `(round_id)` y
  `(storage_path)`. La lista de versiones y la versión vigente (`ORDER BY version_number DESC LIMIT 1`)
  usan el primero. Prueba de nivel 1 sobre `pg_indexes` y `EXPLAIN` con 1 000 filas: sin `Seq Scan`
  sobre `report_version`.
- **Diez veces más versiones (NFR8.3).** Variante de NFR3.2 y NFR3.5 con 10 versiones previas y 1 000
  filas: consolidación p95 ≤ 1 500 ms; lista p95 ≤ 100 ms. El costo de consolidar depende del tamaño de
  la ronda, no del número de versiones (el render solo nombra la versión que reemplaza).
- **Tamaño acotado (NFR8.5).** Prueba de nivel 1 que renderiza el caso de 100 turnos y el peor caso con
  todos los textos en su máximo (topes de `contracts/limits.v1.yaml`): registra `byte_size` y falla por
  encima de 2 MiB. Sin purga: archivos y filas son evidencia de auditoría.

## 4. Una réplica mientras el volumen sea `ReadWriteOnce` (NFR8.6)

- El chart de U2 declara `replicas: 1` y `strategy: Recreate` en el `Deployment` de la API; una política
  Kyverno de nivel 0 sobre `helm template` falla con `replicas > 1` o `RollingUpdate` mientras el PVC
  `veridicus-reports` sea `ReadWriteOnce` (control negativo con un render que lo viola).
- La coordinación de la consolidación ya vive en la base (bloqueos e índices únicos) y la limpieza de
  P2 = A es local a cada proceso, así que con varias réplicas solo habría que cambiar el volumen y el
  barrido del arranque.

## 5. Señales para escalar

| Señal | Umbral | Acción (por PR, con su medición) |
|---|---|---|
| Uso del volumen | > 80 % durante 10 min (NFR15.3) | Ampliar el PVC (Infrastructure Design) |
| Latencia de consolidación | p95 > 1 500 ms en la prueba `perf` o en `veridicus_report_consolidation_seconds` | Revisar render y escaneo; medir por tramo (performance-design §1) |
| Necesidad de más réplicas | Más de un analista simultáneo sostenido | Volumen `ReadWriteMany` o almacén de objetos en el clúster y barrido con bloqueo consultivo de la base; no cambia C1 |
