# Requisitos de rendimiento — U10 anonymizer

**Insumos.** Flujos F1–F3 y la máquina de estados de una llamada de `functional-design/functional-spec.md`
(functional-spec); reglas BR1.1–BR1.4 y BR2.1 de `functional-design/rules.md` (rules); FR11.3, NFR3,
NFR8 y NFR9 de `inception/requirements-analysis/requirements.md` (requirements); C13 y C14 de
`inception/contract-design/contract-summary.md` (contract-summary); respuesta P1 = A de
`nfr-requirements-questions.md`; las metas de U4 (`../../text-flow/nfr-requirements/performance-requirements.md`).

**El proxy se entrega apagado (P1 = A).** Con el valor por defecto no se despliega y no afecta ninguna
latencia del MVP: el juez y los *embeddings* son los internos de U2 y U4. Las metas de este documento
se verifican en nivel 0 y nivel 1 siempre que exista el código, y las de §2 solo en el PR que lo
habilite. Todo se mide en la **máquina de desarrollo con el perfil CPU** (NFR2); ninguna meta depende
de la GPU. Una prueba de rendimiento inestable se arregla o se pone en cuarentena con un *issue*, nunca
se reintenta ni se baja su umbral (team-practices).

## 1. Costo del enmascarado

El enmascarado es código puro (expresiones regulares de tiempo lineal y lista de nombres propios,
`tech-stack-decisions.md` D2). Su costo se mide en proceso, sin red, con un destino *fake*.

| ID | Qué se mide | Objetivo | Carga | Cómo se mide |
|---|---|---|---|---|
| NFR3.1 | Enmascarar un texto (detección + reemplazo + tabla en memoria, BR1.1, BR1.2) | **p95 ≤ 50 ms por cada 10 000 caracteres**; crecimiento lineal: el p95 con 100 000 caracteres ≤ 10 veces el de 10 000 + 20 ms | Textos sintéticos de 10 000 y 100 000 caracteres con 1 mención cada 200 caracteres (nombres, lugares y expedientes del catálogo de U1); lista de **2 000** nombres propios (tope de NFR10.8); 200 repeticiones | Prueba `perf` de nivel 1 en proceso con `time.perf_counter`; el reporte registra p50, p95 y máximo |
| NFR3.2 | Restaurar una respuesta (BR1.3) | p95 ≤ 10 ms por cada 10 000 caracteres | Respuesta de 10 000 caracteres con 100 marcadores conocidos y 5 desconocidos | Ídem |
| NFR3.3 | Sobrecosto del proxy en una llamada `judge` (todo menos la espera al destino) | **p95 ≤ 250 ms** por llamada | Bloque de datos de 24 000 caracteres (≈ el tope de 6 000 *tokens* de U4, NFR3.11 de U4) + instrucciones de 4 000 caracteres + respuesta de 16 000 caracteres; lista de 2 000 nombres; destino *fake* que responde en 0 ms | Prueba `perf` de nivel 1 con el servicio HTTP real en proceso y `httpx.MockTransport` como destino |
| NFR3.4 | Tiempo máximo del enmascarado antes de fallar cerrado | Si enmascarar una llamada pasa de **2 s** (`VERIDICUS_ANONYMIZER_MASKING_TIMEOUT_SECONDS`), no se envía nada y la llamada termina en `failed_closed` (BR2.1) | Detector *fake* que tarda 3 s | Prueba de nivel 0; ver NFR10.1 en `reliability-requirements.md` |

**Efecto en la latencia de U4.** Con NFR3.3, el proxy añade como máximo 0,25 s a un turno: **≤ 0,5 %
del p95 de 60 s** de NFR3.1 de U4. El presupuesto que manda en un juez externo es la espera al destino,
que no controla Veridicus; por eso §2 exige medir el turno completo con el proxy antes de habilitarlo.

## 2. Metas que se miden al habilitar el proxy

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR3.5 | Con el proxy en el camino, el turno de texto sigue cumpliendo la meta de U4. | El reporte de nivel 2 del PR que habilita el proxy (corrido con `--profile cpu --model-gateway anonymizer`) da **p95 ≤ 60 s** para `evaluated_at − submitted_at` (NFR3.1 de U4) y la prueba de humo pasa en ≤ 120 s por caso (NFR3.10 de U4). Si no se cumple, el proxy no se habilita; la meta no se sube. | Nivel 2 y nivel 3, en el PR de habilitación |
| NFR9.1 | La indexación con *embeddings* externos cabe en la meta de 3 minutos. | Enmascarar los pasajes de un documento de 1 048 576 bytes (≈ 1 100 pasajes, en lotes de 32) cuesta **≤ 6 s** en total (NFR3.1 aplicado a 1 MB); el tiempo total desde el 202 hasta `ready_at` con el proxy sigue en **< 180 s** (NFR9.1 de U4). | Nivel 1 (costo del enmascarado) y nivel 2 en el PR de habilitación (tiempo total) |

## 3. Recursos

| ID | Pod | Tope medido | Cómo se mide |
|---|---|---|---|
| NFR8.1 | `anonymizer-proxy` | Pico de RSS **≤ 256 MiB** con 4 llamadas simultáneas (NFR8.2) de 24 000 caracteres y listas de 2 000 nombres | Prueba `perf` de nivel 1 que mide el RSS del proceso; Infrastructure Design fija `limits.memory` con al menos un 20 % sobre el pico, y CPU `requests` de 100m y `limits` de 1 núcleo |

Si un pico supera su tope, es un hallazgo que se corrige por PR; el tope no se sube en silencio.
