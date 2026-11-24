# Ronda 1 — U01-T14

VEREDICTO: NO-VERDE

El revisor corrió él mismo los cinco criterios y todos pasan. Reprodujo el rojo y comparó C1 con contract-summary §C1 ruta por ruta, y coinciden. Lo que impide el VERDE es un NARANJA (F-01): la prueba de forma no falla si se amplía la autorización de una ruta. Le dio al `investigador` permiso para exportar y la suite siguió en verde. Ninguna guardia de T15 lo cubriría, porque §4.6 solo exige que haya roles y que pertenezcan a `Role`.

## Criterios de aceptación, verificados por el revisor (HEAD 1260016)

| # | Criterio | Comando | Resultado |
|---|---|---|---|
| 1a | Forma de C1 | `timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T14/contracts pytest tests/contracts/test_console.py --no-cov -q` | 49 passed |
| 1b | Guardias c1 | `timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T14/contracts pytest tests/guards -m c1 --no-cov -q` | 5 passed, 53 deselected |
| 2 | Suite del Bolt | `timeout 300 uv run … pytest tests/checks tests/guards tests/contracts --no-cov -q` | 1760 passed |
| 3 | Rueda | `timeout 120 uv run … pytest tests/test_package_map.py --no-cov -q` | 8 passed |
| 4 | mypy / ruff / yamllint | `uv run … mypy --strict src`, `uv run … ruff check .`, `uv run … yamllint api/console.v2.yaml` | sin problemas, en los tres |
| 5 | Sin cambios al clúster | `bash /workspace/.worktrees/U01-T14/scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T14` | 0 apariciones |

**Rojo reproducido.** El revisor copió `contracts/` sin `api/console.v2.yaml` y usó las pruebas de ea7329a, que son idénticas a las de HEAD:
- `test_console.py`: 49 failed, todos con `contrato ausente: api/console.v2.yaml`;
- `tests/guards -m c1`: 5 failed;
- con el contrato restituido: 54 passed.

**AUTONOMIA-03 y BR3.3.**
- `veracity.comprobar` y `scan_cases.comprobar` devuelven `[]`.
- No hay campos ni enums de veracidad en C1.
- El cambio de «Verdadero» a «true» lo fuerza E8 de `tests/checks/test_veracity.py:628`. Con el texto original falla.

**Cobertura de C1 frente a contract-summary.**
- Coinciden las 37 rutas con sus métodos.
- Coinciden todas las extensiones de operación, los `security`, los `requestBody` con sus medios y sus `x-veridicus-max-bytes`, y los esquemas, salvo las desviaciones declaradas.
- `ErrorCode` coincide con el catálogo `http: true`: 77 valores, y falta solo `anonymizer.incident`, según P-T07-1.
- Todo cuerpo con tope declara `413`. La excepción es `GET /sessions/{id}` por `Since`, y es correcta.

**Desviaciones declaradas.** Se aceptan todas:
- `$ref` a Problem, y el 429 y el 503 de login en línea;
- `413` en login y `/users`, según security-design §4.3;
- `DateTime`, según BR8.1;
- `^T[0-9]{1,4}$`;
- `prefixItems` con `items: false`;
- `$ref` por `$id`, según FD-U12-05 y FD-U1-11;
- «Verdadero» → `true` (ver A-01);
- los seis `operationId`, según security-design §4.6;
- las cabeceras de NFR10.4 en `/download`.

**Alcance.**
- Toca 4 archivos: C1, `test_console.py`, la bitácora y `test_autonomia_03.py`.
- En `test_autonomia_03.py` solo está la edición de P-T14-1: `DECLARAN_TIPO = {C7, C19}`.
- No hay nada de T15, de `limits.v1.yaml` ni del catálogo.

## Hallazgos

### F-01 · NARANJA · `contracts/tests/contracts/test_console.py:307` · Las pruebas no fallan si se amplía la autorización por ruta, ni con otras mutaciones

**Mutaciones que sí se detectan:**
- borrar `/finalize`;
- abrir el cuerpo de `PATCH /users/{id}`;
- `security: []`;
- quitar `x-veridicus-roles`;
- `202` → `201` en `/turns`;
- quitar `X-CSRF-Token`;
- `PUT /profiles`;
- un puntero externo roto;
- `maxLength 129`;
- `minLength 31`.

**Mutaciones que sobreviven (54 passed):**
- `x-veridicus-roles: [analista, admin, investigador]` en `POST /reports/{id}/exports`. El summary lo prohíbe: «el investigador no (A-3)».
- Quitar `x-veridicus-owner-only` de `POST /sessions/{id}/turns`.
- Quitar `x-veridicus-owner-only-for-role` de `/exports`.
- `201` → `200` en `POST /sessions`.
- Quitar el `409` de `/terminate`.
- `required: []` en el cuerpo de `POST /sessions`.
- Quitar `blocked` de `SessionStatus`.

**Arreglo esperado:**
- una tabla `(método, ruta) → (roles, owner-only, owner-only-for-role)` comparada por igualdad con el summary;
- el conjunto de estados por operación;
- la comparación exacta de los `required` y de los enum listados.

### A-01 · AMARILLO · `contracts/api/console.v2.yaml` (`Run.anonymized`) · Texto del summary cambiado por una guardia fusionada, sin precisión registrada

Solo una descripción difiere, porque `via_anonymizer` ya decía «true». El orquestador lo registra como P-T14-2.

### A-02 · AMARILLO · `console.v2.yaml` (`/exports` 201 `Content-Disposition`) · El patrón no garantiza «solo UUID»

`[0-9a-f-]{36}` admite 36 guiones, y NFR10.4 dice «(solo UUID)». Hay que apretarlo a 8-4-4-4-12.

### A-03 · AMARILLO · `docs/loop/bitacoras/U01-T14.md:101` · Rojo resumido y commits de antes del rebase

El rojo va resumido, no literal, y la bitácora cita `0b0745a` y `95effb4`, que ya no existen tras el rebase.

## Tareas candidatas

- `checks/auth_surface.py` (T15) debería fijar los roles y la propiedad de cada operación frente a una huella versionada. El orquestador lo registra como K-29.

Estado final: el worktree quedó limpio y la copia temporal, borrada.

```
VEREDICTO: NO-VERDE
NARANJA|contracts/tests/contracts/test_console.py:307|Las pruebas no fallan si se amplian roles u owner-only por ruta (investigador exporta: 54 passed), ni con otras mutaciones de estados y cuerpos
AMARILLO|contracts/api/console.v2.yaml:Run.anonymized|Texto del summary cambiado por la guardia E8 sin precision registrada para el humano
AMARILLO|contracts/api/console.v2.yaml:/reports/{report_version_id}/exports|El patron de Content-Disposition no garantiza solo UUID
AMARILLO|docs/loop/bitacoras/U01-T14.md:101|Rojo resumido, no literal; cita commits de antes del rebase
INFORME: docs/loop/revisiones/U01-T14/ronda-1.md
```
