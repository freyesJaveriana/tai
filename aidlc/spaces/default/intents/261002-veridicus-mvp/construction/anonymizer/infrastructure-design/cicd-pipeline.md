# Pipeline de CI/CD — U10 anonymizer

**Revisión 2 (2026-11-23): segunda pasada por el cambio 01, la adenda 02 y el NFR Design revisión 2.**
Sustituye a la revisión 1 del 2026-10-03.
- **Qué cambia.** Sale el PR de habilitación (`anonymizer-enable-gate.yml`, §3 «Retirado»): el proxy forma
  parte del despliegue base (D1). Las políticas de red, el `Corefile` y el endurecimiento pasan a
  `deploy-level0.yml` de U2. Entra el módulo `libs/anonymizer/` con sus adaptadores, la prueba de 0 fugas
  con el NER real en la CI y una puerta de rendimiento con el reporte medido en la máquina de desarrollo.
- **Numeración.** §1–§6 conservan su tema.

**Insumos.** De `nfr-design/` de esta unidad: security-design §2–§4, §6, §8, §10 y §12 (pruebas de
propiedades, verificación final, riesgo residual, cabeceras, *canary*, ADR e import-linter),
reliability-design §1–§5 (fallo cerrado con 0 peticiones, 1 petición tras el envío, sondas,
restauración), performance-design §1, §2, §5 y §6 (mediciones y prueba de NFR8), scalability-design §2,
§4 y §5 (mamparo, memoria, solo CPU), observability-design §1–§3 y §6 (*canary*, cardinalidad y panel) y
logical-components §2 y §5. También: functional-spec (escenarios E1–E34 y F9), components (AnalyzerCli
y Anonymizer), C20, C21, C22 y C25 de contract-summary, los comandos de §5 de
`nfr-requirements/tech-stack-decisions.md`, `platform/nfr-design/security-design.md` de U2 (§2.3, §8,
§9, §10 y §11) e `infrastructure-specification.md` de esta carpeta. `## Testing Posture` y
`## Deployment` de `team.md`.

## 1. Principios

- Todos los *workflows* declaran `permissions: contents: read`, fijan las acciones por SHA y no tienen
  `kubeconfig` ni claves de proveedores. Solo el *job* `build` tiene `packages: write`, y solo en `main`.
- Ninguna prueba llama a un proveedor real, exige GPU ni abre conexiones fuera de `localhost`
  (`pytest-socket`, NFR2.1). El único paso con red de U10 es el aprovisionamiento del NER, que corre
  **antes** de las pruebas, verifica el `sha256` y no lleva datos del proyecto (IDS-U10-07).
- Las pruebas de las guardias de AUTONOMIA-04 y de los contratos C20 y C21 se escriben primero y se ven en
  rojo antes de implementar (`team.md`). Ninguna prueba de los niveles 0 y 1 se reintenta; una inestable
  va a cuarentena con un *issue* y su umbral nunca baja.
- El plan de B10 sigue el orden de R14: módulo, `FakeTransport` y adaptador de Anthropic, después el
  proxy y F9, y al final los adaptadores de Google y OpenAI (functional-spec §7).

## 2. *Workflows* y puertas

| *Workflow* | Se dispara con | *Job* | Comando y umbral (AUTONOMIA-02) | Bloquea |
|---|---|---|---|---|
| `anonymizer-proxy.yml` | `libs/anonymizer/**`, `services/anonymizer-proxy/**`, `contracts/**`, `scripts/check-provider-adr.py`, `docs/adr/**`, `deploy/models.lock` | `lint` | `ruff check` y `ruff format --check` con 0 hallazgos; `mypy --strict` con 0 errores en los dos paquetes; `uv run --directory libs/anonymizer lint-imports` con 0 contratos rotos y cada control negativo fallando; `hadolint` sin errores | Sí |
| | | `lockfile` | `uv run --directory libs/anonymizer pytest -m lockfile`: 0 paquetes `nvidia-*` o `triton` (NFR2.2) | Sí |
| | | `test-level0` | `uv run --directory libs/anonymizer pytest -m "not integration and not perf"` y lo mismo en `services/anonymizer-proxy`, con `pytest-socket`: 0 peticiones en cada rama anterior al envío, exactamente 1 tras el envío, 5 cabeceras salientes, proyección del esquema, `413` por `Content-Length`, quinta petición `503` en < 50 ms, `/healthz` y `/readyz` con 4 llamadas en curso (IDS-U10-04), Hypothesis de NFR1.3 con el NER diminuto; 0 fallos | Sí |
| | | `guards` | `uv run --directory libs/anonymizer pytest --cov-branch --cov-config=.coveragerc-guards` y lo mismo en `services/anonymizer-proxy`: 100 % de ramas (NFR13.2) | Sí |
| | | `limits` | `uv run --directory libs/anonymizer pytest -m limits`: (a) 250 000 caracteres caben en `anonymizer_request_max_bytes`; (b) el presupuesto con 270 s cubre la meta de 20 s (NFR-U10-04) | Sí |
| | | `provider-adr` | `uv run --directory libs/anonymizer python ../../scripts/check-provider-adr.py`: código 0; en la primera rebanada solo el ADR de Anthropic; los controles negativos fallan (NFR1.2) | Sí |
| | | `test-level1` | Paso previo: `scripts/fetch-models.sh --only ner` con verificación del `sha256` de `models.lock` y caché de Actions por ese `sha256`. Después: `uv run --directory libs/anonymizer pytest -m "integration and leakage" --residual-report out/anonymizer-residual.json` con **0 fugas** (NFR1.3), y `uv run --directory services/anonymizer-proxy pytest -m integration`: *canary* con 0 apariciones en logs, métricas y excepciones, TLS 1.1 y certificado ajeno sin enviar el cuerpo, `/readyz` sin conexiones externas, proceso sin escritura | Sí |
| | | `coverage` | `--cov-fail-under=80` en `libs/anonymizer` y `services/anonymizer-proxy` (NFR13.1) | Sí |
| | | `audit` | `pip-audit` sin `HIGH`+ con corrección; `gitleaks` con 0 hallazgos; comprobación de datos sintéticos de U1 sobre `libs/anonymizer/tests/`, `libs/anonymizer/testing/` y `services/anonymizer-proxy/tests/` con 0 hallazgos (NFR12.1) | Sí |
| | | `build` | Imagen sin root (UID ≠ 0) y sin el NER dentro; Trivy con `--exit-code 1 --severity HIGH,CRITICAL --ignore-unfixed`; en `main` publica `veridicus-anonymizer-proxy:<sha>` | Sí |
| `anonymizer-perf-gate.yml` (nuevo) | PR que toca `libs/anonymizer/domain/**`, `application/**`, `data/**`, `services/anonymizer-proxy/src/**` o la entrada `ner` de `deploy/models.lock` | `perf-report` | `scripts/check-anonymizer-perf.py out/anonymizer-perf.json`: el reporte adjunto al PR (mismo mecanismo que la puerta de nivel 2 de U11) declara el SHA del *commit* y el `sha256` del NER del PR, y cumple p95 ≤ 20 s con 250 000 y ≤ 15 s con 186 000, linealidad ≤ 33,5 y ≤ 25, sobrecosto ≤ 50 ms, RSS ≤ 1,5 GiB, crecimiento ≤ 10 % tras 50 peticiones y arranque ≤ 60 s | Sí |
| `deploy-level0.yml` (de U2) | `deploy/**`, `scripts/**`, `.github/**` | `render`, `policies`, `coredns`, `rules` | Lo que fija U2. De U10: el render incluye el proxy; `check-coredns-domains.sh` ejecuta F9 contra `allowed-domains.v1.yaml`; `check-config-copy.sh` compara el SHA-256 del panel (IDS-U10-08); `promtool test rules` sobre `veridicus-anonymizer` con un caso que dispara y otro que no por alerta | Sí |

La medición de rendimiento corre en la máquina de desarrollo, en CPU, con
`uv run --directory services/anonymizer-proxy pytest -m perf --perf-report out/anonymizer-perf.json`
(performance-design: «todo se mide en la máquina de desarrollo»). No corre en la CI porque los
*runners* no tienen la CPU de esa máquina y sus cifras no serían comparables.

## 3. PR de habilitación · Retirado

Retirado: el proxy ya no se habilita por PR (D1). Con él se van `anonymizer-enable-gate.yml`,
`check-anonymizer-enable.py` y los hallazgos R-01 y R-05 de la revisión 1. La evidencia que pedía queda
repartida así:

| Evidencia | Dónde se produce ahora | Umbral |
|---|---|---|
| ADR del proveedor | *Job* `provider-adr` (§2) | Código 0 |
| Fugas y riesgo residual | *Job* `test-level1` (§2); el ADR cita `out/anonymizer-residual.json` | 0 fugas; tasas informativas (NFR1.10) |
| Rendimiento y memoria | `anonymizer-perf-gate.yml` (§2) | Las cifras de la tabla |
| Nivel 2 con el anonimizador en el camino | U11, en B11: la CLI con el perfil de Anthropic y el módulo en el mismo proceso, en la máquina del humano; U10 aporta la cuenta de valores sembrados antes de restaurar y `altered_markers_count` | Umbrales de U11 (NFR4.1, NFR5.1, NFR5.2); no ejercita la red del clúster, que cubre §4 |
| Carga de NFR8 | Tras el despliegue, con un perfil comercial (performance-design §6) | 0 respuestas `503` por saturación y 0 `OOMKilled` |

## 4. Despliegue

| Paso | Qué pasa | Quién |
|---|---|---|
| 1 | `create-secrets.sh` lee el `.env` y escribe el manifiesto de `veridicus-provider-keys` fuera del repositorio; termina con código ≠ 0 si falta la clave de alguna `api_key_ref` externa (IDS-U10-06) | Humano revisa, aplica y borra el archivo |
| 2 | `fetch-models.sh` deja la entrada `ner` en el volumen de modelos con su `sha256` | Humano |
| 3 | PR del Bolt fusionado en `main` protegida, con la evidencia de §2 | Humano (aprobación registrada) |
| 4 | Antes del módulo 8, aplicación manual del chart ya fusionado; después, Argo CD sincroniza | Humano / Argo CD |
| 5 | El pod pasa la `startupProbe` (≤ 120 s) y `/readyz` responde 200; `scripts/smoke.sh <url-base>` con código 0 (con un perfil comercial, su turno sintético pasa por el proxy); verificación manual de U2 (§2.4 de su NFR Design) | Humano |

Ningún *workflow* ni *script* aplica cambios al clúster (AUTONOMIA-01, `check-no-cluster-apply.sh` de
U2). El proxy usa `RollingUpdate` con `maxUnavailable: 0`: el pod nuevo solo recibe tráfico cuando
`/readyz` responde 200, y el viejo termina sus llamadas en curso dentro de 290 s.

## 5. Reversión

| Qué falló | Cómo se revierte |
|---|---|
| `smoke.sh` o la verificación manual tras desplegar | `git revert` del *commit* del Bolt y nueva sincronización (o aplicación manual antes del módulo 8); vuelve el digest anterior |
| El pod nuevo no pasa `/readyz` (dato, NER, perfil o clave inválidos) | No recibe tráfico y el anterior sigue atendiendo; se corrige por PR o se revierte |
| El proveedor incumple su ADR | PR que saca sus modelos de `provider-capabilities.v1.yaml` y los perfiles que los usan; hasta su fusión, el analista usa un perfil local |
| Una versión de reglas o del NER causa fugas o cierres | `git revert` del PR de datos o de la entrada `ner`; mientras tanto, nada sin seudonimizar salió (fallo cerrado) |
| Una clave filtrada | El humano la revoca en el proveedor, pone la nueva en el `.env`, ejecuta `create-secrets.sh`, aplica el Secret y reinicia el pod según el runbook (nunca un *script*) |

## 6. Entornos y secretos

| Entorno | Qué corre de U10 |
|---|---|
| CI | Niveles 0 y 1, cobertura, ADR, imagen y render; sin clúster ni claves; red solo para aprovisionar el NER |
| Máquina del humano (64 GB, solo CPU) | El proxy en Minikube con el digest de la CI, y la CLI de U11 con el módulo en el mismo proceso |
| ZINE | Nada de U10: allí la CLI solo usa perfiles locales |

| Secreto | Dónde vive | Quién lo usa |
|---|---|---|
| Claves de los proveedores | `.env` no versionado → `create-secrets.sh` → `veridicus-provider-keys` | Solo el proxy, por `envFrom` |
| Claves de los proveedores para la CLI | Variables de la máquina del humano, desde el mismo `.env` | La CLI de U11 en esa máquina |
| `GITHUB_TOKEN` con `packages: write` | GitHub Actions, *job* `build` en `main` | Publicar la imagen |

`gitleaks` en pre-commit y en la CI, `no-inline-secrets` de U2 y la prueba *canary* (E34) impiden que una
clave aparezca en el repositorio, en un manifiesto o en un log.
