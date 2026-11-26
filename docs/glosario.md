# Glosario de identificadores

Un identificador de código se escribe en inglés y su traducción del PRD es única: ningún término se traduce
de dos formas (`team.md`, Code Style). Este es el **único** glosario del repositorio; cada unidad suma su
sección. Excepción: los campos del contrato común del TG conservan su nombre en español.

## Contratos (U1)

| Identificador | Término del PRD o significado |
|---|---|
| `review_report` | «reporte de revisión»; sustituye a «reporte forense» (D10.4, VE-03) |
| `review_suggestion` | «sugerencia de revisión»: todo hallazgo de la IA, con estado editable que cambia un humano |
| `undocumented_fact` | «Hecho No Documentado»: resultado normal por debajo del umbral, no un error |
| `cancel_token` | token de cancelación cooperativa del almacén de archivos de reportes (NFRD-U7-11) |
| `view_outdated` | `report.view_outdated`, error 409 cuando el resumen cambió desde que el analista lo abrió (NFRD-U7-11) |

## Anonimizador (U10)

| Identificador | Término del PRD o significado |
|---|---|
| `Anonymizer` | el anonimizador (C20): seudonimiza, llama una vez al proveedor y restaura, o falla cerrado |
| `build_anonymizer` | construcción del módulo en la CLI (F3b, PD-7); no tiene parámetro para saltarse la seudonimización |
| `AnonymizerUnavailable` | el anonimizador no puede atender la llamada: falla cerrado, sin petición y sin `ModelCall` (AUTONOMIA-04) |
| `pseudonymize` | seudonimizar: sustituir cada entidad por una marca (`[ENTIDAD_1]`, `[LUGAR_1]`, `[IDENTIFICADOR_1]`) antes de enviar |
| `restore` | restaurar: devolver cada marca de la respuesta a su valor original, dentro del clúster |
| `altered_markers` | marcas que el proveedor alteró en su respuesta; se informan, no se adivinan |
| `MaskTable` | tabla de correspondencia marca ↔ valor; vive en memoria, se vacía en todos los finales y nunca se registra |
| `AllowedWordList` | lista versionada de palabras con mayúscula inicial que no se enmascaran; nunca lleva nombres de pila |
| `safety_net` | red de seguridad de la detección: marca lo que las reglas no clasificaron (PD-2) |
| `FakeTransport` | transporte HTTP falso para las pruebas y la demostración; captura la petición cruda y no abre red |
| `coverage_gate` | compuerta de cobertura: 100 % de ramas en los módulos guardia y 80 % de líneas |

## Analizador de incoherencias (U11)

| Identificador | Término del PRD o significado |
|---|---|
| `AnalysisRun` | una corrida del analizador sobre una transcripción: de la validación previa a la salida C6 |
| `JudgeCandidate` | candidato a hallazgo que propone el juez, con sus dos citas, antes de filtrarlo y verificarlo |
| `DiscardRecord` | `Discard` en el código: registro de un candidato descartado (por ejemplo, cita alterada o en otro turno); no sale como hallazgo |
| `Survivor` | candidato cuyas dos citas se verificaron en su turno y que pasa al verificador |
| `FilterResult` | resultado del filtro determinista de citas: sobrevivientes y descartes |
| `RunState` | estado de la corrida con su fase (`Phase`); `error` implica hallazgos vacíos |
| `preflight` | validación previa a toda llamada: entrada, consentimiento y límites (F1) |
| `EffectiveConfig` | configuración efectiva del perfil: límites, perfil y SHA-256 del *prompt* |
| `ModelGateway` | puerto de llamadas a modelos; el adaptador `anonymizing` envía todo destino externo por el `Anonymizer` |
| `same_family` | aviso del perfil de demostración: juez y verificador son de la misma familia, así que no sirve para medir |
| `permuted_verifier` | segunda consulta al verificador con las dos citas permutadas |
| `composition_root` | `cli/composition.py`, el único lugar que importa el anonimizador (PD-7) |
| `coverage_gate` (U11) | compuerta de los cuatro paquetes: 100 % de ramas en 9 módulos guardia y 80 % de líneas por paquete |
