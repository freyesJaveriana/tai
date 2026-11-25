# Ronda 1: U01-T13

VEREDICTO: NO-VERDE

Revisión de `tarea/U01-T13` en 32658da, con base 8e9fb75.

- El sha256 de la tarea coincide: `2f97b12f…0633`.
- Los seis criterios de aceptación pasan con la ejecución del revisor.
- El rojo previo se reproduce en un worktree temporal: da `ImportError` de `servers` y `contrato ausente`.

## Criterios de aceptación

| # | Resultado |
|---|---|
| CA-1a | 69 passed |
| CA-1b | 12 passed, 2 deselected |
| CA-2 | 66 passed; `servers.py` con 59 sentencias y 20 ramas, 100 % |
| CA-3 | 19 passed, pero no mira C21 (F-02) |
| CA-4 | 8 passed |
| CA-5 | mypy `Success`; ruff `All checks passed!` |
| CA-6 | 0 apariciones |
| Suite | `-m "not c1 and not c19"`: solo fallan los 15 de `test_autonomia_03.py`, de T11 |

## Hallazgos

### F-01 · ROJO · `contracts/tests/contracts/test_internal_routes.py:21-90`: desborde de alcance

El archivo compara los `code` de C21 con el catálogo (`CODE_EN_TEXTO`, `_problemas_de_estado`, `test_c21_declara_los_estados_…_del_catalogo`). La tarea, en Fuera, asigna esa comparación a T15 (PD-8).

La propia tarea se contradice: el «Esperado» de CA-3 pide esa garantía. El codificador no dejó constancia de la contradicción. Además, el archivo no está en «Dentro» y su rojo no está en la bitácora.

El resto del archivo sí es una prueba sensible: detecta los 15 defectos que sembró el revisor.

### F-02 · NARANJA · CA-3: el comando no ve C21

`checks/error_codes.py` (`_usados`, línea 171) solo lee las claves `code` y `error_code`. C21 nombra sus `code` en `description`. Con el 409 sembrado como `analysis.timeout`, `test_error_codes` sigue en 19 passed. Se cruza con K-05.

### F-03 · NARANJA · `checks/servers.py:80-87`: `servers` por ruta y por operación sin revisar

`paths./x.servers`, `paths./x.get.servers` y `links.*.server` con `https://api.openai.com` dan `[]`. OpenAPI 3.1 deja que estos sustituyan al `servers` global.

### F-04 · NARANJA · `checks/servers.py:65-69`: variables de servidor

- El `default` se evalúa suelto: con `url: /{p}` y `default: /evil.com` la URL resultante es `//evil.com`, y la guardia da `[]`.
- El `enum` se ignora.
- Falso positivo: `http://veridicus-x:{port}` con `default: '8080'`.

### F-05 · NARANJA · `checks/servers.py:47-48`: rutas relativas que resuelven a un host externo

La guardia acepta `/\evil.com`, `/\/evil.com` y `/<TAB>/evil.com`. En Node, `new URL('/\\evil.com', base).host` es `evil.com`.

### F-06 · NARANJA · `checks/servers.py:30,75`: mutantes vivos no equivalentes

De 38 mutantes sobreviven dos no equivalentes:

- **M18:** quita `re.escape(SUFIJO_DEL_CLUSTER)`, y la guardia acepta `http://evil-svc-cluster-local`.
- **M38:** lee `url` antes que `host` en AsyncAPI.

### F-07 · NARANJA · `checks/servers.py:96, 113`: mensajes con valores del documento

- La línea 96 incluye la `{direccion}`, que puede llevar credenciales.
- La línea 113 incluye `{error}` de `LoadError`, que arrastra claves y fragmentos de YAML.

### F-08 · NARANJA · `contracts/api/speech-internal.v1.yaml:51-59`: el 422 rechaza un Problem Details real

`{type, title, status, code, detail, rule_id}` da `Additional properties are not allowed`. Contradice la regla de team.md sobre errores en fronteras: RFC 9457 con `code` y `detail`.

### AMARILLO

- `tema` no lleva `maxLength` ni la marca de C25. Es K-15, para T15.
- En AsyncAPI no se miran `protocol` ni `pathname`: `protocol: https` pasa.
- Los 401 y 503 de la ruta de voz no declaran cuerpo.
- M30: si un contrato es un directorio, se reporta como «ausente» o como «ilegible», según el mutante.

## Sin hallazgo

- C21 coincide con la revisión 4 de contract-summary y con §4.17:
  - es estricto;
  - tiene patrones;
  - tiene las dos marcas de bytes;
  - tiene los siete estados con su `code`;
  - no incluye `anonymizer.incident` ni `api_key_ref`.
- C16 tiene `/healthz` y `/readyz` con `security: []`.
- No hay ningún destino externo y ningún término de veracidad.
- Solo hay datos sintéticos.
- El alcance de los demás archivos está limpio.

## Candidatas fuera de alcance

- §4.9 de security-design solo nombra `servers[].url` y `variables.*.default`. Debe cubrir los `servers` por ruta y por operación y los `enum` de las variables.
- En el catálogo, `speech.text_rejected` tiene estado 409, pero la ruta interna rechaza el texto con 422.
- En `limits.v1.yaml`, `used_in: []` en dos límites. Ya figura como K-14.
