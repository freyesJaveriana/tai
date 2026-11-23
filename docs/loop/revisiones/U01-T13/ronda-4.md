# Ronda 4: U01-T13

VEREDICTO: NO-VERDE

Revisión de c00ec19 contra 26bfa49.

- Los seis criterios de aceptación pasan. En CA-2, `servers.py` queda con 190 sentencias y 82 ramas, todas cubiertas (100 %).
- El rojo se reproduce: 39 fallos y 156 aprobados.
- F-13 queda cerrado: quitar cualquiera de los ocho métodos rompe al menos 2 pruebas.
- Los dos AMARILLO de la ronda 3 quedan cerrados.
- Limitar `openapi` a 3.1.x no rompe C1. Según contract-summary (línea 209), C1 declara 3.1.0 y sus `$ref` de respuesta son `#/components/responses/Problem`.

## Hallazgos

### F-14 · NARANJA · `checks/servers.py:62-66`: `%2F` en el nombre del destino

`[^/]+` acepta `%`. Además, el fragmento se decodifica antes de leerse como JSON Pointer (RFC 6901 §6). Por eso `referencing` resuelve `#/components/pathItems/p%2Fx-oculto` a un `servers` externo, y la guardia da `[]`. Pasa lo mismo con respuestas, links y canales de AsyncAPI.

**Corrección:**
- Limitar el nombre a `[A-Za-z0-9._~-]+`.
- Exigir que el nombre exista como clave del componente recorrido.
- Añadir controles con `%2F` para los cinco tipos.

### F-15 · NARANJA · `checks/servers.py:62-66, 147`: mutantes vivos no equivalentes

| Mutante | Qué cambia |
|---|---|
| R11 | `.+` en lugar de `[^/]+` |
| R13 | `#/.*servers/…` |
| R14 | Una respuesta puede apuntar a `links` |
| R15 | Un callback puede apuntar a `pathItems` |
| R16 | Un link puede apuntar a `responses` |
| R18 | `continue` pasa a `return` en `_de_canales` |

Faltan controles para:
- `/` dentro del nombre;
- `#/x/servers/e`;
- un tipo cruzado por cada nodo;
- dos canales donde el primero tiene `servers` que no es lista. Este caso debe salir como «mal formado».

### AMARILLO

- **`$ref` colgantes y ciclos:** no dan ningún problema. Es un fallo cerrado, porque `PointerToNowhere` aparece al usarlos, pero queda fuera de la guardia.
- **Documento sin `openapi` ni `asyncapi`:** si falta la clave, da `[]`. También da `[]` con `swagger: '2.0'` y `host: api.openai.com`. Conviene exigir `openapi: 3.1.x` o `asyncapi: 3.0.x`.
- **`#` extra en el fragmento:** se acepta, pero no es explotable.
