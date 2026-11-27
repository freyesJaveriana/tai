# Ronda 2 — U02-T04

VEREDICTO: VERDE

Los cuatro hallazgos de la ronda 1 (F-01 a F-04) quedan cerrados. CA-1 y CA-2 pasan con mi propia ejecución. Todos los mutantes mueren y las sondas de F-03 ahora fallan como deben. El diff no sale del alcance. Lo nuevo del README coincide con el código real. Solo queda un AMARILLO, que no bloquea.

## Criterios de aceptación, verificados por mí
| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| CA-1 | Prueba de la guía | `uv run --frozen --offline --directory /workspace/.worktrees/U02-T04/deploy pytest tests/test_readme.py -q` | 54 passed in 0.04s |
| CA-2a | Suite, cobertura 100 % de ramas | `uv run --frozen --offline --directory /workspace/.worktrees/U02-T04/deploy pytest --cov=veridicus_demo --cov-branch --cov-fail-under=100 -q` | 901 passed in 10.75s, 100,00 % |
| CA-2b | mypy | `uv run … mypy --strict src tests` | sin errores, 19 archivos |
| CA-2c | ruff check | `uv run … ruff check .` | All checks passed |
| CA-2d | ruff format | `uv run … ruff format --check .` | 29 files already formatted |
| CA-2e | Los cuatro `check-no-*.sh` | `bash /workspace/.worktrees/U02-T04/scripts/check-no-<x>.sh /workspace/.worktrees/U02-T04`, una llamada por script | los cuatro dan `0 apariciones` |
| CA-2f | Alcance | `git -C … diff --stat origin/bolt/b4-demo -- libs contracts .github deploy/demo-analyzer/{job,kustomization,namespace,networkpolicy,serviceaccount}.yaml deploy/demo-analyzer/entrada scripts deploy/images deploy/src deploy/pyproject.toml deploy/uv.lock` | vacío |
| Rojo | Commit del rojo antes que el verde | `git -C … diff --stat de13e0c eaf79e6` y `de13e0c fd59b84` | el rojo eaf79e6 solo toca `test_readme.py` y `usuario-guion-bajo.md`; `readme_checks.py` y el README cambian solo en el verde fd59b84 |
| Worktree | Limpio | `git -C … status --short` | vacío |

Que fallen exactamente 15 pruebas en eaf79e6 lo dice la bitácora. No lo comprobé en ejecución: habría que hacer checkout de ese commit, y no edito el worktree. Sí cuadra con lo que cambia cada commit.

## Cierre de los hallazgos de la ronda 1
| Hallazgo | Estado | Cómo lo comprobé |
|---|---|---|
| F-01 · NARANJA | Cerrado | **Forma del usuario:** `README.md:27-28` dice «letras, cifras y guion, sin guion bajo», igual que `crear-pull-secret-ghcr.sh:33` (`^[A-Za-z0-9-]+$`). **Forma del token:** «más guion bajo», igual que `:37` (`^[A-Za-z0-9_-]+$`). **Relleno:** el valor literal `relleno` (`:103-104`) cumple las dos regex. **Orden:** el script 2 va antes de `demo-analyzer.sh`. |
| F-02 · NARANJA | Cerrado | **NetworkPolicy:** `README.md:77-81` coincide con `networkpolicy.yaml`: 443 hacia `0.0.0.0/0` sin los rangos privados, DNS hacia `kube-dns`, y `deny-all` con `podSelector: {}` en el namespace. **Anonimizador:** el destino Anthropic y la seudonimización los atribuye al anonimizador, como dice el comentario de `networkpolicy.yaml:14`. **Kyverno:** que corre solo en la CI es cierto; solo aparece en `deploy-level0.yml`, no en `deploy/demo-analyzer/`. |
| F-03 · AMARILLO | Cerrado | Repetí mis sondas de la ronda 1 (resultados abajo); ahora fallan todas como deben. |
| F-04 · AMARILLO | Cerrado | **Plan A:** PAT clásico con `read:packages` (`:93-94`); un token `ghp_…` cumple la regex del token. **Plan B:** se construye antes del script 3 (`:98`). **Reversión:** `minikube image rm ghcr.io/freyesjaveriana/veridicus-analyzer-cli:<etiqueta>` (`:70-71`). |

## Mutantes (en memoria, `mock.patch.object` dentro de `python -c` con `uv run … --directory deploy`)
| Mutante en `readme_checks` | Resultado |
|---|---|
| Sin mutante (control) | 54 passed |
| `_PATH` no detecta nada | 7 fallan, muerto |
| `_PATH` vuelve a la regex de la ronda 1 | 5 fallan, muerto |
| `_BARE_SCRIPT` no detecta nada | 1 falla, muerto |
| `_LATEST` no detecta nada | 1 falla, muerto |
| `_KUBECONFIG` no detecta nada | 1 falla, muerto |
| `_SECRET_SHAPES = ()` | 9 fallan, muerto |
| `gh[pousr]_` vuelve a `ghp_` | 4 fallan (`ghs_`, `gho_`, `ghu_`, `ghr_`), muerto |
| `REQUIRED_SCRIPTS` sin `crear-pull-secret-ghcr.sh` | 3 fallan, muerto |
| `_HEADING` no detecta nada | 43 fallan, muerto |

Tres reglas están escritas en línea dentro de `violations` y no se pueden aislar como mutante: la del guion bajo, la del encabezado múltiple y la continuación de línea de `minikube start`. Las cubren sus controles exactos.

## Sondas de evasión sobre `violations(ok.md + texto)`
| Sonda | Ronda 1 | Ahora |
|---|---|---|
| `scripts/otra/nada.sh` | `[]` | falla la regla de rutas |
| `.github/workflows/no-existe.yml` | `[]` | falla la regla de rutas |
| `redeploy/demo-analyzer/job.yaml` | `[]` | falla la regla de rutas |
| `ghs_…` | `[]` | falla la regla de claves |
| `minikube start \` con `--cni=calico` en la línea siguiente | falso positivo | `[]` |
| `(scripts/otra/x.sh)` | — | falla la regla de rutas |
| README real | — | `[]` |
| `bash ./scripts/humano/no-existe.sh` | — | `[]`: se escapa (F-01 de esta ronda) |
| Usuario y guion bajo en dos líneas | — | `[]`: se escapa (F-01 de esta ronda) |
| «El usuario no admite guion bajo.» | — | falla: falso positivo (F-01 de esta ronda) |

## Hallazgos
### F-01 · AMARILLO · deploy/tests/readme_checks.py:28 y :63-66 · Quedan huecos menores en dos reglas
- **Rutas con `./` delante.** Una ruta escrita como `./scripts/…` no se comprueba: la barra que va detrás del punto bloquea la coincidencia, y `_BARE_SCRIPT` también la excluye. Arreglo propuesto: quitar `^./` antes de buscar, o aceptar un `./` opcional en `_PATH`, con un control negativo.
- **Regla del guion bajo.** Busca palabras sueltas en una misma línea. Por eso marca como error «no admite guion bajo» y deja pasar la frase si se parte en dos líneas. Arreglo propuesto: comparar con la regex real del script (`crear-pull-secret-ghcr.sh:33`) o anclar la frase exacta que se exige.

Hoy ninguno de los dos afecta al README real.

## No verificado
- El conteo de 15 fallos del rojo eaf79e6, explicado arriba.
- Que `minikube image build`, `minikube image rm` y Calico se comporten así en la VM real. No hay VM, y la documentación por MCP solo cubre la API de Claude.
- Que GHCR no acepte PAT de grano fino: lo sé de memoria, no lo comprobé con documentación.

## Tareas candidatas (fuera de alcance, siguen desde la ronda 1)
- Que `demo-analyzer.sh` no exija `veridicus-ghcr` en el plan B.
- Que `demo-analyzer.sh:50` no lea `.items[0]` justo después de un `kubectl delete job` que borra en segundo plano: podría tomar el código de un pod de la corrida anterior.

```
VEREDICTO: VERDE
AMARILLO|deploy/tests/readme_checks.py:28|Las rutas con ./ delante no se comprueban, y la regla del guion bajo es una heurística por línea (falso positivo y evasión en dos líneas)
INFORME: docs/loop/revisiones/U02-T04/ronda-2.md
```
