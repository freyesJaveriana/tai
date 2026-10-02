**Collaborator:** aidlc-devsecops-agent

## Contribution

> Perspectiva de seguridad sobre el borrador del líder (`team-practices.md`,
> `discovered-rules.md`, `evidence.md`). Proyecto greenfield, autor único, clúster local
> Minikube/Kind sin GPU. El criterio de fondo es **poco y bloqueante, no mucho y decorativo**.
> Cada control propuesto corre en CPU, es gratuito, cabe en un runner estándar de GitHub
> Actions (objetivo: menos de 8 min por PR) y está atado a un requisito citado: PRD Seg. 6
> Principio 3, Seg. 8 §5, Seg. 11 Escenario A, Seg. 12 riesgos 5 y 7, Seg. 13 Módulo 7, o
> AUTONOMIA-01/04. Quedan fuera **a propósito**: SonarQube, CodeGuru, Snyk de pago, firma
> con cosign, Falco y DAST como compuerta (justificación en §6).

### 1. Hallazgo principal: el borrador no tiene ningún control de seguridad en la cadena de entrega

`team-practices.md` cubre *lint*, formato, pruebas y validación estructural de manifiestos
(`helm lint`, `kubeconform`), pero no nombra ningún escaneo de secretos, de dependencias, de
imágenes ni de políticas, y no dice cómo llegan los Secrets al clúster sin pasar por git. El
PRD sí lo exige: Seg. 8 §5 pide como MUST `NetworkPolicy`, `requests`/`limits` y Secrets
inyectados en tiempo de ejecución, y el Seg. 13 Módulo 7 es un módulo CKS completo. Además,
`kubeconform` solo valida el **esquema**. Un `Deployment` sin `resources`, corriendo como
root, o un namespace sin `NetworkPolicy` de salida pasan `kubeconform` sin ningún aviso. Sin
una verificación de políticas, AUTONOMIA-04 («existe una tarea que produce la
`NetworkPolicy`») se cumple en el papel, pero nada impide que una regresión la elimine.

### 2. Texto propuesto para integrar en las cinco secciones

**Para `## Way of Working`** (complementa P1/P2):

- `main` está protegida: no admite *push* directo para código, manifiestos ni charts. Exige
  PR con las comprobaciones de CI en verde y la protección **también aplica al
  administrador** («Do not allow bypassing the above settings»). Sin esto, la fusión del PR
  no es una aprobación registrada (AUTONOMIA-01), porque el único autor puede saltársela.
  La documentación (`docs/`, `specs/`, `aidlc/`) puede seguir en commit directo si el humano
  así lo decide en P1. Para eso hace falta un *ruleset* por ruta o aceptar que también pase
  por PR.
- Un **pre-commit local** (`pre-commit` framework) corre `gitleaks`, Ruff y `yamllint` antes
  de cada commit. CI repite todo, porque el hook local se puede saltar con `--no-verify`.

**Para `## Testing Posture`** (complementa P5/P6):

- Las pruebas de seguridad son pruebas de primera clase, citadas por ID en el plan de tareas:
  - suite de *red-teaming* de inyección de prompts (Escenario A, riesgo 7) con casos
    sintéticos que **deben** fallar el intento de anular el *system prompt*. Su carácter
    bloqueante sigue lo que se decida en P6;
  - prueba estática de que todo pod etiquetado como portador de datos sin anonimizar queda
    seleccionado por una `NetworkPolicy` que niega la salida (corre en CI sobre los
    manifiestos renderizados, sin clúster);
  - prueba de humo de salida en el clúster, ejecutada por el humano tras desplegar: desde un
    pod de `veridicus-apps` con datos sin anonimizar, `curl https://example.com` **falla**
    (evidencia para AUTONOMIA-04);
  - prueba del anonimizador (AUTONOMIA-04): el payload saliente no contiene nombres ni
    identificadores del Golden Dataset.
- Los datos de prueba, de CI y del repositorio son **exclusivamente sintéticos** (Golden
  Dataset y escenario de control). Ver la regla candidata en §5.

**Para `## Deployment`** (complementa P8/P9):

- **Imágenes propias**: se etiquetan con el SHA del commit, nunca con `latest`, y se
  escanean con **Trivy** antes de cargarlas o publicarlas. El escaneo bloquea ante hallazgos
  `CRITICAL`/`HIGH` que **tengan corrección disponible** (`--ignore-unfixed`). Las imágenes
  base son mínimas (`python:3.x-slim` o *distroless*, `node` solo en la etapa de *build* del
  frontend) y se fijan **por digest** (`@sha256:…`). El contenedor corre con un `USER` no
  root.
- **Imágenes de terceros** en manifiestos y charts (CloudNativePG, Redis, Argo CD,
  Prometheus/Grafana): versión del chart fijada y, cuando el chart lo permita, imagen fijada
  por digest. Nada de `latest` ni de rangos.
- **Secrets**: ningún manifiesto versionado contiene el valor de un Secret, ni siquiera en
  base64. Los manifiestos solo hacen referencia (`secretKeyRef` / `envFrom`). Los valores
  viven en un `.env` local no versionado y los crea **el humano** con un script revisable
  (`kubectl create secret … --dry-run=client -o yaml | kubectl apply -f -`), lo que encaja
  con AUTONOMIA-01. Se montan como variables de solo lectura, como pide el Módulo 7. El
  cifrado en reposo en etcd (`EncryptionConfiguration`) queda como COULD del Módulo 7 (P14).
- **Línea base de seguridad por pod** (verificada en CI por la política de §3):
  `runAsNonRoot: true`, `allowPrivilegeEscalation: false`, `capabilities.drop: [ALL]`,
  `readOnlyRootFilesystem: true` donde sea viable, `seccompProfile: RuntimeDefault`,
  `automountServiceAccountToken: false` salvo que se justifique, una ServiceAccount por
  servicio y `requests`/`limits` obligatorios.
- **Namespaces** con Pod Security Admission integrada (sin instalar nada):
  `pod-security.kubernetes.io/enforce: restricted` en `veridicus-apps`. En
  `veridicus-system` se usa `restricted` si CloudNativePG y Redis lo soportan y, si no,
  `baseline` con la excepción documentada. Cada namespace lleva una `NetworkPolicy`
  *default-deny* de entrada y salida, con permisos explícitos (DNS, servicio a servicio).
- **Riesgo 7 en el despliegue**: los *system prompts* se montan desde un ConfigMap con
  `readOnly: true`, y el rol de base de datos del juez es de **solo lectura** sobre el marco
  de verdad (roles gestionados por CloudNativePG, uno por servicio, mínimo privilegio).
- **Artefactos de modelo** (Whisper, LLM ≤ 8B, *embeddings*): se descargan en tiempo de
  *build* o de aprovisionamiento, nunca en tiempo de ejecución. Así la `NetworkPolicy` de
  salida puede ser total. La revisión queda fijada (*commit* o etiqueta del repositorio de
  origen) y se verifica con `sha256`. Se prefieren formatos sin código ejecutable
  (`safetensors`, GGUF) frente a `pickle`/`.bin`, y nunca se usa `trust_remote_code=True`.
- **CI no despliega**: el *workflow* de CI no tiene `kubeconfig` ni credenciales del clúster
  y declara `permissions: contents: read` por defecto. Desplegar es cosa del humano o de
  Argo CD (P8), nunca del runner.

**Para `## Code Style`** (complementa P10/P11):

- **SAST de Python sin herramienta extra**: Ruff con las reglas `S` (equivalentes de Bandit)
  activadas en `pyproject.toml`, y también `B` y `PL` si el humano quiere. Una supresión
  (`# noqa: S…`) siempre lleva el motivo en la misma línea.
- **Frontend**: con ESLint, la regla `react/no-danger` en `error` (prohíbe
  `dangerouslySetInnerHTML`). El texto de testimonios, citas y CoT es entrada no confiable y
  podría llevar una inyección almacenada (XSS) hasta la vista del analista. El plugin
  `eslint-plugin-security` es opcional y produce mucho ruido en el frontend; no lo
  recomiendo como bloqueante.
- **Semgrep** (`p/python`, `p/owasp-top-ten`, `p/dockerfile`) como segundo SAST es un COULD
  no bloqueante. Ruff `S` ya cubre lo esencial para Python con costo casi nulo.
- **Dockerfiles**: `hadolint` en CI (imagen base fijada, `USER` no root, sin `ADD` remoto).
- **Escaneo de secretos**: `gitleaks` en pre-commit y en CI, bloqueante. La primera vez se
  ejecuta sobre **todo el historial** (`gitleaks git`) como línea base.

### 3. Verificación de políticas sobre manifiestos (respuesta concreta)

Recomiendo esta cadena, completa y *offline* (ningún paso toca el clúster, así que
AUTONOMIA-01 no aplica):

1. `helm template` → manifiestos renderizados;
2. `kubeconform -strict` (esquema, incluidos los CRD de CloudNativePG con
   `-schema-location` para el catálogo de CRDs);
3. **Kyverno CLI** (`kyverno apply` / `kyverno test`) con políticas versionadas en el repo:
   `require-requests-limits`, `require-run-as-non-root`, `disallow-privilege-escalation`,
   `disallow-latest-tag`, `require-image-digest` (terceros), `disallow-host-path`, y una
   política propia: «todo pod con la etiqueta `veridicus.io/datos: sin-anonimizar` está
   seleccionado por una `NetworkPolicy` sin reglas de *egress* a `0.0.0.0/0`».
4. `trivy config` sobre manifiestos y Dockerfiles, como red de seguridad general.

**Por qué Kyverno y no OPA/Conftest ni Checkov**: las políticas se escriben en YAML (curva baja
para un estudiante) y las **mismas** políticas se pueden instalar después como *admission
controller* en el clúster, en modo `Audit` y luego `Enforce`. Eso es justo el contenido del
Módulo 7 (CKS). Esa instalación sí es un cambio al clúster: va por PR y con aprobación humana
(AUTONOMIA-01). Checkov y kube-linter son alternativas válidas, pero no se reutilizan como
control en tiempo de admisión.

### 4. Cadena de suministro: lo mínimo que sí vale la pena

| Control | Herramienta | Cuándo | Bloquea |
|---|---|---|---|
| Archivo de bloqueo obligatorio | `uv.lock` o `requirements.txt` con `--require-hashes`; `package-lock.json` con `npm ci` | Siempre | Sí (CI falla si falta o no coincide) |
| CVE en dependencias | `pip-audit`, `npm audit --audit-level=high --omit=dev` | Cada PR | Sí, `HIGH`/`CRITICAL` con corrección |
| CVE en imágenes | `trivy image --severity HIGH,CRITICAL --ignore-unfixed --exit-code 1` | Cada PR que toque una imagen | Sí |
| SBOM | `trivy image --format cyclonedx` como artefacto de CI | Cada imagen | No (es evidencia) |
| Actualizaciones | Dependabot semanal (pip, npm, docker, github-actions) | Semanal | No (abre PR) |
| Acciones de CI | `uses: org/accion@<SHA completo>`, no `@v4` | Siempre | Revisión del PR |
| Firma de imágenes (cosign) | — | Fuera de alcance del MVP | — |

**Excepciones**: se registran en archivos versionados (`.trivyignore`, `.gitleaksignore`,
`# noqa: S…`). Cada una lleva su justificación y **fecha de caducidad** en un comentario.
Nunca se baja el umbral para que una compuerta pase (coherente con `org.md`, que prohíbe
debilitar los pisos de calidad).

### 5. Regla dura candidata (para `discovered-rules.md`, solo si el humano la enuncia)

- (candidata, pendiente de confirmación — P18) `NEVER` versionar en el repositorio ni usar en
  CI testimonios, audios, nombres o identificadores reales; los datos del repositorio, de las
  pruebas y de CI son exclusivamente sintéticos (Golden Dataset y escenario de control).
  *Motivo*: GitHub y sus runners están **fuera** del clúster local. Un dato real en un
  *fixture*, en un log de CI o en el historial de git ya salió del perímetro que protege
  AUTONOMIA-04, y borrarlo del historial no lo deshace. AUTONOMIA-04 habla de componentes en
  ejecución, no del repositorio ni de la CI, así que esta regla no lo repite.
- (candidata, pendiente de confirmación — P14) `NEVER` versionar el valor de un Secret, un
  `.env`, un `kubeconfig` ni una clave privada; si `gitleaks` detecta uno, la credencial se
  revoca y se rota antes de limpiar el historial.

Mejora concreta, sin decisión pendiente: el `.gitignore` actual ignora `docker/.env`, pero no
un `.env` en otras rutas, ni `*.pem`, `*.key`, `kubeconfig*`, `*.kubeconfig` o
`secrets*.yaml` sin cifrar. Conviene añadir esos patrones (fuera del bloque `AI-DLC`) en el
primer Bolt de infraestructura. Es un cambio en el repo, no en el clúster.

### 6. DAST para un MVP local

- **No como compuerta.** No hay un entorno de *staging* que escanear en cada PR, y montar el
  clúster en el runner para un escaneo dinámico (Kind dentro de Actions + ZAP) cuesta más
  que lo que aporta en este alcance.
- El «DAST» que sí importa en este dominio es la **suite de *red-teaming* de inyección de
  prompts** sobre la API en ejecución (Escenario A). Ya está en el borrador y su carácter
  bloqueante se decide en P6.
- COULD: un `zap-baseline` manual contra la API expuesta con `kubectl port-forward` antes de
  la sustentación. Lo ejecuta el humano y el informe se adjunta como evidencia.

### 7. Ajustes a las preguntas del líder y preguntas nuevas

| ID | Ajuste / pregunta | Respuesta recomendada y por qué |
|---|---|---|
| P1 (ajuste) | Añadir: ¿protección de `main` que también aplique al administrador, con comprobaciones obligatorias? | **Sí.** Sin ella, «la fusión del PR es la aprobación registrada» (P8, AUTONOMIA-01) no se puede verificar, porque el único autor puede hacer *push* directo. |
| P8 (ajuste) | Si Argo CD sincroniza solo: ¿con *auto-prune* sobre `veridicus-system`? | **Sincronización automática sí; *prune* automático no para la base de datos.** Recomiendo `Prune=false` (anotación `argocd.argoproj.io/sync-options`) en el `Cluster` de CloudNativePG y sus PVC: un borrado accidental del manifiesto destruiría el marco de verdad. Argo CD lee el repo con una *deploy key* de **solo lectura**. La sincronización automática es compatible con AUTONOMIA-01 solo si se cumple P1 (protección de `main`). |
| P9 (ajuste) | Añadir: ¿Trivy bloqueante y base por digest? ¿Registro? | **Carga local (`kind load` / `minikube image load`).** No requiere credenciales de registro ni publica nada fuera de la máquina. Si se elige GHCR, el paquete debe ser **privado** y `packages: write` solo en el *job* de *build*. Etiqueta por SHA + Trivy bloqueante en ambos casos. |
| P10 (ajuste) | Añadir: ¿Ruff con reglas `S`? ¿`react/no-danger` en `error`? | **Sí a ambas**: SAST de costo nulo y defensa contra XSS almacenado en la vista del analista. |
| P11 (ajuste) | Añadir: ¿qué compuertas de seguridad bloquean y con qué umbral? | **Bloquean** `gitleaks`, Ruff `S`, `hadolint`, `pip-audit`/`npm audit` (`HIGH`+ con corrección), Trivy (`HIGH`/`CRITICAL` con corrección) y Kyverno CLI. **Avisan**: Semgrep y `MEDIUM`. CI con `permissions: contents: read`, acciones fijadas por SHA y sin credenciales del clúster. |
| P13 (comentario) | — | Coincido con elevarla a regla dura. Todas las herramientas propuestas aquí corren en CPU. |
| **P14** | ¿Cómo llegan los Secrets al clúster sin versionarlos? ¿Cifrado en reposo de etcd en el Módulo 7? | **Script revisable ejecutado por el humano a partir de un `.env` no versionado**; manifiestos solo con referencias. SOPS o Sealed Secrets **no** hacen falta mientras Argo CD no deba gestionar los Secrets. `EncryptionConfiguration` en Kind/Minikube como COULD del Módulo 7, por PR. |
| **P15** | ¿`gitleaks` en pre-commit y en CI, con escaneo inicial de todo el historial? | **Sí.** Cuesta segundos y el historial actual (solo documentación) debería salir limpio, así que la línea base no estorba. |
| **P16** | ¿Verificación de políticas de manifiestos con Kyverno CLI en CI y Pod Security Admission `restricted` en los namespaces? ¿Instalar Kyverno en el clúster como parte del Módulo 7? | **CLI en CI: sí. PSA: sí. Kyverno en el clúster: COULD**, primero en `Audit`, por PR aprobado (AUTONOMIA-01). Verifica de forma continua la `NetworkPolicy` que AUTONOMIA-04 exige como artefacto. |
| **P17** | ¿Alcance de la cadena de suministro: archivos de bloqueo, digests, acciones fijadas por SHA, Dependabot semanal, SBOM por imagen? ¿Firma con cosign? | **Todo lo anterior sí; cosign no** (no hay registro ni verificador en el clúster que lo consuma, así que firmar sería ceremonia). |
| **P18** | ¿Es regla dura que el repositorio y la CI usen solo datos sintéticos? | **Sí, como `NEVER`** (texto en §5): extiende el perímetro de AUTONOMIA-04 a git y a GitHub Actions sin repetirlo. |
| **P19** | ¿DAST como compuerta, o *red-teaming* de prompts + `zap-baseline` manual antes de la sustentación? | **Sin compuerta DAST**; *red-teaming* según P6; ZAP manual como COULD. |
| **P20** | ¿Fijar la revisión y el `sha256` de los modelos (Whisper, LLM, *embeddings*), con formatos sin código ejecutable y sin `trust_remote_code`, descargándolos en *build* y no en ejecución? | **Sí.** Es la cadena de suministro propia de un sistema de IA: un modelo en `pickle` ejecuta código al cargarse, y una descarga en tiempo de ejecución obligaría a abrir la salida a internet de pods con datos sensibles, lo que contradice la `NetworkPolicy` de AUTONOMIA-04. |

### 8. Lo que este aporte no decide

- La herramienta concreta de anonimización y su prueba son tema de diseño
  (Functional/NFR Design), no de prácticas. Aquí solo se fija que la prueba existe y corre
  en CI.
- El modelado de amenazas STRIDE por componente corresponde a NFR Requirements / NFR Design.
  Aquí se fija la línea base que esas etapas heredan.
- La etapa 3.7 `ci-pipeline` está en SKIP, así que nadie diseñará el *workflow* dentro de
  este flujo. Lo que se afirme aquí es la especificación que el proyecto real debe cumplir
  (misma tensión que P11 en `evidence.md`).

## Positions

- AGREE: Tronco + PR con evidencia y squash-merge (P1) — el PR es el único lugar donde se pueden ejecutar las compuertas de seguridad y donde queda registrada la aprobación de AUTONOMIA-01.
- AGREE: Etiquetar por SHA y prohibir `latest` (candidata P9) — es la base de la trazabilidad imagen↔commit; la amplío a digests para imágenes base y de terceros.
- AGREE: `helm lint` + `kubeconform` sin tocar el clúster — validación necesaria y compatible con AUTONOMIA-01.
- AGREE: Suite de *red-teaming* de inyección de prompts en Testing Posture — es la única prueba dinámica de seguridad que justifica su costo en este MVP (riesgo 7).
- AGREE: Elevar «todo en CPU» a regla dura (P13) — no tiene costo para seguridad; todas las herramientas propuestas corren en CPU.
- OBJECT: El borrador no incluye escaneo de secretos, dependencias ni imágenes — el PRD (Seg. 8 §5, Seg. 13 Módulo 7) y los riesgos 5 y 7 los requieren; sin ellos, el *lint* no protege nada de lo que importa en seguridad.
- OBJECT: `kubeconform` presentado como validación suficiente de manifiestos — solo valida el esquema; hace falta una verificación de políticas (Kyverno CLI) para `resources`, no root y la `NetworkPolicy` de AUTONOMIA-04.
- OBJECT: La tensión de P8 se plantea solo como sincronización automática vs. manual — la fusión cuenta como aprobación registrada solo si `main` está protegida también frente al administrador (hoy todo es *push* directo), y el *auto-prune* sobre la base de CloudNativePG debe quedar desactivado.
- OBJECT: `## Deployment` no dice cómo llegan los Secrets al clúster — sin una práctica explícita (referencias en manifiestos, valores creados por el humano desde un `.env` no versionado), lo más probable es que acabe un Secret en git.
- OBJECT: Falta la regla candidata «solo datos sintéticos en el repositorio y en CI» — GitHub está fuera del clúster y AUTONOMIA-04 no cubre ese perímetro.
