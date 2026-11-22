# Diseño de escalado — U10 anonymizer

**Revisión 2 (2026-11-22): segunda pasada por el cambio 01, la adenda 02 y el NFR Requirements revisión
2.** Sustituye a la revisión 1 del 2026-10-03. Sale el proxy con 0 réplicas por defecto y la carga de
`embed`; entra el tamaño de 250 000 caracteres (NFRD-U10-01).

**Insumos.** `nfr-requirements/scalability-requirements.md` (scalability-requirements: NFR8.2–NFR8.5),
`performance-requirements.md` (performance-requirements), `reliability-requirements.md`
(reliability-requirements), `security-requirements.md` (security-requirements),
`observability-requirements.md` (observability-requirements) y `tech-stack-decisions.md`
(tech-stack-decisions, D5) de esta unidad; F1 y F8 de `functional-design/functional-spec.md`
(functional-spec); C20, C21 y C25 de `inception/contract-design/contract-summary.md` (contract-summary);
NFR-U4-12 de U4.

## 1. Modelo de carga

- `semantic-agent` hace una corrida a la vez para todo el sistema (NFR-U4-12). En la primera rebanada
  solo el juez es externo (NFR-U11-01): pasa como mucho una llamada a la vez por el proxy.
- El techo real lo pone el proveedor: sus límites de tasa devuelven `429`, que U10 traduce a
  `ProviderError` sin reintentar.
- En la CLI, el módulo corre en el mismo proceso, una llamada a la vez salvo que U11 decida otra cosa.

## 2. Mamparo de concurrencia (NFR8.2)

- Un `anyio.Semaphore(VERIDICUS_ANONYMIZER_MAX_CONCURRENCY)` (por defecto 4, entre 1 y 4; fuera de rango
  impide arrancar) en un *middleware* que corre **antes** de leer el cuerpo.
- La petición que no consigue cupo al instante (`acquire_nowait`) responde `503`
  `analysis.anonymizer_unavailable`, sin leer el cuerpo, sin seudonimizar y con 0 peticiones al transporte
  (NFR-U10-08). No hay cola de espera: un cliente que no recibe cupo termina su corrida en error.
- El cupo se libera cuando termina la petición **y** el hilo del NER que usaba (`reliability-design.md` §2).
- **Prueba.** 5 peticiones a la vez con un `FakeTransport` que espera: 4 en curso, la quinta recibe `503`
  en < 50 ms, y `veridicus_anonymizer_inflight` nunca pasa de 4.

## 3. Sin estado y con réplicas (NFR8.4)

- Cada petición construye y suelta su propia `MaskTable`; no hay caché, sesión ni archivo compartido. La
  copia de perfiles, los datos y el NER son de solo lectura e iguales en cada réplica.
- **Prueba.** Dos peticiones concurrentes con transcripciones sintéticas distintas restauran cada
  respuesta solo con sus propias formas (E33).
- El MVP despliega **1 réplica** en una sola máquina (`team.md`). Escalar es subir réplicas por PR de U2,
  sin cambiar U10; el cupo de 4 vale por réplica.

## 4. Memoria (NFR8.3)

| Elemento | Estimación | Cómo se acota |
|---|---|---|
| NER cargado en CPU | ≤ 700 MiB | Un modelo, cargado una vez |
| Una petición de 250 000 caracteres | ≤ 150 MiB (cuerpo, copia normalizada, tabla, cuerpo nativo, respuesta) | Topes de C25 y liberación al terminar |
| 4 peticiones simultáneas | ≤ 600 MiB | Mamparo de §2 |
| Total | ≤ **1,5 GiB** de RSS | Medido con `psutil` en nivel 1 |

La medida queda en `out/anonymizer-perf.json` y U2 declara `requests`/`limits` a partir de ella. Tras 50
peticiones seguidas, el RSS no crece más del 10 % respecto de la décima.

## 5. CPU solamente (NFR8.5, NFR2.2)

El NER corre en CPU y las suites de niveles 0 y 1 corren con `CUDA_VISIBLE_DEVICES=""`. El lockfile usa el
índice de `torch` solo CPU, y una comprobación falla si aparece `nvidia-*` o `triton`.

## 6. Decisiones y alternativas

| # | Decisión | Alternativas descartadas | Consecuencias |
|---|---|---|---|
| DE1 | Mamparo de 4 con rechazo inmediato antes de leer el cuerpo | Cola de espera; sin límite | Memoria acotada y sin peticiones colgadas; a cambio, una ráfaga mayor falla en vez de esperar |
| DE2 | Proceso sin estado, 1 réplica en el MVP | Afinidad por sesión; varias réplicas desde el inicio | Escalar es un PR de U2; hoy no hay alta disponibilidad |
| DE3 | Un proceso de Uvicorn por pod | Varios *workers* por pod | Un solo NER en memoria por pod; para más capacidad, más réplicas |
