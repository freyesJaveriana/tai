# Reglas de negocio — U10 anonymizer

**Insumos.** Los mismos de `entities.md`. Todo el módulo es guardia de AUTONOMIA-04: vive en `domain/`
como código puro y exige 100 % de ramas (team-practices, si se construye).

```yaml
rules:
  # BR1 — Enmascaramiento
  - id: BR1.1
    statement: Antes de cualquier llamada externa, el proxy reemplaza nombres, lugares y números de expediente por marcadores consistentes.
    category: policy
    applies_to: [MaskingRequest, MaskTable]
    trigger: Cada llamada judge o embed
    logic: SI un tramo del payload coincide con DetectionRuleSet ENTONCES se reemplaza por [PERSONA_n], [LUGAR_n] o [EXPEDIENTE_n]; el mismo valor (sin mayúsculas ni tildes) recibe el mismo marcador en toda la llamada.
    violation: Prueba de nivel 0 del payload saliente con nombres, lugares y expedientes sembrados.
    source: FR11.3; AC11.3.1; Respuesta P1 = A
  - id: BR1.2
    statement: La detección combina expresiones regulares en español con la lista de nombres propios del escenario, y enmascara ante la duda.
    category: calculation
    applies_to: [DetectionRuleSet]
    trigger: Detección
    logic: SI un tramo coincide con un patrón de persona, de lugar, de expediente o con un nombre propio del escenario ENTONCES se enmascara; SI coincide con dos categorías ENTONCES gana la primera en el orden EXPEDIENTE, PERSONA, LUGAR; ningún tramo que coincida queda sin enmascarar.
    violation: Prueba de nivel 0 con casos ambiguos («San José»).
    source: Respuesta P2 = A; FR11.3
  - id: BR1.3
    statement: La respuesta externa se restaura dentro del clúster con la tabla de la misma llamada, y la tabla se destruye al terminar.
    category: policy
    applies_to: [MaskTable]
    trigger: Respuesta del destino externo
    logic: SI la respuesta trae marcadores de la tabla ENTONCES se reemplazan por los valores originales antes de devolverla a ModelGateway; un marcador desconocido se deja tal cual; al terminar la llamada (éxito o error) la tabla se borra de memoria.
    violation: Prueba de nivel 0.
    source: Respuesta P1 = A
  - id: BR1.4
    statement: Los embeddings externos nunca reciben texto sin enmascarar.
    category: constraint
    applies_to: [MaskingRequest]
    trigger: Llamada embed
    logic: SI la operación es embed ENTONCES el texto se enmascara igual que en judge antes de enviarlo; los vectores no se restauran.
    violation: Prueba de nivel 0.
    source: AUTONOMIA-04; AC11.3.1

  # BR2 — Falla cerrada
  - id: BR2.1
    statement: Si el enmascaramiento falla, no se hace la llamada externa.
    category: constraint
    applies_to: [MaskingRequest]
    trigger: Error en la detección, en la carga de reglas o de la lista del escenario
    logic: SI cualquier paso del enmascaramiento falla o tarda más que su timeout ENTONCES no se envía nada y la llamada devuelve error del sistema; el turno queda en error con turn.error.system.
    violation: Prueba de nivel 0 con cada rama de fallo.
    source: AC11.3.1; FR11.3
  - id: BR2.2
    statement: El proxy no arranca sin reglas válidas, sin destino HTTPS o sin la referencia a su credencial.
    category: validation
    applies_to: [DetectionRuleSet, OutboundDestination]
    trigger: Arranque de anonymizer-proxy
    logic: SI falta o es inválido cualquiera de ellos ENTONCES el proceso termina con código ≠ 0 y /readyz no pasa.
    violation: Prueba de nivel 0.
    source: NFR10; C16
  - id: BR2.3
    statement: Nada del payload original, de la tabla ni de la respuesta restaurada aparece en logs.
    category: constraint
    applies_to: [MaskingRequest, MaskTable]
    trigger: Cualquier log del proxy
    logic: SI se registra una llamada ENTONCES solo request_id, operation, número de reemplazos por categoría y resultado; nunca texto.
    violation: Prueba de nivel 1 con un canary sembrado.
    source: AC9.1.5; NFR10

  # BR3 — Red
  - id: BR3.1
    statement: Solo el proxy tiene salida fuera del clúster, y solo hacia su destino.
    category: constraint
    applies_to: [OutboundDestination]
    trigger: Política de manifiestos
    logic: SI otro pod tiene salida fuera del clúster, o el proxy la tiene hacia algo distinto de su destino, ENTONCES la política de nivel 0 falla; con control negativo.
    violation: Prueba de nivel 0 (Kyverno CLI sobre los manifiestos).
    source: AC11.3.2; AC9.1.1; AUTONOMIA-04
  - id: BR3.2
    statement: Con el proxy construido, ModelGateway solo acepta como destino externo el proxy; cualquier otro destino no interno impide arrancar.
    category: constraint
    applies_to: [OutboundDestination]
    trigger: Arranque de semantic-agent y session-api
    logic: SI la URL del juez o de embeddings no es interna del clúster ni es el proxy ENTONCES el servicio no arranca.
    violation: Prueba de nivel 0.
    source: AC9.1.4; C13
  - id: BR3.3
    statement: La verificación en el clúster de que solo el proxy sale es manual y de solo lectura.
    category: policy
    applies_to: [OutboundDestination]
    trigger: Antes de la sustentación
    logic: SI se verifica en el clúster ENTONCES desde cada pod sensible curl -m 5 a un host público termina con código ≠ 0, desde el proxy solo alcanza su destino, y ningún paso aplica cambios al clúster.
    violation: Verificación manual con su evidencia.
    source: AC9.1.2; AUTONOMIA-01
  - id: BR3.4
    statement: El proxy aparece en la tabla de fronteras de Infrastructure Design con lo que cruza.
    category: policy
    applies_to: [OutboundDestination]
    trigger: Infrastructure Design
    logic: SI se construye el proxy ENTONCES la tabla de fronteras lo lista fuera de la frontera solo con el payload enmascarado.
    violation: Revisión manual en Infrastructure Design.
    source: AC9.1.3
```

## Resumen

| Grupo | Reglas | Qué protege |
|---|---|---|
| BR1 Enmascaramiento | BR1.1–BR1.4 | Nombres, lugares y expedientes reales fuera del clúster |
| BR2 Falla cerrada | BR2.1–BR2.3 | Que un error deje pasar el payload original o lo registre |
| BR3 Red | BR3.1–BR3.4 | Otra salida a internet que no sea el proxy |
