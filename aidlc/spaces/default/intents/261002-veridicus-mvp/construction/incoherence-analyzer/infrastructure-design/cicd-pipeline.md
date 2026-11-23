# Pipeline de CI/CD — U11 incoherence-analyzer

**Revisión 1 (2026-11-23): primera pasada.** U11 nació con el cambio 01 (DT27) y no tiene revisión anterior
de esta etapa.
- **Tipo `library`.** El archivo de etapa le pide a una `library` solo este documento y `traceability.json`
  (`produces_kinds`). U11 no despliega nada propio: no hay `infrastructure-specification.md` ni
  `monitoring-design.md`. Lo que un `service` pondría ahí y U11 sí necesita (la máquina donde corre la CLI,
  ZINE y la frontera de datos) va en §5–§7 (IDS-U11-01).
- **Supuesto de máquina.** Un solo equipo de 64 GB, solo CPU y sin máquina GPU, con WSL2 de 56 GB y Minikube
  de 50 GiB, como ya decidió U2 (IDS-U2-01; brief del 2026-11-22). U11 no cambia ninguna cifra de pods.
- **Preguntas.** Ninguna (`infrastructure-design-questions.md`): todo lo fijan las fuentes.

**Insumos.**
- De `nfr-design/` de esta unidad (revisión 1): `security-design.md` (security-design §1–§11 y NFRD-U11-01 a
  NFRD-U11-12), `performance-design.md` (performance-design §1–§8), `reliability-design.md`
  (reliability-design §1–§9) y `logical-components.md` (logical-components §1, §2, §4 y §5). No existen
  `scalability-design` ni `observability-design` para U11: no hay requisitos de escalabilidad ni de
  observabilidad propios, y lo que U11 aporta a NFR8 y NFR15 está en performance-design §6 y §7.
- `nfr-requirements/tech-stack-decisions.md` (D1, D2, D6, D7, §3, §5 y §6).
- `functional-design/functional-spec.md` (functional-spec: F9, F10, F12 y la tabla de fronteras de §7) y
  `functional-design/rules.md` (BR11.5, BR14.1–BR14.5).
- AnalyzerCli, IncoherenceAnalyzer y ModelGateway en `inception/domain-design/components.md` (components,
  tabla de fronteras).
- C6, C13, C14, C17, C19 v2, C21 y C25 de `inception/contract-design/contract-summary.md` (contract-summary).
- B11 de `inception/delivery-planning/bolt-plan.md` (definición de terminado, puntos 1–6).
- Infrastructure Design de U2 (`platform/infrastructure-design/`: `deploy-level0.yml`, `values-cpu.yaml`,
  `models.lock`, `fetch-models.sh`, IDS-U2-01 e IDS-U2-11) y de U10 (`anonymizer/infrastructure-design/`:
  IDS-U10-07 e IDS-U10-09).
- Mediciones M2 y M5 de `docs/validacion-zine/reporte.md` (servidor local y wheelhouse en ZINE).
- `## Testing Posture`, `## Deployment` y `## Code Style` de `team.md`; reglas de `project.md`.

## 1. Principios

- **La CI no despliega.** Los dos *workflows* de U11 declaran `permissions: contents: read`, fijan cada acción
  por SHA, no tienen `kubeconfig`, claves de proveedores ni `packages: write` (U11 no publica imagen ni
  paquete).
- **Sin red ni GPU en los niveles 0 y 1.** `pytest-socket` con `--disable-socket --allow-hosts=127.0.0.1`
  (performance-design §5): solo *loopback* para los servidores HTTP *fake*. La única descarga con red de U11 es
  el NER de U10 para el nivel 1, que corre **antes** de las pruebas, verifica su `sha256` y no lleva datos del
  proyecto (IDS-U11-10).
- **Guardias primero** (`team.md`, Ordering): las pruebas de los siete módulos guardia, de AUTONOMIA-03/04/05 y
  de los contratos C6, C13, C18, C19 y C21 se escriben y se ven en rojo antes de implementar; el plan de tareas
  de B11 lo cita (reliability-design §6).
- **Nada se reintenta para ocultar un fallo.** Una prueba inestable va a cuarentena con un *issue* enlazado; los
  umbrales y la cobertura nunca bajan para que una puerta pase.
- **AUTONOMIA-01.** Ningún *workflow* ni *script* de U11 aplica cambios al clúster ni envía trabajos a ZINE;
  los `.sbatch` los lanza el humano (BR14.4).

## 2. *Workflows* y puertas

Los dos *workflows* se disparan con **todo** PR y deciden por dentro si tienen trabajo, para que sus
comprobaciones puedan ser obligatorias en `main` protegida sin bloquear los PR que no las tocan (IDS-U11-07).
Corren en *runners* `ubuntu-24.04` de GitHub (x86_64, sin GPU), con caché de `uv` por el *hash* de cada
`uv.lock`.

| *Workflow* | *Job* | Comando y umbral (AUTONOMIA-02) | Bloquea |
|---|---|---|---|
| `analyzer.yml` | `changes` | `scripts/ci-paths.py analyzer` contra la base del PR: hay trabajo si cambia algo de `libs/incoherence_analyzer/**`, `libs/model_gateway/**`, `libs/execution_profiles/**`, `libs/integrity_policy/**`, `libs/anonymizer/**`, `contracts/**`, `config/**`, `evaluation/**`, los `scripts/check-*.py` de U11 o `.github/workflows/analyzer*.yml` | — |
| | `lint` | Por paquete, `uv run --directory libs/<paquete> ruff check` y `ruff format --check` (reglas `S`), `mypy --strict` y `lint-imports` con los cinco contratos de security-design §9: 0 hallazgos, 0 errores, 0 contratos rotos, y cada módulo de control negativo falla como se espera; `yamllint config/ evaluation/` sin errores | Sí |
| | `test-level0` | Por paquete, `uv run --directory libs/<paquete> pytest -m "not integration"` con `pytest-socket`: 0 fallos. Incluye la prueba compuesta con el NER diminuto de U10 (security-design §3), el armado del gateway y el fallo cerrado (§2), el *canary* con cada código 0, 2, 3, 4, 5 y 6 (§7), las comprobaciones AST de configuración y de reexportación (§9), la tabla de fronteras del README frente a security-design §1, el rendimiento de NFR3.2 (≤ 2 s, con margen 3× en la CI) y la memoria ≤ 512 MiB con `tracemalloc` (performance-design §4 y §8), y el máximo de 1 llamada concurrente (performance-design §6) | Sí |
| | `checks` | `scripts/check-profiles.py config/profiles.yaml` (NFR1.7), `scripts/check-dataset.py evaluation/synthetic/manifest.v1.yaml` (NFR4.11, NFR4.12), `scripts/check-thresholds.py` (umbrales iguales o más estrictos que NFR4), `scripts/check-sbatch.py evaluation/zine/` (IDS-U11-13), la búsqueda estática de `sbatch`, `ssh`, `scp` y `rsync` sobre `scripts/`, `evaluation/`, `libs/` y `.github/` (security-design §11), `git ls-files resultados-locales evaluation/zine/paquete` vacío, la comprobación de datos sintéticos de U1 sobre los `tests/` y `evaluation/` (NFR12.1) y `scripts/check-reports-dir.py` (IDS-U11-04): 0 hallazgos y cada control negativo falla | Sí |
| | `guards` | `pytest --cov --cov-branch --cov-report=json` por paquete y `scripts/check-guard-coverage.py`: 100 % de ramas en los siete módulos guardia de reliability-design §6 (NFR13.2) | Sí |
| | `coverage` | `--cov-fail-under=80` de líneas por paquete; exclusiones solo en `[tool.coverage.run] omit` (arnés y código generado), cada una nueva justificada en su PR (NFR13.1, NFR13.3) | Sí |
| | `test-level1` | Paso previo: `scripts/fetch-models.sh --only ner` con verificación del `sha256` de `deploy/models.lock` y caché de Actions por ese `sha256`. Después: `uv run --directory libs/incoherence_analyzer --extra cli pytest -m integration`: prueba compuesta con el NER real con **0 apariciones** de las entidades sembradas en `judge`, `verifier` y `verifier_permuted` y su control negativo con el puente de U10 (NFR1.3); comprobación de contexto de cada perfil local (tech-stack-decisions §3) | Sí |
| | `audit` | `uv run --directory libs/<paquete> pip-audit` sobre cada `uv.lock`: 0 `HIGH`/`CRITICAL` con corrección; `gitleaks detect --no-git --source libs/` y `--source evaluation/`: 0 hallazgos (NFR10.14) | Sí |
| | `package` | `uv build --wheel` de los cuatro paquetes; en un entorno virtual limpio, `pip install --no-index --find-links dist/`, `veridicus --version` con código 0 y una prueba que lee `prompt.v1.md` y los esquemas con `importlib.resources` y compara el SHA-256 del *prompt* con el `prompt_sha256` de `config/profiles.yaml` (NFR5.4) | Sí |
| | `wheelhouse` | La wheelhouse de ZINE armada como en §6 (IDS-U11-03): 0 ruedas de `torch`, `nvidia-*`, `triton` o `libs-anonymizer`; instalación con `pip install --no-index --find-links` dentro de `python:3.12-slim` fijado por digest con `docker run --network none`; `veridicus --version` con código 0 y, como control negativo, `veridicus analyze` con un perfil comercial de prueba termina con código 3 y 0 conexiones (IDS-U11-02) | Sí |
| | `gate` | Depende de todos los anteriores; verde si todos pasaron, o si `changes` no encontró trabajo. Es la única comprobación obligatoria de este *workflow* (IDS-U11-09) | Sí |
| `analyzer-level2-gate.yml` | `check` | `scripts/check-level2-report.py` (§4): sin cambios en las rutas de IA, verde; con cambios, exige un reporte de nivel 2 válido del árbol del PR. Se dispara también con cada etiqueta `analyzer-v*` | Sí (nivel 2) |
| `secrets-scan.yml`, `semgrep.yml`, Dependabot (de U2) | — | Lo que fija U2. U11 añade a Dependabot el ecosistema `pip` de cada uno de sus cuatro paquetes | `gitleaks` sí; Semgrep y Dependabot no |

Ningún *job* tiene más de 30 minutos (`test-level1`, 45 por la primera descarga del NER). `concurrency`
cancela la corrida anterior del mismo PR.

## 3. Comprobaciones de nivel 0 propias de la CI

| Comprobación | Qué falla | Origen |
|---|---|---|
| `scripts/check-sbatch.py` | Un `.sbatch` con `--gres=gpu`, sin `--time` ≥ `run_deadline_final_s` × muestras del trabajo, sin `--cpus-per-task` o con `--mem` menor que la suma de los GGUF de su manifiesto más 8 GiB | performance-design §5; IDS-U11-13 |
| Búsqueda estática de AUTONOMIA-01 | `sbatch`, `ssh`, `scp` o `rsync` fuera de un comentario o de una cadena de instrucciones al humano | security-design §11; BR14.4 |
| `evaluation/zine/` | Otro archivo rastreado que no sea `.sbatch`, `empaquetar.py` o `manifest.yaml`, o un campo del manifiesto distinto de nombre, SHA-256 y fuente | BR14.1 |
| `scripts/check-reports-dir.py` | Un archivo de `evaluation/reports/` que no valida contra C19 v2, que no es `kind: evaluation` o que no tiene su archivo de evidencia | IDS-U11-04; `project.md` (sin datos reales en Git) |
| Tabla de fronteras | Las filas de `libs/incoherence_analyzer/README.md` distintas de las de security-design §1 | NFR1.1 |

## 4. Nivel 2 con el reporte adjunto al PR

### 4.1 Cuándo se exige

`analyzer-level2-gate.yml` exige el reporte si el PR cambia alguna **ruta de IA** (`team.md`: *prompts*,
perfiles, adaptadores de modelos y esquemas de salida):

| Ruta | Por qué |
|---|---|
| `libs/incoherence_analyzer/data/**` | *Prompt* y esquemas del juez y del verificador |
| `libs/incoherence_analyzer/domain/**`, `libs/incoherence_analyzer/application/**` | Filtro, verificación de citas, ventanas y armado de mensajes deciden lo que se emite |
| `libs/model_gateway/**` | Adaptadores y enrutador |
| `libs/anonymizer/adapters/**`, `libs/anonymizer/data/provider-capabilities*` | Adaptadores de los proveedores comerciales (CD-04) |
| `config/profiles.yaml` | Perfiles |
| `contracts/analyzer/**`, `contracts/integrity/forbidden-vocabulary*` | Esquema de salida C6 y vocabulario del filtro |
| `evaluation/thresholds.v1.yaml`, `evaluation/synthetic/**`, `evaluation/adversarial/**` | Umbrales y conjunto |

También se exige en cada etiqueta `analyzer-v<semver>` («toda entrega etiquetada»): el último reporte de
`evaluation/reports/level2/` tiene que cubrir el árbol etiquetado con la misma regla.

### 4.2 Qué comprueba `scripts/check-level2-report.py`

Sin modelos ni red, con las funciones de la propia biblioteca:

1. El PR añade o cambia un par `evaluation/reports/level2/<slug-del-bolt>.json` y
   `<slug-del-bolt>.evidence.yaml`.
2. El reporte valida contra C19 v2 de U1, es `kind: evaluation` y `profile_name: evaluacion-comercial` (el
   único perfil que bloquea, NFR-U11-14), y trae las métricas del Escenario A (corrida con
   `--adversarial escenario-a`, NFR5.1).
3. `prompt_sha256`, `config_sha256`, `profile_sha256`, `dataset_sha256` y el SHA-256 de los umbrales,
   recalculados sobre el árbol del PR, son iguales a los del reporte; `analyzer_version` es la versión de
   `libs/incoherence_analyzer/pyproject.toml`.
4. `evaluated_commit` de la evidencia es antecesor del *head* del PR y `git diff --quiet <evaluated_commit>
   HEAD --` sobre las rutas de §4.1 no muestra cambios: lo evaluado es lo que se fusiona.
5. Las métricas se comparan otra vez con `evaluation/thresholds.v1.yaml` (no se confía en `passes`): 100 % de
   citas verificadas, 0 % de error de formato JSON, 100 % de permutación, consistencia > 0,65, precisión y
   sensibilidad con sus umbrales, 0 fugas del anonimizador, y el Escenario A con sus criterios (NFR4.1–NFR4.9,
   NFR5.1).
6. `gitleaks` sobre los dos archivos con 0 hallazgos. El reporte no puede llevar texto: C19 v2 es cerrado y
   cada cadena tiene `pattern` (P12).

La evidencia es un YAML cerrado, sin texto libre (esquema en `scripts/schemas/level2-evidence.v1.json`,
`additionalProperties: false`):

| Campo | Forma | Para qué |
|---|---|---|
| `evaluated_commit` | 40 caracteres hexadecimales | Paso 4 |
| `host` | `maquina-64gb` o `zine` (este último solo informativo) | Saber dónde se midió |
| `verifier_image_digest` | `sha256:` y 64 hexadecimales | Mismo binario que `model-verifier` de U2 |
| `verifier_model_sha256` | 64 hexadecimales, igual a la línea de `deploy/models.lock` | Mismo modelo que el clúster |
| `started_at`, `finished_at` | Fecha y hora UTC | Duración frente a la meta de 6 h (NFR2.2) |
| `cli_exit_code` | Entero; tiene que ser 0 | La CLI terminó sin métricas por debajo del umbral |

Los reportes de evaluación sobre el conjunto sintético solo llevan cifras, *hashes* y versiones, así que se
versionan; los reportes sobre el corpus del piloto (`kind: run`) nunca entran en Git (BR11.5, `project.md`).
Los reportes informativos de ZINE sobre el conjunto sintético pueden ir en `evaluation/reports/zine/` con la
misma evidencia y no bloquean.

### 4.3 Procedimiento en la máquina de 64 GB (lo ejecuta el humano)

| Paso | Qué pasa | Quién |
|---|---|---|
| 1 | Con el árbol limpio en el *commit* que se quiere evaluar, apaga el juez de `todo-local` en Minikube con `models.todoLocalJudge.enabled=false`, como artefacto revisable que él aplica (IDS-U2-11) | Humano |
| 2 | `scripts/host-verifier.sh start`: comprueba con `sha256sum -c` la línea de `gpt-oss-20b Q8_0` de `deploy/models.lock` y levanta el verificador (§5.2) en `127.0.0.1:18080` | Humano |
| 3 | Carga en su terminal de WSL2 la clave `VERIDICUS_ANTHROPIC_API_KEY` desde el `.env` no versionado | Humano |
| 4 | `VERIDICUS_LOCAL_BASE_URL_VERIFIER=http://127.0.0.1:18080 uv run --directory libs/incoherence_analyzer --extra cli veridicus evaluate --conjunto evaluation/synthetic --perfil evaluacion-comercial --adversarial escenario-a --salida resultados-locales/eval` (forma de F10, NFRD-U11-08); meta ≤ 6 h, reanudable con el mismo `--salida` (NFRD-U11-11) | Humano |
| 5 | `scripts/host-verifier.sh stop`; vuelve a encender el juez de `todo-local` si lo necesita | Humano |
| 6 | `scripts/level2-evidence.py --reporte resultados-locales/eval/reporte.json --slug <slug>`: copia el reporte a `evaluation/reports/level2/`, escribe la evidencia con el *commit* evaluado y los digests, y se niega si el árbol tiene cambios en las rutas de §4.1 | Humano |
| 7 | *Commit* de esos dos archivos solos y *push*; `analyzer-level2-gate.yml` comprueba | Humano y CI |

La corrida de humo sobre las 10 entrevistas del piloto usa el mismo procedimiento con `veridicus analyze` y
`comercial-piloto`, con `--salida` fuera de Git; no produce evidencia ni entra en el PR.

## 5. Dónde corre la CLI: máquina de 64 GB

### 5.1 La CLI en la anfitriona

| Facet | Choice | Rationale |
|---|---|---|
| Lugar | WSL2 del equipo de 64 GB, **fuera** de Minikube y fuera del contenedor de trabajo | `VERIDICUS_LOCAL_BASE_URL_*` tiene que ser *loopback* o privada (NFR1.6); desde el contenedor de trabajo habría que usar un nombre como `host.docker.internal`, que NFR1.6 rechaza (IDS-U11-06) |
| Instalación | `uv sync --directory libs/incoherence_analyzer --extra cli` desde el lockfile; Python 3.12; `torch` solo CPU por el índice de U10 | D1; `team.md` |
| Recursos | Proceso de la CLI ≤ 512 MiB sin modelos (performance-design §8) más el módulo de U10 con su NER (≤ 1,5 GiB de RSS, IDS-U10-02) | Una corrida y una llamada a la vez (performance-design §6) |
| Configuración | `config/profiles.yaml`, `config/prices.yaml` y el catálogo de C25 del repositorio; `VERIDICUS_LIMIT_*` solo baja (NFRD-U11-02); `model_call_timeout_s` = 300 y `run_deadline_final_s` = 3 600 (performance-design §3) | tech-stack-decisions §3 |
| NER del anonimizador | `VERIDICUS_ANONYMIZER_NER_PATH` en `/srv/veridicus/models/<entrada ner>` con su `sha256`, el mismo archivo que usa el proxy | IDS-U10-09 |
| Salidas | `--salida` en `resultados-locales/` (ignorado por Git) o fuera de todo repositorio; regla del corpus con `git check-ignore` | BR11.5 |

### 5.2 Verificador local en la anfitriona (nivel 2 y corridas de la CLI)

| Facet | Choice | Rationale |
|---|---|---|
| Servidor | La **misma imagen de `llama-server`, por digest**, que `model-verifier` de U2 en `values-cpu.yaml`; `scripts/host-verifier.sh` lee el digest de ese archivo | El mismo binario que en el clúster; sin otra imagen que mantener (IDS-U11-05) |
| Modelo | gpt-oss-20b Q8_0 desde `/srv/veridicus/models`, montado de solo lectura; `sha256sum -c` con la línea de `deploy/models.lock` antes de arrancar | `team.md` (artefactos de modelo); el mismo archivo que el volumen de U2, sin segunda descarga |
| Ajustes | `--parallel 1`, `--threads 8`, caché de *prompt* activa, `response_format` `json_schema` | performance-design §2; D6 |
| Red | Puerto publicado solo en `127.0.0.1:18080`; sin `--hf-repo` ni descargas; contenedor con `--read-only`, `--cap-drop ALL` y `no-new-privileges` | NFR1.6; 18080 no choca con el `port-forward` del Ingress en 8443 (IDS-U2-04) |
| Recursos | `--memory 14g`, `--cpus 8` | NFR2.2 (≤ 14 GB, 1 ranura); con el juez de `todo-local` apagado cabe en los 56 GB de WSL2 (IDS-U2-11) |
| Ciclo de vida | `start` y `stop` explícitos; nada lo deja corriendo | Automatizar también la baja |

## 6. ZINE (nodos CPU, instalación sin internet)

| Facet | Choice | Rationale |
|---|---|---|
| Qué corre | La CLI y `llama-server` de conda-forge en el **mismo trabajo** de SLURM, con perfiles locales (`evaluacion-local-zine`) | BR14.4, BR14.5; M2 midió esa API |
| Wheelhouse | `evaluation/zine/empaquetar.py` (en la máquina del humano): `uv export --frozen --no-dev` de cada paquete **sin** el *extra* `cli`, `pip download --only-binary=:all: --platform manylinux2014_x86_64 --python-version 3.12 --implementation cp --require-hashes`, y `uv build --wheel` de los cuatro paquetes y de `veridicus_contracts` | security-design §11; Python 3.12.16 en ZINE (M5); sin `torch` ni `libs-anonymizer`, que ZINE no usa (IDS-U11-02, IDS-U11-03) |
| Paquete | `evaluation/zine/paquete/` ignorado por Git: transcripciones validadas de dos fuentes, consentimiento del corpus desde el archivo del humano, la wheelhouse y un perfil sin destinos externos; `gitleaks` sobre el paquete y, con un hallazgo, se borra y sale ≠ 0 | BR14.2, BR14.3 |
| Instalación | `instalar-y-analizar.sbatch`: `pip install --no-index --find-links` en el entorno conda propio y `veridicus analyze` sobre una muestra sintética; el humano adjunta al PR el comando, el ID de SLURM, el nodo, el código 0 y la versión | BR14.5; AC14.2.5 |
| Recursos | Solo CPU y RAM, sin `--gres=gpu`; `--cpus-per-task` y `--mem` declarados; tiempo de pared ≥ `run_deadline_final_s` × muestras | performance-design §5; IDS-U11-13 |
| Plazos | `model_call_timeout_s` = 3 600 por ventana, `run_deadline_final_s` = 43 200, ventanas 60/20 | performance-design §3 |
| Lo que vuelve | Las salidas sintéticas y el reporte C19 del corpus; `veridicus evaluate --puntuar` puntúa en la máquina del humano | F12; BR12.7 |
| Quién lanza | Siempre el humano: copia el paquete y lanza los `.sbatch` | AUTONOMIA-01 |

## 7. Frontera de AUTONOMIA-04 por entorno

| Componente o entorno | Dentro o fuera del clúster | Datos que cruzan su frontera | Control |
|---|---|---|---|
| *Runner* de la CI | Fuera; GitHub | Solo datos sintéticos; sin claves; red solo para herramientas fijadas, dependencias y el NER público | `pytest-socket`; comprobación sintética de U1; `gitleaks` |
| CLI con perfil comercial (máquina del humano) | **Fuera** del clúster | Sale, directo desde la máquina, solo el texto seudonimizado del papel `judge` hacia `api.anthropic.com` (NFR-U11-01); el verificador recibe citas en claro por *loopback* | Módulo de U10 en el mismo proceso, armado del gateway y fallo cerrado (security-design §2–§3); en la anfitriona no hay `NetworkPolicy`: la barrera es la del proceso (IDS-U10-09) |
| Verificador en la anfitriona | Fuera; contenedor en WSL2 | Entra por `127.0.0.1:18080`: `hecho`, `tipo` y las dos citas. No sale nada | Solo *loopback* y sin descargas. Riesgo residual declarado: el contenedor conserva la salida de la red puente de Docker, como la propia CLI; `llama-server` no abre conexiones con una ruta de modelo local |
| CLI con perfil local (máquina o ZINE) | Fuera | Nada: el anonimizador no interviene (BR7.7) | `base_url` privada o *loopback* (NFR1.6) |
| Paquete de ZINE | Fuera; lo copia el humano | Transcripciones sintéticas y del corpus público del piloto con su consentimiento, wheelhouse y perfil local | Fuera de Git, `gitleaks`, solo perfiles locales (BR14.2, BR14.3) |
| `reporte.json` (C19 v2) | Donde corre la CLI | Solo cifras, *hashes* y versiones; los de evaluación sintética entran en Git como evidencia (§4) | Esquema cerrado con `pattern` (P12) |
| Biblioteca dentro de `semantic-agent` | Dentro, namespace `veridicus` | Hacia fuera, nada: lo externo va por el cliente de C21 al proxy | `NetworkPolicy` de U2; import-linter de U4 (sin `libs.anonymizer`) |

## 8. De la fusión al uso (sin despliegue propio)

| Paso | Qué pasa | Quién |
|---|---|---|
| 1 | PR de B11 (rama `feat/b11-incoherence-analyzer`) con `analyzer.yml` en verde y el reporte de nivel 2 de §4 (definición de terminado de B11, punto 5) | Agente propone; humano revisa |
| 2 | Squash-merge en `main` protegida: la aprobación humana registrada | Humano |
| 3 | La CLI se usa desde `main` en la máquina del humano (`uv sync`); para ZINE, el humano corre `empaquetar.py` sobre una etiqueta `analyzer-v<semver>` | Humano |
| 4 | En el clúster, la biblioteca llega solo dentro de la imagen de `semantic-agent`, que reconstruye el *workflow* de U4 (filtro por `libs/**`) y promueve el PR de despliegue de U2 | U4 y U2 |

U11 no publica paquetes en PyPI ni en GHCR: el repositorio es público, la wheelhouse se arma desde los
lockfiles y la etiqueta (IDS-U11-12).

## 9. Reversión

| Qué falló | Cómo se revierte |
|---|---|
| Un cambio de *prompt*, perfil, umbral o adaptador da peores métricas después de fusionar | `git revert` de su PR; el reporte anterior sigue cubriendo el árbol anterior (§4.2 paso 4) |
| La biblioteca rompe `semantic-agent` | `git revert` del PR de despliegue (U2) y después del PR de U11 |
| Una wheelhouse no instala en ZINE | `empaquetar.py` sobre la etiqueta anterior; el trabajo nuevo no cambió nada allí |
| Un reporte de nivel 2 con datos que no debía llevar | No puede: C19 v2 es cerrado. Si `gitleaks` falla, el PR no se fusiona |
| Una clave filtrada | El humano la revoca en el proveedor y la cambia en su `.env`; la CI y ZINE nunca la tuvieron |

## 10. Secretos

| Secreto | Dónde vive | Quién lo usa |
|---|---|---|
| Clave de Anthropic para la CLI (`VERIDICUS_ANTHROPIC_API_KEY`) | `.env` no versionado de la máquina del humano, cargado en su terminal | Solo la raíz de composición de la CLI, que se la pasa al módulo de U10 (security-design §7) |
| Claves en la CI | Ninguna | — |
| Claves en ZINE | Ninguna: solo perfiles locales; el paquete pasa `gitleaks` | — |
| `GITHUB_TOKEN` | Solo lectura en los dos *workflows* | Clonar y leer la base del PR |

`gitleaks` en pre-commit y en la CI y la prueba del *canary* (security-design §7) impiden que una clave
aparezca en el repositorio, en un reporte o en un log.

## 11. Precisiones y peticiones (IDS-U11-xx)

No edité ningún artefacto aprobado ni de otra unidad. En la aprobación decides cuáles se llevan al original,
cada una en su propio commit. Ninguna deja salir del clúster ni de la máquina algo que hoy no sale, ni cambia
cifras de pods.

| ID | Artefacto aprobado o unidad | Precisión o petición | Origen |
|---|---|---|---|
| IDS-U11-01 | Archivo de etapa (`produces_kinds`) | U11 es `library`: solo `cicd-pipeline.md` y `traceability.json`. La máquina de la CLI, ZINE y la frontera van en §5–§7 de este documento | `produces_kinds` del archivo de etapa |
| IDS-U11-02 | `nfr-requirements/tech-stack-decisions.md` (D1) y `nfr-design/security-design.md` §9 | `cli/composition.py` importa `libs.anonymizer` **de forma diferida**, solo si el perfil tiene un papel externo. Sin el *extra* `cli` instalado, un perfil comercial termina con código 3 y 0 llamadas, igual que con el módulo que no se construye; `todo-local` y `evaluacion-local-zine` arrancan. Así la wheelhouse de ZINE no lleva `torch` ni `libs-anonymizer`. Prueba de nivel 0 y *job* `wheelhouse` | D1; BR14.2 (solo perfiles locales en ZINE) |
| IDS-U11-03 | `nfr-design/security-design.md` §11 (wheelhouse) | `uv export --frozen` se completa con `pip download --only-binary=:all: --platform manylinux2014_x86_64 --python-version 3.12 --implementation cp --require-hashes` y `uv build --wheel` de los paquetes propios; una dependencia sin rueda `manylinux2014` hace fallar el empaquetado en vez de compilar en ZINE. El *job* `wheelhouse` repite el armado e instala con `--network none` | M5 (Python 3.12.16, instalación sin internet); AC14.2.5 |
| IDS-U11-04 | `team.md` (nivel 2: «el reporte JSON se adjunta al PR») y `tech-stack-decisions.md` §6 | «Adjunto al PR» es un par versionado en `evaluation/reports/level2/`: el reporte C19 v2 y un YAML de evidencia cerrado con el *commit* evaluado y los digests, comprobados por `check-level2-report.py` (§4.2). C19 v2 no tiene campo de *commit* y no se amplía (U1). U10 puede usar la misma evidencia para su `anonymizer-perf-gate.yml` | C19 v2; IDS-U10 (perf gate «mismo mecanismo que U11») |
| IDS-U11-05 | Infrastructure Design de U2 (IDS-U2-11, «verificador en la anfitriona») | El verificador de la anfitriona es la imagen de `llama-server` de `model-verifier` por digest, levantada con `scripts/host-verifier.sh` en `127.0.0.1:18080` con `--memory 14g` y `--cpus 8`, sobre el archivo de `/srv/veridicus/models` verificado con `sha256sum -c`. No es una petición: U2 no cambia nada | NFR2.2; IDS-U2-11 |
| IDS-U11-06 | `tech-stack-decisions.md` §3 (`VERIDICUS_LOCAL_BASE_URL_<PAPEL>`) | La CLI corre en WSL2 y no dentro del contenedor de trabajo, porque desde el contenedor el verificador solo se alcanzaría por un nombre que NFR1.6 rechaza | security-design §2 (destino local) |
| IDS-U11-07 | — (decisión de esta etapa) | Los dos *workflows* se disparan con todo PR y filtran por rutas en el *job* `changes`; `gate` y `check` son las comprobaciones obligatorias. Un *workflow* con filtro `paths:` dejaría pendiente una comprobación obligatoria en los PR que no lo disparan | Protección de `main` con comprobaciones obligatorias (`team.md`, P0.1) |
| IDS-U11-08 | Infrastructure Design de U4, revisión 1 (`libs.yml` y `ai-eval-gate.yml`) | **Petición a U4** para su segunda pasada: `libs.yml` y `ai-eval-gate.yml` quedan sustituidos por `analyzer.yml` y `analyzer-level2-gate.yml` de U11, porque los paquetes de `libs/` y el nivel 2 del analizador son ahora de U11. `semantic-agent.yml` conserva su filtro por `libs/**` | Cambio 01 (U11 dueña de `model_gateway` e `integrity_policy`) |
| IDS-U11-09 | Tarea previa P0.1 (configuración de GitHub) | **Petición al humano**: añadir `analyzer / gate` y `analyzer-level2-gate / check` a las comprobaciones obligatorias de `main` cuando B11 cree los *workflows* | `team.md` (comprobaciones obligatorias) |
| IDS-U11-10 | `nfr-design/security-design.md` §3 (prueba compuesta en nivel 1 con el NER real) | El nivel 1 reutiliza el paso de IDS-U10-07 (`fetch-models.sh --only ner`, verificación del `sha256` y caché por ese `sha256`); ninguna prueba descarga nada | IDS-U10-07; `team.md` (descarga en aprovisionamiento) |
| IDS-U11-11 | `tech-stack-decisions.md` §4 («el perfil GPU no lo usa ninguna prueba de U11») | Sin máquina GPU no hay etapa GPU para U11; la evaluación local grande va a ZINE en CPU y la comercial a la máquina de 64 GB | Cambio de máquinas del 2026-11-22 (decidido por U2) |
| IDS-U11-12 | `team.md` (nivel 2 en «toda entrega etiquetada») | Una entrega de U11 es una etiqueta `analyzer-v<semver>` igual a la versión de `libs/incoherence_analyzer/pyproject.toml`; `analyzer-level2-gate.yml` se dispara con ella. No se publica en PyPI ni en GHCR | Repositorio público; D1 |
| IDS-U11-13 | `nfr-design/performance-design.md` §5 (comprobación de los `.sbatch`) | `check-sbatch.py` exige además `--cpus-per-task` y un `--mem` no menor que la suma de los GGUF del manifiesto más 8 GiB, porque juez y verificador conviven en el mismo trabajo | M1 y M6 (tamaños de los GGUF); BR14.5 |
