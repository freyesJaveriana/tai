# Requisitos de escalado — U7 forensic-report (módulo ReviewReport)

**Revisión 2 (2026-11-22), segunda pasada por el cambio 01, la adenda 02 y el Functional Design de U7,
revisión 2.** Sustituye a la revisión 1 del 2026-10-03.
- **IDs.** Los requisitos conservan su ID y cada fila dice si **se mantiene**, **cambia** o es **nuevo**.
  Entra NFR8.10 (exportaciones). Ninguno se retira.
- **Qué cambia.** La cota del reporte pasa de 2 MiB a `report_max_bytes` = 8 MiB (NFR-U7-01), el PVC es
  de 2 GiB con cuota propia (Infrastructure Design de U7) y la retención de U13 ya purga (VE-12), así que
  los reportes dejan de crecer sin límite.

**Insumos.**
- Flujos F2, F3, F6, F8 y F10 de `functional-design/functional-spec.md` (functional-spec, revisión 2).
- Reglas BR3.1, BR4.1–BR4.3, BR6.5, BR9.5 y BR10.1 de `functional-design/rules.md` (rules) y entidades
  de `entities.md` (ReportVersion, ReportExport).
- NFR8 y los supuestos de `inception/requirements-analysis/requirements.md` (requirements, revisión 3),
  con VE-12 de la adenda 02.
- C1, C11, C24 y C25 de `inception/contract-design/contract-summary.md` (contract-summary).
- `nfr-requirements-questions.md`, segunda pasada, sin preguntas.

## 1. Carga esperada del MVP

| Dimensión | Valor | Origen |
|---|---|---|
| Analistas a la vez | 1 (uso real y sustentación); 3 sesiones concurrentes en la prueba de carga | Supuestos de requirements; NFR8 |
| Turnos por sesión | ≤ 60 esperados; las pruebas llegan a 2 000 (`transcript_max_turns`) | Conjunto sintético; C25 de U4 |
| Versiones por sesión | ≤ 3 esperadas; las pruebas llegan a 10 | Supuesto del MVP |
| Exportaciones por sesión | ≤ 10 esperadas; las pruebas llegan a 100 | Supuesto del MVP; NFR3.14 |
| Sesiones con reporte | ≤ 100 a la vez en el MVP, con la retención de 90 días de U13 | Supuesto del MVP; VE-12 |
| Tamaño de un reporte | ≈ 30–60 KB para un caso del conjunto sintético; ≈ 400 KB para el caso de 100 turnos; **≤ 8 MiB** como cota (`report_max_bytes`) | `performance-requirements.md` §1; NFR8.5 |
| Volumen ocupado | Esperado ≤ 100 × 3 × 60 KB ≈ 18 MB. Cuota de 2 GiB = 256 reportes del caso máximo | Cálculo; Infrastructure Design de U7 |
| Filas | ≤ 300 `ReportVersion` y ≤ 1 000 `ReportExport` esperadas; las pruebas llegan a 1 000 y 10 000 | Cálculo |

## 2. Requisitos

| ID | Estado | Requisito | Criterio medible |
|---|---|---|---|
| NFR8.2 | se mantiene | Tres consolidaciones de sesiones distintas a la vez no se estorban. | `perf` de nivel 1 con 3 hilos y una barrera, cada uno consolidando el caso de 100 turnos de **otra** sesión, 20 repeticiones: 3 `201` por repetición, p95 ≤ 2 000 ms y 0 `503`. El bloqueo es por sesión y ronda, así que sesiones distintas nunca se esperan. |
| NFR8.3 | cambia | Las metas aguantan 10 veces las versiones y las exportaciones. | Variante de NFR3.2, NFR3.5 y NFR3.12 con 10 versiones previas, 100 exportaciones en la sesión, 1 000 filas de `ReportVersion` y 10 000 de `ReportExport`: consolidación p95 ≤ 1 500 ms, lista p95 ≤ 100 ms y exportación p95 ≤ 500 ms. |
| NFR8.4 | cambia | Las consultas de U7 usan índices. | Índices únicos `ReportVersion (session_id, version_number)`, `(round_id)` y `(storage_path)`; `ReportExport (report_version_id)` para la purga y la consulta de U13. Nivel 1 que consulta `pg_indexes` y que, con las filas de NFR8.3, `EXPLAIN` de la lista, de la versión vigente y de la selección de la purga no hace `Seq Scan` sobre las dos tablas. |
| NFR8.5 | cambia | El tamaño de los reportes y del volumen está medido y acotado. | Nivel 1 que renderiza el caso de 100 turnos y el caso máximo (`performance-requirements.md` §1.2): registra `byte_size` y falla si el caso máximo supera `report_max_bytes` = **8 MiB**, o si los puntos de página suman ≥ 2 % de sus bytes. El PVC es de **2 GiB** con la cuota `VERIDICUS_REPORT_VOLUME_QUOTA_BYTES` (Infrastructure Design). El peor caso teórico de 100 sesiones × 3 versiones del caso máximo (2,4 GiB) **no** cabe: es un riesgo aceptado porque el esperado es 18 MB, la regla de NFR15.3 lo muestra al 80 % y una consolidación que no cabe falla con `500 system.internal` y 0 filas (NFR10.15). La retención de U13 libera el espacio de las sesiones vencidas (NFR11.8). |
| NFR8.6 | cambia | La API de `session-api` corre una sola réplica mientras el volumen sea `ReadWriteOnce`. | El chart `deploy/veridicus` declara `replicas: 1` y `strategy: Recreate` para el `Deployment` de la API; política estática de nivel 0 sobre el render que falla con `replicas > 1` o `RollingUpdate` mientras el PVC de reportes sea `ReadWriteOnce`. **Límite conocido:** la coordinación de la consolidación está en la base (bloqueos e índices únicos) y funcionaría con varias réplicas; lo que impide escalar es el volumen y el barrido (NFR10.16). El `Job` de retención no se lanza mientras otra purga corre (U13) y comparte el nodo único de Minikube. |
| NFR8.10 | nuevo | Las exportaciones no ocupan el volumen. | La exportación solo añade una fila de `ReportExport` (≈ 200 B); tras 100 exportaciones el uso del volumen no cambia (NFR10.25). |

## 3. Señal para escalar

No hay autoescalado. Las señales son: p95 de NFR3.2 sobre 1 500 ms o de NFR3.13 sobre 6 s en la prueba
`perf`, o el volumen sobre el 80 % de la cuota (NFR15.3). Las opciones, en este orden: acortar la retención
por PR (U13); ampliar el PVC y la cuota por PR (Infrastructure Design); revisar el render si los reportes
crecen; y, si alguna vez hace falta más de una réplica de la API, pasar a un volumen `ReadWriteMany` o a
un almacén de objetos dentro del clúster con el barrido bajo un bloqueo asesor de la base. Cada cambio
entra por PR con su medición y no cambia C1.
