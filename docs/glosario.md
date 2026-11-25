# Glosario de identificadores

Un identificador de código se escribe en inglés y su traducción del PRD es única: ningún término se traduce
de dos formas (`team.md`, Code Style). El glosario de los identificadores de los contratos (U1) está en
`contracts/README.md`; aquí se suman los de las demás bibliotecas.

## Anonimizador (`libs/anonymizer`, U10)

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
