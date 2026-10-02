# Dependencias externas — Veridicus (MVP)

**Insumos.** Bolts de `bolt-plan.md`; prácticas de
`inception/practices-discovery/team-practices.md` (team-practices); dependencias externas de los
componentes en `inception/domain-design/components.md` (components); servidores de modelos (C14) en
`inception/contract-design/contract-summary.md` (contract-summary); NFR y restricciones de
`inception/requirements-analysis/requirements.md` (requirements); plan del curso (PRD S13);
respuestas P6 y P7 de `delivery-planning-questions.md`.

Un **Bolt** es una pasada de construcción sobre una o varias unidades que termina en algo demostrable
(ver `bolt-plan.md`). Este documento lista lo que está fuera del control del equipo y puede frenar un
Bolt. Todo el sistema corre dentro del clúster local (AUTONOMIA-04), así que ninguna dependencia es una
API externa en tiempo de ejecución.

## Dependencias con seguimiento (P7: A, C, D, E)

| # | Dependencia | Dueño | Plazo o tiempo de espera | Bolts que bloquea | Si se retrasa |
|---|---|---|---|---|---|
| D1 | **Calendario del curso**: módulo 6 (sem. 10–11), módulo 7 (sem. 12–13), módulo 8 (sem. 14) y sustentación en la sesión 16 (PRD S13) | Docente del curso | Fijo; no lo controla el equipo | B4 (contenido de los módulos 6–8); todos los MUST deben cerrar antes de la sesión 16 | Se aplica la línea de corte: la demo queda completa en B6; B7 se recorta en alcance antes que B1–B6, y ningún SHOULD empieza (P5). Ninguna prueba ni umbral se rebaja. |
| D2 | **Máquina GPU** opcional (hasta 4 GPU, 32 GB de RAM) | Autor | A demanda; disponibilidad no garantizada | Ninguno de forma obligatoria; respalda la evaluación con modelos más grandes y el ensayo de la demo | Todo funciona y se prueba en CPU (NFR2); sin GPU solo se pierde la etapa separada del perfil GPU, que nunca bloquea niveles 0 y 1. |
| D3 | **Descarga de modelos** (juez cuantizado ≤ 8B, *embeddings* multilingües, Whisper `tiny`/`base`, TTS) con revisión fijada y `sha256`, en formatos sin código ejecutable | Proveedores de los modelos (repositorios públicos) | Una vez por revisión; tamaño a medir frente al disco y la memoria de la máquina CPU | B3 (juez y *embeddings*), B4 (servidores en el clúster), B9 (Whisper y TTS) | Se descargan en *build* o aprovisionamiento, nunca en ejecución (team-practices). Si un modelo no cabe en la máquina CPU, NFR Requirements elige otro de la misma clase antes de B3; si cambia su revisión, se fija la anterior por `sha256`. |
| D4 | **Configuración de GitHub**: protección de `main`, comprobaciones obligatorias, GHCR privado, *deploy key* de solo lectura, permisos de Actions y Dependabot | Autor + agente (tarea conjunta P0.1) | Antes de cualquier desarrollo | Todos (B1 en adelante) | No empieza ningún desarrollo hasta validarla con el PR de prueba y el *push* rechazado (team-practices). |

## Dependencia interna previa con riesgo externo

| # | Dependencia | Dueño | Plazo | Bolts que bloquea | Si se retrasa |
|---|---|---|---|---|---|
| D5 | **Golden Dataset** generado con un modelo comercial de otra familia que el juez (P6) | Autor (usa la API de un proveedor solo con datos sintéticos) | Tarea previa P0.2, antes de cerrar B3 | B3 (evaluación de nivel 2), B7 (NFR8), B8 (permutación) | B3 puede avanzar en niveles 0 y 1 con *fakes* deterministas, pero no cierra sin la evaluación de nivel 2. Si la API no está disponible, el autor escribe el dataset a mano (P6, opción B) y lo declara en el manifiesto. |

## Sin seguimiento

- **Par del curso que califica la CoT (NFR6).** No se marcó en P7: queda como riesgo bajo sin
  seguimiento. Sigue siendo parte de la verificación manual antes de la sustentación
  (team-practices, nivel manual).
- **Imágenes de terceros** (CloudNativePG, Redis, Argo CD, Prometheus, Grafana, KEDA): versión de
  chart fijada y, cuando se puede, digest (team-practices); no se espera bloqueo.
