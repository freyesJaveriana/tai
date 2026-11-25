# Ronda 1 — U01-T02b

VEREDICTO: NO-VERDE

Contexto: el SHA-256 de la tarea coincide (`sha256sum /workspace/docs/loop/tareas/U01-T02b-registro-id-relativo.md` da `c7d0880b…2d76a04661c4bb8fe19fff72846e2e7a20d61f792efa1f32735d03`). La rama `tarea/U01-T02b` tiene un solo commit (8936bc3) sobre `feat/b1-contratos`. Al terminar, el worktree está limpio: solo quedan cachés que git ignora (`git -C /workspace/.worktrees/U01-T02b status --short --ignored contracts`).

## Criterios de aceptación, verificados por mí
| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| 1 | `$id` relativo aceptado y referencia resuelta | `timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T02b/contracts pytest tests/test_registry.py --no-cov` | pasa: 15 passed |
| 1-rojo | Rojo primero, reproducido por mí | `timeout 60 uv run --frozen --offline --directory /workspace/contracts pytest -p no:cacheprovider /workspace/.worktrees/U01-T02b/contracts/tests/test_registry.py --no-cov -q` (las pruebas nuevas contra el `registry.py` de la base) | 3 failed, 12 passed, igual que la bitácora: 2 `LoadError … solo se admite bajo vendor/` y 1 `DID NOT RAISE` con `//example.com/x` |
| 2 | Suite de las tareas anteriores | `timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T02b/contracts pytest tests/test_loaders.py tests/test_registry.py tests/test_canonical.py tests/test_validators.py tests/test_package_map.py tests/test_runner.py --cov-fail-under=0` | pasa: 80 passed |
| 2 | 100 % de ramas en `registry` | `uv run --frozen --offline --directory /workspace/.worktrees/U01-T02b/contracts coverage report --include=src/veridicus_contracts/registry.py --fail-under=100` | pasa: 48 sentencias, 22 ramas, 100 % |
| 3 | Tipos | `uv run --frozen --offline --directory /workspace/.worktrees/U01-T02b/contracts mypy --strict src` | pasa: `Success: no issues found in 6 source files` |
| 3 | Lint | `uv run --frozen --offline --directory /workspace/.worktrees/U01-T02b/contracts ruff check .` | pasa: `All checks passed!` |
| 4 | AUTONOMIA-01 | `bash /workspace/.worktrees/U01-T02b/scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T02b` | pasa: `0 apariciones` |

## Comprobaciones adicionales del encargo, por lectura de vuelta
- **URIs ajenas.** Llamé a `_uri_de` directamente con 27 `$id`, en la rama y en la base (`uv run … python -c` con `"\x24id"`). Se rechazan:
  - las absolutas de otro sitio: `https://example.com/x`, `file:///etc/passwd`, `data:…`, `urn:x`, `javascript:x`, `http:x`, `HTTPS://…` y la que empieza con espacio;
  - las que salen de la base: `//example.com/x`, `../x`, `a/../../x`, `/../x` y `..`.
  - **Mejora respecto de la base:** en `feat/b1-contratos`, `//example.com/x` se registraba como `https://example.com/x`. El cambio cierra ese hueco.
  - `%2e%2e/x`, `a\..\..\x` y `\\example.com\x` se aceptan, pero quedan como texto bajo `https://veridicus.invalid/`: ni `urljoin` ni `referencing` los decodifican, así que no salen del host.
- **Forma de C6.** Usé un esquema sintético con `$id` `veridicus/contracts/analyzer/v1/salida`. Se registra en `https://veridicus.invalid/veridicus/contracts/analyzer/v1/salida`. Desde otro esquema, `$ref` `/veridicus/contracts/analyzer/v1/salida#/$defs/cita` funciona: la instancia válida da True y la inválida False. También funcionan una `$ref` interna `#/$defs/t` dentro del esquema de `$id` relativo y una relativa entre hermanos `salida#/$defs/t`.
- **Duplicados:** no se detectan. Ver F-01.
- **Alcance:** se tocan 5 archivos: `registry.py`, `tests/data/registro_relativo/{a,b}.schema.json`, `test_registry.py` y la bitácora. Ninguno es de T03. No hay rastro de C6, de `/insumos` ni de datos del piloto; los esquemas son sintéticos (`ejemplo/v1`).

## Hallazgos

### F-01 · NARANJA · contracts/src/veridicus_contracts/registry.py:63-74 · Un `$id` repetido se sobrescribe sin aviso, y el cambio abre una segunda grafía para el mismo `$id`
`build_registry` pasa todos los pares a `with_resources` y no comprueba si una URI ya está registrada. Con este cambio, `veridicus/contracts/ejemplo/v1/a` y `/veridicus/contracts/ejemplo/v1/a` dan la misma URI. Lo probé con dos esquemas sintéticos, uno con cada grafía: la salida fue `DUPLICADO NO DETECTADO; gana: {… '$id': '/veridicus/contracts/ejemplo/v1/a', 'type': 'integer'}`. Gana el último en orden alfabético y no se lanza ningún error.

Ya pasaba antes con dos `$id` idénticos con barra (lo reproduje: `DUPLICADO IDENTICO NO DETECTADO`). Lo nuevo es que ahora un esquema escrito con barra puede ocultar a la copia de C6, que no la lleva. Así, todo lo que valida por el registro dejaría de validar contra la copia sin editar (BR1.8, F7), sin ningún error.

Corrección pedida: `build_registry` lanza `LoadError` si dos archivos dan la misma URI (nombrando los dos archivos), con una prueba de las dos grafías y otra de dos `$id` idénticos.

### F-02 · AMARILLO · contracts/src/veridicus_contracts/registry.py:58-60 · Se admiten `$id` degenerados que antes se rechazaban
`""` (queda en la base misma, `https://veridicus.invalid/`), `#frag`, `?q=1`, `veridicus/a#frag` y `./x` ahora se aceptan; en la base se rechazaban. Ninguno sale del dominio `.invalid`. Aun así, un `$id` con fragmento no vale en 2020-12, y uno vacío ocupa la raíz del registro, lo que agrava F-01. Sugerencia: rechazar los `$id` vacíos, con fragmento o con consulta.

### F-03 · AMARILLO · contracts/tests/test_registry.py:117-121 · La prueba de `../x` no comprueba por qué se rechaza
`match=r"\$id"` coincide con cualquier `LoadError` del registro. Con el código de la base, `../x` y `a/../../x` pasaban la prueba por la rama equivocada («solo se admite bajo vendor/»). Sugerencia: comprobar `sale de la base`.

## Tareas candidatas (defectos reales fuera de alcance)
- Ninguna. El duplicado ya existía en la base, pero entra en esta tarea: es el mismo módulo guardia y la nueva grafía lo agrava (F-01).

```
VEREDICTO: NO-VERDE
NARANJA|contracts/src/veridicus_contracts/registry.py:63-74|Un $id repetido se sobrescribe sin aviso, y el cambio abre una segunda grafía para el mismo $id
AMARILLO|contracts/src/veridicus_contracts/registry.py:58-60|Se admiten $id degenerados que antes se rechazaban
AMARILLO|contracts/tests/test_registry.py:117-121|La prueba de ../x no comprueba por qué se rechaza
INFORME: docs/loop/revisiones/U01-T02b/ronda-1.md
```
