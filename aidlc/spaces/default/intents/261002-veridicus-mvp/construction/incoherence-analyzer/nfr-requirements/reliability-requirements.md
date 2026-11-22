# Requisitos de fiabilidad y calidad de la IA — U11 incoherence-analyzer

**Revisión 1 (2026-11-22): primera pasada.**
- **IDs.** Todo es **nuevo** y hereda el ID del NFR de Inception (NFR4, NFR6, NFR10, NFR13).
- **Por qué existe.** U11 es `library`, y el archivo de etapa no pide este documento para ese tipo. Se añade
  porque el fallo cerrado de AUTONOMIA-05, los plazos y reintentos, y los umbrales de NFR4 son de U11.
- **Respuestas.** **P2 = A** (umbrales estadísticos, NFR-U11-02) y **P3 = A** (composición del conjunto,
  NFR-U11-03).

**Insumos.** BR3.4, BR5.1–BR5.8, BR6.1–BR6.4, BR7.1–BR7.3, BR10.3, BR11.2–BR11.4, BR12.1–BR12.7 y BR13.1–BR13.5
de rules; flujos F1–F12 y escenarios de functional-spec; NFR4, NFR6, NFR10 y NFR13 de requirements; C6, C13,
C17, C19 y C25 de contract-summary; mediciones M4 y M5 del reporte de ZINE (20/20 respuestas JSON válidas con
el razonamiento apagado; 4/4 pares repetibles con semilla fija).

## 1. Fallo cerrado, plazos y reintentos (NFR10)

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR10.4 | nuevo | Toda llamada lleva su *timeout* y respeta el plazo de la corrida (BR7.2). | `timeout_s = min(model_call_timeout_s, deadline − ahora)` en el 100 % de las llamadas capturadas. Con reloj simulado: plazo agotado entre ventanas da `tiempo_agotado` y 0 llamadas nuevas; `cancelled()` verdadero tras la primera llamada da `Cancelled` y una sola llamada | Nivel 0 |
| NFR10.10 | nuevo | Un fallo nunca produce un resultado parcial (AUTONOMIA-05; BR7.1). | Para cada código de error de la biblioteca (`salida_invalida`, `bloqueo_contenido`, `tiempo_agotado`, `proveedor`, `anonimizador_no_disponible`, `incidente_anonimizacion`), la `Salida` tiene `estado: error`, hallazgos y descartes vacíos, sin `observaciones_conductor`, y valida contra C6. 100 % de ramas en ese módulo | Nivel 0 |
| NFR10.11 | nuevo | Reintentos solo donde son seguros (BR10.3). | Adaptador local: conexión rechazada, 502, 503 o 504 → hasta 2 reintentos a los 2 s y 6 s, solo si el plazo restante alcanza. *Timeout* y salida inválida → 0 reintentos. Adaptador `anonymizer` y cliente de C21 → 0 reintentos en todo caso. Una prueba por fila de la tabla de C13 con reloj simulado | Nivel 0 |
| NFR10.12 | nuevo | La CLI nunca deja archivos a medias (BR11.2, BR11.4). | Validación previa del lote completa antes de la primera llamada; si falla, 0 archivos escritos (ni `AVISO.txt`). Cada archivo se escribe en un temporal del mismo directorio, se sincroniza (`fsync`) y se renombra (`os.replace`); con un sistema de archivos *fake* que falla a mitad, no queda el archivo final, se borra el temporal y el código es 5 | Nivel 0 |
| NFR10.13 | nuevo | Interrupción y códigos de salida (BR11.3). | SIGINT o SIGTERM pasa como cancelación: la corrida en curso queda sin salida, el reporte se escribe con las hechas y el código es 5. Una prueba por código 0, 2, 3, 4, 5 y 6 | Nivel 0 |
| NFR10.15 | nuevo | Configuración faltante impide arrancar (`team.md`). | Sin `contracts/limits.v1.yaml`, sin el perfil pedido, con el SHA-256 del *prompt* distinto del de la configuración o con una cifra de entorno que **sube** un tope de C25: la CLI termina con 3 y `semantic-agent` no construye el `ModelGateway` | Nivel 0 |

## 2. Calidad de la IA en el conjunto sintético (NFR4)

### Umbrales

Viven en `evaluation/thresholds.v1.yaml`, cambian solo por PR y nunca bajan (`team.md`).

| ID | Estado | Métrica | Umbral | Bloquea |
|---|---|---|---|---|
| NFR4.1 | nuevo | `verified_quotes` (citas emitidas que verifican de nuevo con BR5.5) | = 1 | Siempre, con todo perfil |
| NFR4.2 | nuevo | `json_format_errors` | = 0 | Siempre |
| NFR4.3 | nuevo | `permutation_coverage` | = 1 | Siempre |
| NFR4.4 | nuevo | `anonymizer_leaks` | = 0 | Siempre |
| NFR4.5 | nuevo | `completed_runs` | = 1 en evaluación (la tolerancia de 0,98 es de NFR8.2, que no es una evaluación) | Siempre |
| NFR4.6 | nuevo | `precision` (media de 3 corridas) | ≥ 0,70 | Con `evaluacion-comercial` (P2 = A) |
| NFR4.7 | nuevo | `recall` (media de 3 corridas) | ≥ 0,60 | Con `evaluacion-comercial` (P2 = A) |
| NFR4.8 | nuevo | `three_run_agreement` (Jaccard medio por muestra) | ≥ 0,60 | Con `evaluacion-comercial` (P2 = A) |
| NFR4.9 | nuevo | `reversed_order_consistency` | > 0,65 | Con todo perfil de evaluación (`team.md`) |
| NFR4.10 | nuevo | `type_agreement` y sensibilidad por tramo de distancia | Sin umbral; se reportan | No |

**Cómo bloquea.** `veridicus evaluate` termina con 6 si una métrica que bloquea con ese perfil no alcanza su
umbral. Con los otros perfiles (`evaluacion-local-zine`, `todo-local`) el reporte lleva `passes` por métrica y
`blocking: false`, y el código es 0 si las absolutas pasan. El reporte va adjunto al PR de IA y a cada entrega
etiquetada (`team.md`, nivel 2).

### Conjunto y repetibilidad

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR4.11 | nuevo | Composición mínima del conjunto 1.0.0 (P3 = A; BR13.2). | `scripts/check-dataset.py` sobre `evaluation/synthetic/manifest.yaml` exige: 40 muestras; 21 con contradicción, 3 por cada uno de los 7 tipos; 11 coherentes; 8 trampa, 2 por cada uno de los 4 casos; ≥ 6 con más de 120 turnos; ≥ 3 contradicciones esperadas en cada tramo de distancia (NFR-U11-09); cada valor de `tipo_hecho` y de `perfil_persona` en ≥ 2 muestras. Un manifiesto con 2 muestras de un tipo hace fallar la comprobación | Nivel 0 |
| NFR4.12 | nuevo | Cada muestra es comprobable sin el modelo (BR13.1, BR13.2). | Cada contradicción esperada trae sus dos citas literales, y ambas verifican con BR5.5 sobre su muestra; cada muestra valida contra C6 | Nivel 0 |
| NFR4.13 | nuevo | El reporte identifica la medición. | `reporte.json` (C19 v2) trae `dataset_version`, `dataset_sha256`, `prompt_sha256`, `profile_sha256`, `config_sha256`, el modelo por llamada, `origin` y las métricas. Un reporte que no valida contra C19 da código 5 | Nivel 0 |
| NFR4.14 | nuevo | Repetibilidad con modelos locales. | Con semilla fija y `temperature: 0`, dos corridas de `evaluacion-local-zine` sobre la misma muestra dan el mismo conjunto de pares (lo midió M5: 4/4). Con modelos comerciales no se exige; lo mide NFR4.8 | Nivel 2 en ZINE |

## 3. Calidad del razonamiento (NFR6)

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR6.1 | nuevo | Las observaciones se pueden calificar a ciegas. | `veridicus evaluate --export-likert <dir>` (opción nueva, NFR-U11-15) escribe por muestra el `hecho`, las dos citas y las `observaciones`, sin perfil ni modelo, para dos evaluadores. La media de la calificación Likert es ≥ 4,5/5 (`team.md`, manual, antes de la sustentación). La comprobación de la exportación es de nivel 0; la calificación es manual | Nivel 0 y manual |

## 4. Cobertura (NFR13)

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR13.1 | nuevo | Líneas. | ≥ 80 % de líneas en cada uno de `libs/incoherence_analyzer`, `libs/model_gateway`, `libs/execution_profiles` y `libs/integrity_policy`, medido en la CI y bloqueante | CI |
| NFR13.2 | nuevo | Ramas en los módulos guardia. | 100 % de ramas en: verificación de citas (BR5.5–BR5.7), validación de la salida y sustitución por error (BR7.1, BR8.1), fallo cerrado ante el anonimizador (BR7.4–BR7.6), escáner de vocabulario (BR9.1–BR9.3) y validación de perfiles (BR2). Se escriben primero y se ejecutan en rojo (`team.md`, Ordering) | CI |
| NFR13.3 | nuevo | Exclusiones declaradas. | Solo se excluyen el arnés de `evaluation/` y el código generado, en `pyproject.toml`; cada exclusión nueva se justifica en su PR | Revisión del PR |

## 5. Riesgos

| Riesgo | Tratamiento |
|---|---|
| Con 21 contradicciones esperadas, el margen de una proporción es de unos ±0,15; una corrida mala puede bloquear un PR de IA antes de la demo | Aceptado (P2 = A). Los umbrales no bajan; se mejora el *prompt* o el perfil por PR |
| El verificador en CPU hace que la evaluación tarde horas (NFR2.2) | Se puede partir por muestras y sumar reportes; ninguna prueba de nivel 0 o 1 lo necesita |
| El juez comercial no es determinista | NFR4.8 mide el acuerdo entre 3 corridas en vez de exigir el mismo conjunto (`project.md`) |
