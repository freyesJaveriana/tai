# Ronda 3: U01-T13

VEREDICTO: NO-VERDE

Revisión de 26bfa49 contra a3d8e0c.

- Los seis criterios de aceptación pasan. CA-2 da 152 sentencias y 64 ramas, con el 100 % cubierto.
- El rojo se reproduce: 7 fallan y 159 pasan.
- Quedan cerrados F-09 en su forma original, F-10 (los cuatro mutantes mueren), F-11 y el AMARILLO del `enum`.

## Hallazgos

### F-12 · NARANJA · `checks/servers.py:86-152`: un `$ref` estructural no se sigue

Un path item, una respuesta, un link, un callback o un servidor de canal de AsyncAPI puede ser un `$ref` que apunta a `#/x-…` o a otro archivo. Lo que hay detrás no se revisa: con `https://api.openai.com` detrás, la guardia da `[]`.

**Corrección:** que esos `$ref` solo puedan apuntar a lo que la guardia recorre:
- en OpenAPI, `#/components/{pathItems,responses,links,callbacks}/…`;
- en AsyncAPI, `#/servers/…` o `#/components/servers/…`.

Lo demás da el problema «referencia fuera de la estructura». Hace falta un control negativo por cada tipo de nodo.

### F-13 · NARANJA · `checks/servers.py:51`: mutantes vivos W01, W02, W04 y W05

Se pueden quitar `trace`, `head`, `options` o `delete` de `METODOS` y ninguna prueba falla.

**Corrección:** parametrizar el control de `servers` por operación con los ocho métodos.

### AMARILLO

- **W10 y E04:** un `server` que no es objeto y una variable que no es objeto hacen que la guardia falle con `TypeError`, sin un control que lo cubra.
- **OpenAPI 3.2:** no se recorren `query` ni `additionalOperations`. Conviene rechazar cualquier versión de `openapi` distinta de 3.1.
- **AsyncAPI:** `channels.*.servers` no se recorre. Su variante con `#/x-…` queda dentro de F-12.

## Nodos comprobados

Hoy ningún contrato usa estos rodeos. Los únicos `$ref` que existen son de esquema. F-12 es un riesgo para C1 (T14) y para los contratos futuros.

## Candidatas

- **K-18:** un `code` propio para el 422 de la ruta de voz.
- **K-17 (amplía):** §4.9 debe fijar que los `$ref` estructurales solo apuntan a `components` y qué versiones de OpenAPI se admiten.
