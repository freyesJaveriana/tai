# Ronda 3 (corta) — U02-T01

> Ronda autorizada por el humano como excepción a ML-5 (2026-11-26), con alcance limitado a F-06 y F-07.

VEREDICTO: VERDE

F-06 está cerrado y F-07 también, salvo dos huecos menores en `RUN --mount` que dejo como AMARILLO. No hay regresiones. El worktree quedó limpio antes y después (`git -C /workspace/.worktrees/U02-T01 status --porcelain` sin salida). No hice llamadas de red y no ejecuté el punto de entrada fuera de pytest.

## Alcance del diff contra 8bd1176
`git -C /workspace/.worktrees/U02-T01 diff --stat 8bd1176 03e57dc` muestra tres archivos:
- `deploy/tests/test_dockerfile.py`;
- `docs/loop/bitacoras/U02-T01.md`;
- `docs/loop/bitacoras/U02-T01-ronda-2-respuesta.md`.

Los dos últimos son bitácora. No se tocó el Dockerfile, `src/` ni ningún umbral, así que no hay desborde. El rojo `aa37e17` solo añade pruebas (95 líneas en `test_dockerfile.py`).

## Criterios, verificados por mí
| # | Comando que corrí | Resultado |
|---|---|---|
| Suite | `uv run --frozen --offline --directory /workspace/.worktrees/U02-T01/deploy pytest --cov=veridicus_demo --cov-branch --cov-fail-under=100 -q` | pasa: `96 passed in 1.45s`, `entrypoint.py 116 stmts, 30 branches, 100%` |
| Tipos | `uv run … mypy --strict src tests` | `Success: no issues found in 7 source files` |
| Lint | `uv run … ruff check .` | `All checks passed!` |
| Formato | `uv run … ruff format --check .` | `7 files already formatted` |
| Dockerfile real | `check_copy_from_pinned(t.DOCKERFILE.read_text())` en memoria | `[]`: sigue cumpliendo |

## F-06, cerrado
`_instructions` ahora separa con `re.split(r"\s+", …, maxsplit=1)`. Lo comprobé de dos formas.

**Mutante en memoria:** con `mock.patch.object(t, '_instructions', <la versión vieja con partition(" ")>)`, las cuatro pruebas nuevas de F-06 fallan. Los controles muerden el defecto.

**Mis propios casos:**
- `USER \t 0:0` y `user\t0` dan «USER final es root».
- `COPY \` seguido de `\t--from=img:1` en la línea siguiente falla.
- `COPY\t--chown=1:1\t--from=img:1` falla.
- `COPY\t--chown=1\t.env\t/app/` falla.
- Con `\x0b` o `\x0c` como separador, `splitlines` corta la línea en dos y sale «USER no numérico». Falla en cerrado.

## F-07, cerrado (salvo lo que dejo como AMARILLO)
- **ONBUILD:** `ONBUILD ONBUILD COPY --from=img:1` falla por la recursión.
- **Etapas posteriores:** `--from=1` antes del segundo `FROM` falla, y `--from=2` hacia una etapa futura también.
- **Lo que debe pasar, pasa:**
  - una etapa nombrada antes de usarse, también con otra caja (`AS Build` / `--from=BUILD`);
  - una etapa con `\tAS\t`;
  - un `FROM --platform=… AS b`;
  - un `RUN --mount=from=…@sha256:<64>`.

## Regla de números de etapa (`--from=N`), mi juicio: correcta
Una etapa numerada cuenta como interna solo si su índice es menor que la cantidad de `FROM` ya vistos (`int(N) < declared`). Eso coincide con la numeración desde 0 que usa Docker, y `01` se lee como 1, igual que en Docker.

Deja pasar un único caso dudoso: que una etapa se cite a sí misma (`FROM x` y luego `COPY --from=0`), y lo mismo por nombre (`FROM x AS a` y luego `--from=a`). Eso no deja colar una imagen externa; BuildKit lo rechaza al construir por dependencia circular, aunque esto no lo comprobé.

Los dígitos Unicode que Python acepta como número (`isdigit`) no forman una referencia de imagen válida, así que tampoco abren un hueco. La regla falla en cerrado y es coherente con la de nombres.

## Hallazgos
### F-08 · AMARILLO · `deploy/tests/test_dockerfile.py:62-64` · Dos formas de `--mount from=` que no se reconocen
Las dos devuelven `[]` en mi prueba en memoria:
- `RUN --mount=type=bind,FROM=img:1,target=/x true`: la clave en mayúsculas.
- `RUN --mount=type=bind,"from=img:1",target=/x true`: el campo entre comillas, al estilo CSV.

No verifiqué si BuildKit acepta esas dos formas. Creo que pasa la clave a minúsculas y lee el valor como CSV, pero no lo comprobé. Hoy el Dockerfile real no tiene ningún `--mount`. El arreglo sería comparar la clave sin distinguir mayúsculas y quitar las comillas de cada campo. Es el resto de un hallazgo AMARILLO y no bloquea.

## Tareas candidatas
- La que ya estaba: `hadolint` en la CI (U02-T03) como segunda barrera.

## No verificado
- El comportamiento real de BuildKit en tres casos: las referencias a etapas posteriores, las citas de una etapa a sí misma y las formas de F-08.
- El build real y Trivy.

```
VEREDICTO: VERDE
AMARILLO|deploy/tests/test_dockerfile.py:62|RUN --mount con FROM= en mayúsculas o con el campo entre comillas no se reconoce
INFORME: docs/loop/revisiones/U02-T01/ronda-3.md
```
