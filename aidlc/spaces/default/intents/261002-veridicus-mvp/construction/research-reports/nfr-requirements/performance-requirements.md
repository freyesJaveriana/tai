# Requisitos de rendimiento — U12 research-reports

**Revisión 1 (2026-11-22): primera pasada.**
- **IDs.** Todo es **nuevo** y hereda el ID del NFR de Inception (NFR2 y NFR3).
- **Qué mide.** U12 no llama a modelos. Su trabajo es síncrono y acotado: validar, contrastar y escribir una
  subida, y leer la lista, el detalle y la comparación. NFR3 («interfaz no bloqueante») se cumple aquí con
  respuestas rápidas y con un diálogo de subida que no congela el resto de la consola.

**Insumos.** F1–F4, BR2.1–BR2.8 y BR6.5 de functional-spec y rules; NFR2 y NFR3 de requirements; C1 y C19
de contract-summary; NFR3.2 y NFR3.3 de U4 (orden de magnitud de las demás rutas de `session-api`); D11 de
U4 (proceso de la API separado del trabajador).

**Cómo se mide.**
- En la **máquina de desarrollo con CPU** (NFR2), con PostgreSQL real en contenedor.
- Con la marca `perf` de `pytest` (nivel 1), en proceso y con `time.perf_counter`, 50 repeticiones por caso.
  Se informa la mediana y el p95.
- Con los *fixtures* sintéticos del generador de NFR12.3 (`security-requirements.md`):
  - **típico:** una evaluación de 40 muestras × 3 corridas con unas 15 llamadas por corrida (~1 MiB);
  - **peor caso estimado:** 240 corridas × 30 llamadas (~3,3 MB; `scalability-requirements.md` §1);
  - **máximo:** un reporte válido de exactamente `research_report_max_bytes` (8 MiB).
- Una prueba de rendimiento inestable se arregla o se pone en cuarentena con un *issue*. Nunca se reintenta
  ni se baja su umbral (`team.md`).

## 1. Latencia

| ID | Estado | Qué se mide | Objetivo | Carga | Cómo se mide |
|---|---|---|---|---|---|
| NFR3.1 | nuevo | `POST /research-reports` aceptado, de punta a punta en el servidor (lectura, SHA-256, JSON, esquema, contraste, validez y escritura) | **p95 ≤ 2 s** | *Fixture* típico | `perf`, nivel 1 |
| NFR3.2 | nuevo | La misma subida con los *fixtures* grandes | Peor caso estimado: **p95 ≤ 6 s**. Máximo: **p95 ≤ 12 s** | *Fixtures* de peor caso y máximo | `perf`, nivel 1 |
| NFR3.3 | nuevo | Rechazos tempranos | `413`: en ≤ 1 s, sin leer más de tope + 64 KiB. `409` (duplicado): ≤ 1 s con el *fixture* máximo, porque solo calcula el SHA-256. `json_depth` y `encoding`: ≤ 1 s con un archivo de 8 MiB | Archivos de tope + 1, duplicado, 8 MiB de `[` y 8 MiB con un byte inválido al final | `perf`, nivel 1 |
| NFR3.4 | nuevo | `GET /research-reports` | **p95 ≤ 500 ms** | 1 000 reportes guardados (techo de NFR3.9) | `perf`, nivel 1 |
| NFR3.5 | nuevo | `GET /research-reports/{id}` | Típico: **p95 ≤ 500 ms**. Peor caso estimado: **p95 ≤ 2 s** (respuesta con unas 7 200 llamadas) | Un reporte de cada tamaño | `perf`, nivel 1 |
| NFR3.6 | nuevo | `GET /research-reports/compare` | **p95 ≤ 1 s** con dos típicos; **≤ 4 s** con dos del peor caso | Pares de reportes | `perf`, nivel 1 |
| NFR3.7 | nuevo | La consola no se bloquea | Con 1 000 reportes en la lista, cambiar un filtro o marcar una casilla responde en **≤ 300 ms**. Mientras una subida está en `uploading`, «Cancelar» y Escape siguen respondiendo, y las demás pestañas de la consola no se congelan (la subida es una petición asíncrona del navegador) | Lista de 1 000 filas | Playwright, nivel 3, con `performance.now()` |

**Presupuesto orientativo de NFR3.2 (máximo).** La medición lo confirma; no lo reemplaza.

| Tramo | Presupuesto |
|---|---|
| Lectura del cuerpo y SHA-256 | ≤ 0,5 s |
| Profundidad y análisis del JSON | ≤ 1,5 s |
| Esquema C19 con `jsonschema` | ≤ 4 s |
| Coherencia, contraste y validez | ≤ 1 s |
| Escritura (fila y tablas hijas en una transacción) | ≤ 5 s, dentro de `research_report_write_timeout_s` (15 s) |

Si el esquema no cabe en su tramo, se compila el validador una sola vez al arrancar (D3 de
`tech-stack-decisions.md`); el umbral no se cambia.

## 2. CPU primero

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR2.1 | nuevo | Las pruebas de U12 de los niveles 0 y 1 no exigen GPU, red ni modelos. | Corren en un contenedor sin GPU; `pytest-socket` bloquea toda conexión salvo la de PostgreSQL de la prueba. U12 no carga ningún modelo | Nivel 0 y nivel 1 |

## 3. Recursos

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR3.8 | nuevo | Una subida máxima no desborda el proceso de la API. | El aumento de memoria residente del proceso de la API durante una subida del *fixture* máximo es **≤ 256 MiB**, y con dos subidas máximas simultáneas (E8) **≤ 512 MiB**. Infrastructure Design suma esa cifra al `limits.memory` del proceso de la API de `session-api`, con el 20 % de margen de U4 | Nivel 1, con el pico de RSS medido por `psutil` |

Si un pico supera su tope, es un hallazgo que se corrige por PR, no un tope que se sube en silencio.
