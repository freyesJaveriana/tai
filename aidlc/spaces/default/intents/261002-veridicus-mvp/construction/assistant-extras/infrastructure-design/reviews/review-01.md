## Review

**Verdict:** READY
**Reviewer:** aidlc-architecture-reviewer-agent
**Date:** 2026-10-03T11:07:01Z
**Iteration:** 1

Revisión ADVISORY de una sola pasada. Los hallazgos están ordenados por severidad y el humano decide en la aprobación.

### Findings

| ID | Severity | Location | Finding | Required action | Status |
|---|---|---|---|---|---|
| R-01 | Major | aidlc/spaces/default/intents/261002-veridicus-mvp/construction/assistant-extras/infrastructure-design/cicd-pipeline.md > §2 fila «Humo»; infrastructure-specification.md > §1.2 fila `smoke.timeoutSeconds` y §6 | El diseño convierte `scripts/smoke.sh` en `scripts/smoke.sh <url-base> --values <values de la Application>`, pero `nfr-design/performance-design.md` §5 (aprobado) dice que `smoke.sh` no cambia para U8 y que `smoke.spec.ts` comprueba primero que la sesión creada trae las tres opciones en `false`. En la máquina de demostración, con `values-extras.yaml` y banderas en `"true"`, esa comprobación falla, o el humo se salta. Además, el contrato de humo que fija `team.md` (`smoke.sh <url-base>`) y el de `text-flow/infrastructure-design/cicd-pipeline.md` §2 (120 s fijos, sin `--values`) no están en la tabla de precisiones de §6, que solo cubre el origen del tiempo de espera. Hay un cambio de interfaz en un script que pertenece a U2 y U4 sin dueño ni prueba. | Registrar en §6 la nueva opción `--values` de `smoke.sh` y el cambio de `smoke.spec.ts`. Definir cómo se espera el valor de las opciones (leídas de los values, no fijas en `false`). Añadir una prueba de nivel 0 que ejecute `smoke.sh` contra el render con extras. Mantener compatible la forma `smoke.sh <url-base>` de `team.md`. | New |
| R-02 | Major | aidlc/spaces/default/intents/261002-veridicus-mvp/construction/assistant-extras/infrastructure-design/infrastructure-specification.md > §1.1 y cicd-pipeline.md > §2 fila «Evaluación con extras» | La evidencia que enciende un extra se mide en CPU (`--profile cpu`, «corrido en CPU» según §1.1), pero `values-extras.yaml` solo se despliega con `values-gpu.yaml` en la máquina de demostración. La tasa de permutación > 65 %, la repetibilidad de NFR4.5, el `model_digest` y los picos de memoria se prueban en un perfil distinto del que corre. La tabla de topes de memoria («dentro de los topes de U4») también viene de CPU. `team.md` pide registrar el perfil CPU/GPU en el reporte, pero ningún paso exige un reporte del perfil GPU antes de activar. | Decidir y escribir una de dos opciones. Exigir en `check-eval-report.py` un reporte del perfil `gpu` para el PR de activación, o declarar que el reporte de CPU basta y que el humo y la repetibilidad se vuelven a verificar en GPU antes de la sustentación, con un comando y un umbral. | New |
| R-03 | Minor | aidlc/spaces/default/intents/261002-veridicus-mvp/construction/assistant-extras/infrastructure-design/cicd-pipeline.md > §1.1 `check-extras-values.py` | La barrera de P1 = A («la máquina de desarrollo nunca incluye los extras») solo comprueba que `veridicus-dev.yaml` no cite `values-extras.yaml` y que `values-cpu.yaml` y `values-gpu.yaml` no tengan banderas en `"true"`. No detecta que esa `Application` active un extra por `valuesObject`, `parameters` o un archivo de values distinto. `VeridicusExtrasOnDevMachine` es informativa y, según infrastructure-specification §6, depende de la etiqueta `cluster`, que cambia los values de Prometheus de otra unidad. | Ampliar la comprobación: la `Application` de desarrollo solo puede listar `valueFiles: [values-cpu.yaml]` y no puede llevar `parameters` ni `valuesObject`. Probarlo con un control negativo. | New |
| R-04 | Minor | aidlc/spaces/default/intents/261002-veridicus-mvp/construction/assistant-extras/infrastructure-design/cicd-pipeline.md > §1 fila `ai-eval-gate.yml` | El filtro de rutas incluye `values-extras.yaml`, pero no `deploy/argocd/veridicus-demo.yaml`. El PR de activación (§3 paso 5) también cambia esa `Application`. Un PR posterior que solo cambie la lista de `valueFiles` de la demostración, por ejemplo para quitar o restaurar `values-extras.yaml`, o que suba el digest del juez en `values-gpu.yaml` con extras activos, no exige un reporte de nivel 2. | Añadir `deploy/argocd/veridicus-demo.yaml` y los cambios de digest del juez a las rutas del filtro, o declarar que quedan fuera con su motivo. | New |
| R-05 | Minor | aidlc/spaces/default/intents/261002-veridicus-mvp/construction/assistant-extras/infrastructure-design/infrastructure-specification.md > §6 fila `platform/.../cicd-pipeline.md` §4.2 y §7 | La tabla de precisiones no registra que la plataforma fija 18 GiB para Minikube en la máquina de desarrollo (`platform/.../cicd-pipeline.md` §5 «Entornos»), mientras que la especificación de U8 afirma 20 GiB. El valor lo fijó U4, pero U8 lo repite como dato sin citar la precisión. | Citar en §6 la diferencia de 18 GiB (plataforma) frente a 20 GiB (U4) con su origen, o retirar la cifra de U8 y remitir a la especificación de U4. | New |

### Validation Tool Results

| Tool | Result | Interpretation |
|---|---|---|
| JSON de `traceability.json` | PASS: 60 entradas, 58 `OK` y 2 `N/A` (NFR6.1, NFR10.7, ambas justificadas como reglas de código) | Estructura válida |
| Cobertura de IDs `NFR\d+.\d+` de `assistant-extras/nfr-requirements/` | PASS: 60 IDs en los requisitos, 0 ausentes en los artefactos o en la trazabilidad | Cobertura completa |
| P1 = A frente a los artefactos | Coherente: dos `Application`, la de desarrollo sin `values-extras.yaml`, render con extras en CI y alerta `VeridicusExtrasOnDevMachine` | Con la salvedad de R-03 y R-04 |
| Permutación frente a la ranura única y U4 | Coherente: 3 llamadas en serie, p95 ≤ 150 s, 24 turnos en cola, plazo 600 s, reclamo 510 s > 482,2 s, topes de memoria de U4 sin cambios | Con la salvedad de R-02 (medido en CPU) |
| Puertas con comando y umbral (AUTONOMIA-02) | PASS: las 13 filas de §2 llevan comando y umbral | Cumple |
| AUTONOMIA-01, -04 y -05 | PASS: CI sin `kubeconfig`, aplicación por el humano o por Argo CD tras el PR, sin destinos nuevos, tabla de frontera por componente, 0 preguntas en el caso de Hecho No Documentado | Cumple |
| Precisiones sin editar originales | PASS en el principio (tabla §6); incompleta por R-01 y R-05 | Ver hallazgos |
| Fragmentos ≤ 15 líneas | PASS: el bloque YAML de §1.2 tiene 13 líneas y el diagrama Mermaid cuenta con texto alternativo | Cumple |

### Summary

El diseño es implementable: no añade procesos, cubre los 60 requisitos NFR y sostiene P1 = A con comprobaciones en CI. Antes de aprobar, el humano debería pesar dos puntos. El primero es la interfaz nueva de `smoke.sh` y su choque con la comprobación de «opciones en false» del humo aprobado (R-01). El segundo es que la evidencia para activar los extras se mide en CPU y se despliega en GPU (R-02).
