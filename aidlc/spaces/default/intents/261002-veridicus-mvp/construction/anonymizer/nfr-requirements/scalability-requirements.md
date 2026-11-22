# Requisitos de escalabilidad — U10 anonymizer

**Revisión 2 (2026-11-22): segunda pasada por el cambio 01, la adenda 02 y el Functional Design
revisión 2.** Sustituye a la revisión 1 del 2026-10-03. Se conservan los IDs NFR8.2–NFR8.4, y lo nuevo
toma el número siguiente (NFR8.5).

**Insumos.**
- F1 y F8 de `functional-design/functional-spec.md` (functional-spec).
- BR6.5 de `functional-design/rules.md` (rules).
- NFR2 y NFR8 de `inception/requirements-analysis/requirements.md` (requirements).
- C20, C21 y C25 de `inception/contract-design/contract-summary.md` (contract-summary).

## 1. Carga esperada

- **Concurrencia.** `semantic-agent` atiende un turno a la vez para todo el sistema (decisión de NFR
  Requirements registrada en `project.md`). Por cada tramo, U11 hace las llamadas de juez, verificador
  y, si el perfil lo pide, verificador permutado. La prueba de NFR8 corre 3 sesiones concurrentes.
- **Tamaño.** El mayor cuerpo es la transcripción más larga del modo final: ~186 000 caracteres, el
  tamaño de la entrevista más larga del piloto.
- **En la CLI.** El módulo corre en el mismo proceso, una llamada a la vez salvo que la CLI decida
  otra cosa (U11).

## 2. Requisitos

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR8.2 | cambia | El proxy limita las peticiones simultáneas, y el exceso no envía nada (NFR-U10-08). | Como máximo **4** peticiones en curso: juez, verificador y verificador permutado de un tramo, más una de margen. Se configura con `VERIDICUS_ANONYMIZER_MAX_CONCURRENCY` (por defecto 4, entre 1 y 4; un valor fuera de rango impide arrancar). La quinta petición simultánea responde al instante `503` `analysis.anonymizer_unavailable`, sin leer el cuerpo entero, sin seudonimizar y con **0 peticiones** al transporte. Prueba con 5 peticiones a la vez y un `FakeTransport` que espera. | Nivel 0 |
| NFR8.3 | cambia | La memoria del proceso está acotada y se conoce. | Pico de RSS del proxy ≤ **1,5 GiB** con el NER cargado y 4 peticiones simultáneas de 186 000 caracteres. Se mide con `psutil` en la prueba de nivel 1 y queda en `out/anonymizer-perf.json`. Los `requests`/`limits` del pod los declara U2 a partir de esta cifra. La memoria de una petición se libera al terminar: tras 50 peticiones seguidas, el RSS no crece más del 10 % respecto de la décima. | Nivel 1 |
| NFR8.4 | cambia | El proxy no tiene estado y puede tener varias réplicas (BR6.5). | Cada petición construye y suelta su propia tabla. Una prueba concurrente con dos transcripciones sintéticas distintas restaura cada respuesta solo con sus propias formas. El MVP despliega **1 réplica** en una sola máquina (`team.md`); escalar es subir réplicas por PR de U2, sin cambiar U10. | Nivel 0 |
| NFR8.5 | nuevo | Todo funciona en CPU (NFR2). | El NER corre en CPU y las suites de niveles 0 y 1 de U10 no piden GPU: corren con `CUDA_VISIBLE_DEVICES=""`. | Nivel 0 y nivel 1 |

## 3. Límites conocidos

- **Una sola máquina.** Una sola réplica en Minikube; no hay alta disponibilidad (`team.md`,
  Deployment).
- **El techo real lo pone el proveedor comercial.** Sus límites de tasa devuelven `429`, que U10 traduce
  a `ProviderError` sin reintentar (NFR10.4). La prueba de NFR8 debe declarar el perfil y los límites de
  la cuenta de Anthropic que usó (P2 = A).
