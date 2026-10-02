# Evidencia — Practices Discovery

**Líder:** `aidlc-pipeline-deploy-agent` · **Apoyo:** `aidlc-quality-agent`, `aidlc-developer-agent`, `aidlc-devsecops-agent` · **Tipo de proyecto:** Greenfield · **Scope:** `classic` (`skeleton: off`) · **Commit del borrador:** `e0311bc` · **Commit de la integración:** `608bcb9` · **Fecha:** 2026-10-02

## Qué inspeccionó cada participante

| Participante | Inspeccionó | Infirió |
|---|---|---|
| Líder (pipeline-deploy) | `memory/org.md`, `team.md`, `project.md` (`## Decided`); `aidlc-state.md` (scope `classic`, Guard Policy `strict`, 3.7 y Operation en SKIP); `.claude/scopes/aidlc-classic.md`; `specs/prd.md` Seg. 6, 8, 9, 11, 13; `plan-aidlc.md`; `docs/limite-autonomia.md`; `git log`/`branch -a`/`remote -v`; raíz del repo, `.gitignore`, `docker/` | Un solo autor, solo `main`, cero PR y cero merges (todo por commit directo); Conventional Commits en español en el historial reciente; sin código, sin `.github/` ni configuración de *linters*; `docker/` es el contenedor de trabajo; remoto `freyesJaveriana/tai` en GitHub. Propuso tronco + PR con evidencia, sin ceremonia de esqueleto, test-after y un único clúster local |
| Calidad | Borrador del líder, PRD Seg. 10–11, `team.md` (AUTONOMIA), Test Strategy Standard | Metodología `custom` (guardias y contratos primero); niveles 0–3 y manual; umbrales del Golden Dataset; mapa de pruebas AUTONOMIA; prueba de humo medible; hueco en la meta de detección |
| Desarrollo | Raíz del repo (`e0311bc`), PRD Seg. 6, 8, 9, 11, 13, borrador del líder | Monorepo en la raíz; identificadores en inglés con glosario; capas `api/worker → application → domain` + `adapters/`; jerarquía de errores con Problem Details; mypy estricto; migraciones como `Job` aprobado |
| DevSecOps | Borrador del líder, PRD Seg. 8 §5, Seg. 12 (riesgos 5 y 7), Seg. 13 Módulo 7, `.gitignore` | El borrador no tenía ningún control de seguridad en la cadena de entrega; propuso `gitleaks`, Trivy, `pip-audit`/`npm audit`, cadena de políticas `helm template` → `kubeconform` → Kyverno CLI, Secrets solo referenciados, CI sin credenciales del clúster, artefactos de modelo fijados, protección de `main` frente al administrador |

## Decisiones de la entrevista

| # | Tema | Respuesta | Efecto en `team-practices.md` |
|---|---|---|---|
| 1 | Entrada a `main` | A | PR con evidencia y squash-merge para código e infraestructura; `main` protegida también frente al administrador; documentación y AI-DLC por commit directo |
| 2 | Revisión de PR | A | Autor + revisión del agente; par del curso a pedido |
| 3 | Repositorio | A | Monorepo en la raíz (`frontend/`, `services/`, `libs/`, `contracts/`, `db/migrations/`, `deploy/`, `evaluation/`) |
| 4 | Esqueleto | A | Sin ceremonia; primera unidad = flujo de texto de punta a punta |
| 5 | Orden de pruebas | A | `custom`: guardias AUTONOMIA-03/04/05 y contratos primero; resto test-after por capa |
| 6 | Cobertura | A | 80 % de líneas por servicio y frontend + 100 % de ramas en módulos guardia |
| 7 | Herramientas | A | `pytest`/`pytest-cov`, mypy estricto, Vitest + RTL, TypeScript estricto |
| 8 | Golden Dataset | A + nota | Bloquea PR que tocan la IA y entregas etiquetadas; nota: se ejecutará con GPU en otra máquina, con requisitos para los pasos GPU, y la mayor parte del desarrollo en la máquina CPU |
| 9 | Meta de detección | A | Diferida a Requirements Analysis |
| 10 | Entorno | C + nota | Diferido a Infrastructure Design; infraestructura mínima con máximo 4 GPU y 32 GB de RAM; desarrollo en CPU; pruebas GPU agrupadas en una etapa separada |
| 11 | Llegada al clúster | A | Fusión = aprobación registrada; Argo CD con sincronización automática, sin *prune* sobre CloudNativePG, *deploy key* de solo lectura; migraciones como `Job` por su propio PR; antes del Módulo 8, aplicación manual |
| 12 | Imágenes | A (la parte de `kind load` la reemplaza el seguimiento 4) | SHA, nunca `latest`, base por digest, sin root, Trivy bloqueante |
| 13 | Secrets | A | Solo referencias; valores desde `.env` no versionado; `.gitignore` ampliado; `gitleaks` en pre-commit y CI |
| 14 | Lenguajes y *linters* | A | Python 3.12, Ruff (con `S`), `uv`; TypeScript, ESLint + Prettier, `react/no-danger`; `yamllint`, `hadolint`, `helm lint` |
| 15 | Idioma de identificadores | A | Inglés con glosario único; textos visibles, errores y comentarios en español |
| 16 | CI | A + nota | GitHub Actions con las compuertas listadas; nota: **tarea conjunta de configuración y validación de GitHub antes del desarrollo** |
| 17 | Reglas duras | B, C, E | Tres reglas `NEVER` en `discovered-rules.md`. A no es regla dura porque la GPU se permite para la demo y algunas etapas. D tampoco, aunque AUTONOMIA-03 sigue vigente (seguimiento 1) |
| S1 | Opinión de veracidad | A | AUTONOMIA-03 sin cambios: la IA califica cada afirmación como congruente / incongruente / no documentada frente al marco de verdad, con CoT y como sugerencia editable; nunca «falso», «verdadero» ni «miente» |
| S2 | Papel de la GPU | A | GPU opcional: el sistema funciona completo en CPU; perfil GPU (≤ 4 GPU) para evaluación con modelos más grandes y demo; pruebas GPU en etapa separada a demanda. El PRD y `project.md` ya se ajustaron (commits `7afdb15`, `608bcb9`) |
| S3 | «32 GB» | A | RAM del sistema; la memoria de GPU se documenta en Infrastructure Design |
| S4 | Distribución de imágenes | A | GHCR privado por SHA; ambas máquinas descargan la misma imagen; se mantienen Trivy, digest y usuario sin root |

## Cómo se resolvieron las objeciones de los revisores

- **Calidad**: `test-after` puro → `custom` (P5 = A). Golden Dataset «aparte» → bloquea los PR de IA y las entregas (P8 = A). Faltaban contratos y los Escenarios B y C de *red-teaming* → incluidos en el nivel 2. Humo no medible → `scripts/smoke.sh` con un resultado esperado concreto. Meta de detección → diferida (P9 = A).
- **Desarrollo**: organización del repositorio (P3 = A), verificador de tipos (P7 = A), idioma de identificadores (P15 = A), capas y errores → integrados en `## Code Style`. Migraciones al arrancar → regla dura (P17-E).
- **DevSecOps**: controles de seguridad, cadena de políticas, Secrets, protección de `main` frente al administrador y *prune* desactivado → integrados (P1, P11, P13, P16 = A).

## Disenso que se mantiene

- **«NEVER asumir GPU» (17-A)**: los tres revisores la recomendaban como regla dura y el humano la rechazó. Mitigación en las prácticas: la suite completa corre en CPU, ninguna prueba de los niveles 0 y 1 exige GPU y el perfil GPU es una etapa separada. El riesgo residual es que una dependencia CUDA entre en una imagen del perfil CPU sin que lo detecte una regla dura; la cubre la revisión del PR.
- **Vocabulario de veracidad en identificadores (17-D)**: desarrollo la recomendaba como regla dura y el humano la rechazó. AUTONOMIA-03 cubre la salida de la IA y la interfaz con una prueba automatizada, pero no cubre columnas, métricas ni nombres internos. Queda a criterio del glosario de dominio.
- **Distribución de imágenes**: devsecops prefería la carga local (sin credenciales de registro). El humano eligió GHCR privado (S4); se adoptan las condiciones de devsecops (paquete privado, `packages: write` solo en el *job* de *build*).
- **Política de manifiestos**: calidad sugería `conftest`/OPA y devsecops Kyverno CLI. P16 = A fija Kyverno CLI.

## Elementos diferidos

| Elemento | Etapa destino |
|---|---|
| Meta de detección de las 6 discrepancias sembradas y alertas espurias toleradas en las 4 transcripciones alineadas | Requirements Analysis |
| Igualdad exacta con el umbral (¿alerta o Hecho No Documentado?; calidad recomienda Hecho No Documentado) | Requirements Analysis |
| Rol que cambia el estado de una alerta (¿solo `analista` o también `admin`?) | Requirements Analysis |
| Prueba de carga para la meta de > 98 % de sesiones sin `OOMKilled` ni `timeout` (la etapa 4.6 está en SKIP): ¿en Build and Test con k6/Locust y con cuántas sesiones? | Requirements Analysis (con *N* en NFR Requirements) |
| Clasificación congruente / incongruente / no documentada por afirmación (S1) como requisito explícito | Requirements Analysis |
| Valor de *N* (segundos) de la prueba de humo | NFR Requirements |
| Entorno de cada máquina: distribución de Kubernetes, CNI que haga cumplir `NetworkPolicy`, namespaces, VRAM, qué corre en el perfil GPU | Infrastructure Design |
| **Tarea conjunta de configuración y validación de GitHub antes del desarrollo** (petición explícita del humano, P16) | Delivery Planning: debe ser la primera tarea, antes de la primera unidad |
| Primera unidad = flujo de texto de punta a punta (P4) | Delivery Planning |

## Incertidumbre que queda

- **Perfil de referencia de la compuerta de nivel 2**: el humano piensa correr la evaluación en la máquina GPU, pero el sistema debe funcionar completo en CPU. No está decidido si el reporte que bloquea un PR de IA debe salir del perfil CPU, del GPU o de ambos. Las prácticas exigen que el reporte declare su perfil; la decisión corresponde a Requirements o NFR Requirements.
- **Protección de rama en GitHub**: no se verificó si el repositorio `freyesJaveriana/tai` es público o privado ni qué plan tiene. En un repositorio privado, la protección de ramas y los *rulesets* pueden requerir un plan de pago. Lo resuelve la tarea conjunta de configuración de GitHub.
- **Acceso a GHCR privado**: las dos máquinas y Argo CD necesitan una credencial de lectura (*image pull secret*) creada por el humano; el mecanismo lo define Infrastructure Design.
- **CI sin diseño propio**: la etapa 3.7 `ci-pipeline` está en SKIP y este trabajo se detiene en la Parte 1 de Code Generation, así que lo afirmado aquí es la especificación que el proyecto real debe cumplir.
- **Herramientas no observadas**: no existe código, así que ninguna herramienta se observó en uso; todas son prácticas afirmadas por el humano.
