# Diseño de rendimiento — U10 anonymizer

**Insumos.** `nfr-requirements/performance-requirements.md` (performance-requirements),
`nfr-requirements/security-requirements.md` (security-requirements),
`nfr-requirements/scalability-requirements.md` (scalability-requirements),
`nfr-requirements/reliability-requirements.md` (reliability-requirements),
`nfr-requirements/observability-requirements.md` (observability-requirements) y
`nfr-requirements/tech-stack-decisions.md` (tech-stack-decisions, D2, D5, D6) de esta unidad; flujos
F1 y F2 de `functional-design/functional-spec.md` (functional-spec); C13 y C14 de
`inception/contract-design/contract-summary.md` (contract-summary); respuestas P1 = A y P2 = A de
`nfr-design-questions.md`; metas de U4 (p95 de 60 s por turno, indexación en menos de 180 s).

Todo se mide en la máquina de desarrollo con el perfil CPU; ninguna meta depende de la GPU. Una
prueba de rendimiento inestable se arregla o va a cuarentena con un *issue*; nunca se baja su umbral.

## 1. Presupuesto de una llamada `judge` (NFR3.3, NFR3.4)

| Tramo | Diseño | Presupuesto p95 (24 000 + 4 000 caracteres de entrada, 16 000 de respuesta, 2 000 nombres) |
|---|---|---|
| Validación de esquema y límites | Pydantic v2 sobre el cuerpo ya leído | 10 ms |
| Compilar la lista de nombres de la llamada | Alternación escapada en `google-re2`, ordenada de mayor a menor longitud | 60 ms |
| Decodificar y enmascarar (P2 = A) | Recorrido de cadenas hoja y búsqueda sobre la copia normalizada | 80 ms |
| Serializar y comprobación final | `json.dumps(ensure_ascii=False)` y segunda búsqueda con la misma lista compilada | 50 ms |
| Restaurar | Un solo patrón `re2` de marcadores y diccionario | 20 ms |
| Holgura | — | 30 ms |
| **Total, sin la espera al destino** | — | **≤ 250 ms** (NFR3.3) |

- Las reglas de `DetectionRuleSet` se compilan **una vez** al arrancar; la lista de nombres se compila
  **por llamada**, porque el proxy no guarda estado entre llamadas (NFR8.3) y no conserva nombres
  propios en memoria más allá de la llamada. Si la compilación por llamada rompe el presupuesto, es un
  hallazgo que se corrige por PR (por ejemplo, con un autómata de cadenas); no se introduce una caché
  de listas.
- La comprobación final (P2 = A) reutiliza la lista ya compilada: su costo es una búsqueda lineal más
  sobre el cuerpo, dentro del presupuesto.
- `NumberingPlan` (P1 = A) es un diccionario de valor normalizado a número, construido al compilar la
  lista; asignar un marcador es O(1).
- Si el enmascarado pasa de 2 s (`fail_after`), la llamada termina cerrada (NFR3.4); prueba de nivel 0
  con un detector *fake* de 3 s.

## 2. Costo lineal y protección de CPU (NFR3.1, NFR3.2)

- `google-re2` garantiza tiempo lineal en el largo del texto; no hay retroceso catastrófico (T12). La
  normalización (minúsculas, sin tildes, espacios y saltos de línea colapsados) también es lineal y
  produce un mapa de posiciones al original en un arreglo de enteros.
- El trabajo de CPU corre en un hilo (`anyio.to_thread.run_sync`) para no bloquear el bucle de
  Uvicorn mientras otras llamadas esperan al destino; el semáforo de 4 llamadas (NFR8.2) limita los
  hilos simultáneos.

| ID | Prueba `-m perf` (nivel 1, en proceso, `time.perf_counter`, 200 repeticiones) | Umbral |
|---|---|---|
| NFR3.1 | Enmascarar 10 000 y 100 000 caracteres con 1 mención cada 200 y lista de 2 000 nombres | p95 ≤ 50 ms por 10 000; p95(100 000) ≤ 10 × p95(10 000) + 20 ms |
| NFR3.2 | Restaurar 10 000 caracteres con 100 marcadores conocidos y 5 desconocidos | p95 ≤ 10 ms |
| NFR3.3 | Llamada `judge` completa con el servicio HTTP en proceso y destino `httpx.MockTransport` de 0 ms | p95 ≤ 250 ms |

El reporte de la prueba registra p50, p95 y máximo, y el tramo de la comprobación final por separado.

## 3. Lotes de *embeddings* (NFR9.1)

- `embed` admite hasta 32 textos por llamada (catálogo de límites de U1). El indexador de U4 ya envía
  lotes de 32; con P1 = A cada lote de la misma versión de escenario usa la misma numeración, sin costo
  adicional.
- Meta: enmascarar los ≈ 1 100 pasajes de un documento de 1 048 576 bytes cuesta ≤ 6 s en total
  (prueba `-m perf` que suma los 35 lotes); el tiempo de 202 a `ready_at` con el proxy sigue en
  < 180 s en el nivel 2 del PR de habilitación.

## 4. Metas que se miden al habilitar (NFR3.5)

El PR que habilita el proxy adjunta
`uv run --directory evaluation python -m golden.run --profile cpu --model-gateway anonymizer --report out/level2-anonymizer.json`:
p95 de `evaluated_at − submitted_at` ≤ 60 s y prueba de humo ≤ 120 s por caso. Si no se cumple, el
proxy no se habilita; la meta de U4 no se sube.

## 5. Recursos del pod (NFR8.1)

| Recurso | Diseño | Verificación |
|---|---|---|
| Memoria | 1 proceso Uvicorn; como máximo 4 llamadas con cuerpos de 512 KiB, sus copias normalizadas, la serialización y la respuesta de 2 MiB; ninguna caché | Prueba `-m perf` que mide el pico de RSS con 4 llamadas de 24 000 caracteres y 2 000 nombres: ≤ 256 MiB |
| CPU | `requests` 100m, `limits` 1 núcleo | Entregado a Infrastructure Design (`logical-components.md` §4) |
| `limits.memory` | Pico medido + ≥ 20 % (≈ 320 MiB si el pico es 256 MiB) | Infrastructure Design |
| GPU | Ninguna en ningún perfil (NFR2.2) | Prueba de nivel 0 sobre el render |

Un pico por encima del tope es un hallazgo que se corrige por PR; el tope no se sube en silencio.
