# Requisitos de escalado — U7 forensic-report

**Insumos.** Flujos F2, F3, F6 y F7 de `functional-design/functional-spec.md` (functional-spec); reglas
BR3.1, BR4.1–BR4.3 y BR6.5 de `functional-design/rules.md` (rules) y entidades de `entities.md`; NFR8 y
los supuestos de `inception/requirements-analysis/requirements.md` (requirements); C1 y C11 de
`inception/contract-design/contract-summary.md` (contract-summary); `nfr-requirements-questions.md`
(sin preguntas nuevas).

## 1. Carga esperada del MVP

| Dimensión | Valor | Origen |
|---|---|---|
| Analistas a la vez | 1 (uso real y sustentación); 3 sesiones concurrentes en la prueba de carga | Supuestos de requirements; NFR8 |
| Turnos por sesión | ≤ 15 esperados; las pruebas llegan a 100 | Golden Dataset; caso de `performance-requirements.md` §1 |
| Versiones por sesión | ≤ 3 esperadas (la inicial y una o dos correcciones); las pruebas llegan a 10 | Supuesto del MVP (igual que las rondas de U5) |
| Sesiones consolidadas en total | ≤ 100 en el MVP (incluidas las de prueba) | Supuesto del MVP (NFR8.5 de U5) |
| Tamaño de un reporte | ≈ 30–60 KB para un caso del Golden Dataset; ≈ 470 KB para el caso de 100 turnos; **≤ 2 MiB** como cota (turnos ≤ 2 000 caracteres, pasajes ≤ 1 000, notas y reformulaciones ≤ 2 000, NFR10.5 de U5) | Cálculo; medido en NFR8.5 |
| Volumen ocupado | Esperado ≤ 100 × 3 × 60 KB ≈ 18 MB; peor caso 100 × 3 × 2 MiB = 600 MiB | Cálculo |
| Filas de `ReportVersion` | ≤ 300 esperadas; ≤ 1 000 en las pruebas | Cálculo |

## 2. Requisitos

| ID | Requisito | Criterio medible |
|---|---|---|
| NFR8.2 | Tres consolidaciones de sesiones distintas a la vez no se estorban. | Prueba `perf` de nivel 1 con 3 hilos y una barrera, cada uno consolidando el caso de 100 turnos de **otra** sesión, 20 repeticiones: 3 respuestas `201` en cada repetición, p95 ≤ 2 000 ms y 0 `503`. El bloqueo es por ronda (por sesión), así que sesiones distintas nunca se esperan entre sí. |
| NFR8.3 | Las metas aguantan 10 veces el número de versiones. | Variante de NFR3.2 y NFR3.5 con 10 versiones previas en la sesión y 1 000 filas de `ReportVersion` en la tabla: consolidación p95 ≤ 1 500 ms y lista de versiones p95 ≤ 100 ms. |
| NFR8.4 | Las consultas de U7 usan índices. | Índices únicos `ReportVersion (session_id, version_number)`, `(round_id)` y `(storage_path)`, y la clave primaria `report_version_id`. Prueba de nivel 1 que consulta `pg_indexes` y que, con 1 000 filas, `EXPLAIN` de la lista de versiones y de la versión vigente no hace `Seq Scan` sobre `ReportVersion`. |
| NFR8.5 | El tamaño de los reportes y del volumen está medido y acotado. | Prueba de nivel 1 que renderiza el caso de 100 turnos y un caso de peor caso con todos los textos en su máximo (100 turnos de 2 000 caracteres, 100 sugerencias con notas y reformulaciones de 2 000, 100 paquetes con 3 pasajes de 1 000): registra `byte_size` y falla si el peor caso supera **2 MiB**. El PVC se pide de **1 GiB** (cubre el peor caso de §1 con margen); los archivos y filas son evidencia de auditoría (NFR11) y no se purgan en el MVP. |
| NFR8.6 | La API de `session-api` corre una sola réplica mientras el volumen sea `ReadWriteOnce`. | El chart declara `replicas: 1` y `strategy: Recreate` para el `Deployment` de la API (un pod nuevo no arranca mientras el viejo tiene el volumen); política estática de nivel 0 sobre el render de `helm template` que falla con `replicas > 1` o `RollingUpdate` mientras el PVC de reportes sea `ReadWriteOnce`. **Límite conocido:** la coordinación de la consolidación ya está en la base (bloqueo de la ronda e índices únicos, NFR10.13) y funcionaría con varias réplicas; lo que impide escalar es el volumen y el barrido (NFR10.16). |

## 3. Señal para escalar

No hay autoescalado. Las señales son: p95 de NFR3.2 por encima de 1 500 ms en la prueba `perf`, o el
volumen por encima del 80 % (alerta de NFR15.3). Las opciones, en este orden, son: ampliar el PVC por PR
(Infrastructure Design); revisar el render si el tamaño de los reportes crece; y, si alguna vez hace
falta más de una réplica de la API, pasar a un volumen `ReadWriteMany` o a un almacén de objetos dentro
del clúster y cambiar el barrido por uno con bloqueo consultivo de la base. Cada cambio entra por PR con
su medición y no cambia el contrato de C1.
