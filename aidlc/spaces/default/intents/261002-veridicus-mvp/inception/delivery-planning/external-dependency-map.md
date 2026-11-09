# Dependencias externas — Veridicus (MVP)

**Revisión 2 (2026-11-09), segunda pasada por el cambio 01 (DT27) y la adenda 02.** Sustituye a la
revisión 1. Conserva D1–D4 (D3 cambia de modelos), marca D5 «Retirado» y añade D6 y D7 (P14 = A, B, C,
D).

**Insumos.** Bolts de `bolt-plan.md`; prácticas de `inception/practices-discovery/team-practices.md` y
`team.md` (team-practices); dependencias externas de los componentes en
`inception/domain-design/components.md` (components); contratos C14 y C22 en
`inception/contract-design/contract-summary.md` (contract-summary); NFR de
`inception/requirements-analysis/requirements.md` (requirements); plan del curso (PRD S13); respuestas P6,
P7 y P14 de `delivery-planning-questions.md`.

Un **Bolt** es una pasada de construcción sobre una unidad que termina en algo que corre y se puede
demostrar (ver `bolt-plan.md`). Este documento lista lo que está fuera del control del equipo y puede
frenar un Bolt. Desde el cambio 01 sí hay APIs externas en tiempo de ejecución: los proveedores
comerciales, solo detrás del anonimizador y solo con texto seudonimizado (AUTONOMIA-04, C22).

## Dependencias con seguimiento (P14: A, B, C, D)

| # | Dependencia | Dueño | Plazo o tiempo de espera | Bolts que bloquea | Si se retrasa |
|---|---|---|---|---|---|
| D1 | **Calendario del curso**: módulo 6 (sem. 10–11), módulo 7 (sem. 12–13), módulo 8 (sem. 14) y sustentación en la sesión 16 (PRD S13) | Docente del curso | Fijo; no lo controla el equipo | B4 (contenido de los módulos 6–8), B10 (anonimizador en el módulo 7); todas las MUST deben cerrar antes de la sesión 16 | Se recorta en el orden de P13: B13 → partes SHOULD/COULD de B4 y B7 → alcance de B7. La demo queda completa en B6. Nunca se recortan B1, B10, B11 ni B2–B6, ni se rebaja una prueba o un umbral. |
| D3 | **Descarga de modelos locales** (juez y verificador de familias distintas, Whisper y TTS) con revisión fijada y `sha256`, en GGUF o `safetensors` y sin `trust_remote_code` | Proveedores de los modelos (repositorios públicos) | Una vez por revisión; tamaño frente al disco y la memoria de cada máquina | B11 (perfil local de la primera rebanada), B4 (servidores en el clúster), B9 (Whisper y TTS) | Se descargan en *build* o aprovisionamiento, nunca en ejecución (team-practices). Si un modelo no cabe, NFR Requirements elige otro de la misma clase antes del Bolt; si cambia su revisión, se fija la anterior por `sha256`. Las cifras de los modelos locales vienen de la validación en ZINE (`docs/validacion-zine/`). |
| D6 | **Cuenta y clave de API del proveedor comercial** de la primera rebanada (US13.6) y, después, de los otros dos (US13.7) | Autor (crea la clave y el `Secret` desde un `.env` no versionado) | Antes de la evaluación de nivel 2 de B11 | B10 (prueba de punta a punta del proxy), B11 (nivel 2 con el perfil comercial), B4 (`Secret` en el clúster) | Los niveles 0 y 1 usan respuestas grabadas sin red y no se bloquean. Sin clave, B11 no cierra su nivel 2 con el perfil comercial; se vigila el costo por corrida con el registro de US12.5. |
| D7 | **Clúster ZINE** (cola SLURM, nodos `ingsistemas`) | Administradores de ZINE; los `sbatch` los lanza el humano (AUTONOMIA-01) | A demanda; la cola no está garantizada | Ninguno de forma obligatoria: B11 entrega los scripts y el paquete de entrada (US14.2, US14.3) como artefactos revisables | Las mediciones de modelos locales grandes se corren cuando haya cupo; no bloquean el cierre de B11, que mide en la máquina local. |

## Dependencias internas que no requieren seguimiento aparte

| # | Dependencia | Estado |
|---|---|---|
| D2 | Máquina GPU opcional (hasta 4 GPU, 32 GB de RAM) | Sin seguimiento (P14 no la marcó). Todo funciona y se prueba en CPU (NFR2); sin GPU solo se pierde la etapa separada del perfil GPU, que nunca bloquea los niveles 0 y 1. |
| D4 | Configuración de GitHub (P0.1) | Sin seguimiento como dependencia externa (P14 no la marcó): sigue siendo tarea previa obligatoria de `team.md` y bloquea B1 hasta validarse con el PR de prueba y el *push* rechazado. |
| D5 | Golden Dataset con escenario (P0.2) | **Retirado** (P12 = A): el conjunto sintético se construye dentro de B11. |

## Sin seguimiento

- **Par del curso que califica las observaciones (NFR6).** Riesgo bajo sin seguimiento; sigue siendo
  parte de la verificación manual antes de la sustentación (team-practices, nivel manual).
- **Imágenes de terceros** (CloudNativePG, Redis, Argo CD, Prometheus, Grafana, KEDA): versión de chart
  fijada y, cuando se puede, digest (team-practices); no se espera bloqueo.
- **Contrato común del TG**: su fuente vive en el repositorio principal del TG (ADR-017); un cambio de
  versión mayor entra por su propio PR a U1 y no se espera durante el MVP.
