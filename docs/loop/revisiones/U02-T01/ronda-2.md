# Ronda 2: U02-T01

VEREDICTO: NO-VERDE

Los cinco hallazgos de la ronda 1 están cerrados. Volví a correr CA-1 a CA-5 y todos pasan. El veredicto es NO-VERDE por un solo NARANJA nuevo, F-06: las comprobaciones del Dockerfile dejan pasar una instrucción separada por tabulador. El Dockerfile real cumple; lo que tiene el hueco es la prueba que lo vigila. El worktree quedó limpio (`git -C /workspace/.worktrees/U02-T01 status --porcelain` vacío, antes y después).

## Criterios de aceptación, verificados por mí

| # | Comando que corrí | Resultado |
|---|---|---|
| CA-1 | `uv run --frozen --offline --directory /workspace/.worktrees/U02-T01/deploy pytest tests/test_entrada.py -q` | pasa: `10 passed in 0.35s` |
| CA-2 | `uv run --frozen --offline --directory …/deploy pytest tests/test_entrypoint.py --cov=veridicus_demo --cov-branch --cov-fail-under=100 --cov-report=term-missing` | pasa: `41 passed in 1.36s`, `entrypoint.py 116 stmts, 30 branches, 100%` |
| CA-3 | `uv run --frozen --offline --directory …/deploy pytest tests/test_dockerfile.py -q` | pasa: `23 passed in 0.04s`, sin xfail. Tarda milisegundos porque solo lee archivos |
| CA-4 | `mypy --strict src tests`, luego `ruff check .`, luego `ruff format --check .` | los tres en 0 |
| CA-5 | `uv run --frozen --offline --directory …/libs/incoherence_analyzer --extra cli pytest tests/e2e --no-cov -q` | pasa: `4 passed` |
| CA-5 | los tres `bash /workspace/.worktrees/U02-T01/scripts/check-no-*.sh /workspace/.worktrees/U02-T01` | `0 apariciones` en cada uno |
| CA-5 | `git -C /workspace/.worktrees/U02-T01 diff --stat origin/bolt/b4-demo -- libs contracts` | vacío |
| CA-5 | `grep -rnoP "sk-[A-Za-z0-9_-]{6,}" /workspace/.worktrees/U02-T01/deploy --exclude-dir=.venv` | una sola aparición, la clave canario de `tests/support.py:17` |

## Cierre de F-01 a F-05

- **F-01, cerrado.** `Dockerfile:17` copia uv con `COPY --from=ghcr.io/astral-sh/uv:0.13.9@sha256:d3b601f0…` y ya no queda ningún `pip install`. La prueba es estricta y exige ese digest. Hay controles negativos para: sin digest, el marcador, `latest` y 63 caracteres hex. El digest lo tomé como dado.
- **F-02, cerrado.** `.dockerignore` ya trae los cinco patrones de secretos. El control negativo comprueba cada uno por separado (`len(problems) == 8`).
- **F-03, cerrado.** El escáner ya pasa por los cuatro mensajes fijos y por los rótulos con 0, 1, 2 y 5 hallazgos.
- **F-04, cerrado, y lo comprobé con la clave puesta.** Con `uv run … python -c "import os; print('VERIDICUS_ANTHROPIC_API_KEY' in os.environ)"` sale `True`: la clave real está en el entorno de las pruebas. Aun así pasa `test_the_test_environment_never_carries_the_real_provider_key`, así que el fixture autouse de `conftest.py` sí la quita en cada prueba. Las otras claves que leen los perfiles (`VERIDICUS_OPENAI_API_KEY`) no las usa el perfil `demo-anthropic`.
- **F-05, cerrado.** `_count` da «1 hallazgo» y «N hallazgos». Lo prueban los casos 0, 1, 2 y 11.

**Prueba primero:** el rojo `935cf38` solo trae pruebas. Comparé las pruebas entre `935cf38` y `7674d12`: se quitó el xfail y se borró la prueba de transición del marcador. Las demás diferencias son de formato. Ninguna aserción se debilitó.

## Hallazgos

### F-06 · NARANJA · `deploy/tests/test_dockerfile.py:30` · Una instrucción separada por tabulador evade las cuatro comprobaciones

`_instructions` separa la instrucción del resto solo por espacio (`stripped.partition(" ")`). El parser de Dockerfile acepta cualquier espacio en blanco, también el tabulador, así que `USER<TAB>0` es una instrucción válida que deja la imagen corriendo como root. Para el parser de la prueba, en cambio, esa línea no es un `USER`.

Lo comprobé en memoria con `uv run --frozen --offline --directory …/deploy python -c "…import test_dockerfile as t…"`:
- `check_final_user('FROM x AS a\nUSER 10001:10001\nUSER\t0\n')` devuelve `[]`: la imagen quedaría como root y la prueba no lo ve.
- `check_copy_from_pinned('…COPY\t--from=img:1 /a /b\n')` devuelve `[]`: un `COPY --from` externo sin digest pasa.
- `check_from_pinned('FROM\tpython:3.12-slim AS a\n')` devuelve `[]`.
- `check_no_forbidden_copy('…COPY\t.env /app/.env\n')` devuelve `[]`.

Hoy el Dockerfile real no tiene tabuladores (`grep -cP "\t" …/Dockerfile` da `0`), así que ningún criterio falla. Pero es la guardia de CA-3 y de la regla «sin root, fijado por digest» de team.md, y deja pasar una sintaxis válida. Los controles negativos solo prueban la forma con espacio.

**Arreglo:** separar con `re.split(r"\s+", stripped, maxsplit=1)` y añadir un control negativo con tabulador para `USER` y otro para `COPY --from`.

### F-07 · AMARILLO · `deploy/tests/test_dockerfile.py:49` · Otras formas de traer una imagen externa sin digest

Hay más formas de traer una imagen externa sin digest que `check_copy_from_pinned` no mira. Las tres devuelven `[]` en mi prueba en memoria:
- `ONBUILD COPY --from=img:1 …`;
- `RUN --mount=type=bind,from=img:1,…`;
- `COPY --from=uv` antes de una etapa `AS uv` que se declara más abajo. El conjunto de etapas sale de todo el archivo, no solo de las anteriores. No verifiqué si BuildKit resolvería ese nombre como imagen o como la etapa posterior.

Por otro lado, la comprobación sí falla en cerrado con `${VAR}`, con la instrucción en minúsculas, con `--chown` delante de `--from` y con líneas continuadas.

## Tareas candidatas

- Que la CI (U02-T03) corra `hadolint` con DL3002 (último `USER` root) y DL3007, como segunda barrera de las guardias estáticas.

## No verificado

- El build real, `hadolint` y Trivy: les tocan a la CI.
- Los digests de python y de uv: los tomé como dados.
- Cómo resuelve BuildKit una referencia a una etapa posterior (F-07).
- No ejecuté el punto de entrada fuera de pytest ni hice ninguna llamada de red.

```
VEREDICTO: NO-VERDE
NARANJA|deploy/tests/test_dockerfile.py:30|Una instrucción separada por tabulador evade las cuatro comprobaciones
AMARILLO|deploy/tests/test_dockerfile.py:49|Otras formas de traer una imagen externa sin digest
INFORME: docs/loop/revisiones/U02-T01/ronda-2.md
```
