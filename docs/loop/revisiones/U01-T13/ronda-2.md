# Ronda 2: U01-T13

VEREDICTO: NO-VERDE

Revisión de a3d8e0c contra 32658da.

- Los seis criterios de aceptación pasan. CA-1a da 125 passed. CA-2 da 113 sentencias y 50 ramas, al 100 %.
- El rojo se reproduce: 55 failed, 98 passed.
- La suite con `-m "not c1 and not c19"` da 674 passed y 15 failed. Los 15 fallos son de T11.

## Hallazgos de la ronda 1

- **F-01 y F-02:** cerrados como decidió el orquestador. La comparación de los `code` de C21 con el catálogo sale de T13 y pasa a T15 (K-19). Solo queda la comprobación de P-T07-1, y la contradicción quedó anotada en la bitácora.
- **F-03, F-05, F-06 y F-07:** cerrados.
- **F-08:** queda a medias; sigue como F-11.
- **Desvíos del codificador:** los dos se aceptan.
  - **Protocolo AsyncAPI:** `http`, `redis` o ausente. C2, C3 y C5 usan `redis`. El «siempre http» de §4.9 se refiere al esquema de la URL. Se registra como precisión de §4.9.
  - **401 y 503 de voz sin cuerpo:** contract-summary, línea 126.

## Hallazgos

### F-09 · NARANJA · `checks/servers.py:52, 93`: `SALTADAS` se aplica a cualquier profundidad

Con `https://api.openai.com`, la guardia da `[]` en seis casos:

- un callback llamado `schema`;
- un link llamado `example`;
- un webhook llamado `examples`;
- `components.pathItems.schemas`;
- `components.links.example`;
- `components.callbacks.properties`.

**Corrección:** recorrer el documento por la estructura de OpenAPI y AsyncAPI, o saltar esas claves solo donde son palabras de esquema o de ejemplo.

### F-10 · NARANJA · `checks/servers.py:34, 159`: mutantes vivos no equivalentes

- **M54:** `%` en `RUTA` acepta `/%2F/evil.com`.
- **M50 y M51:** `@` y `:` en `RUTA`.
- **M55:** `startswith("/servers")` trata `serversX` como servidor global.

### F-11 · NARANJA · `contracts/api/speech-internal.v1.yaml:56-72`: el 422 rechaza `instance`

El `Problem` de C1 (contract-summary, líneas 237-246) declara `instance` y `type` con `format: uri-reference`, y RFC 9457 los admite.

### AMARILLO

- **`enum` mal formado:** un `enum` que no es lista se ignora en silencio. `enum: []` también pasa sin aviso.
- **AsyncAPI 3:** `channels.*.servers` con `$ref` daría un falso positivo en el futuro.
- **Punteros:** repiten nombres de claves del documento.
- **Ejemplo del 422:** usa `speech.text_rejected`, que en el catálogo es 409 (K-18).

## Sin hallazgo

- **Variables:** anidadas, sin `default` o sin declarar, quedan rechazadas.
- **Codificaciones:** `%2F`, `%2f%2f`, `%5C` y `..%2F` se rechazan. `/.//evil.com` resuelve al host interno.
- **Protocolo:** en mayúsculas o `null` se rechaza.
- **F-07:** ningún mensaje repite marcas *canary*.

## Candidatas

- **§4.9:** debe nombrar los `servers` de ruta, operación, `links`, callbacks y webhooks, y el `protocol` de AsyncAPI. Se amplía K-17.
- **Ruta de voz:** necesita un `code` 422 propio o una precisión del catálogo. Se amplía K-18.
