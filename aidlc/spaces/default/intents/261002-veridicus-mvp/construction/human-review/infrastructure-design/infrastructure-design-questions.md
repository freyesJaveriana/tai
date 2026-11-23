# Preguntas de Infrastructure Design — U5 human-review

**Unidad.** U5 `human-review` (tipo `service`): consulta de la CoT (`cot-views`), decisiones del
analista dueño (aceptar, editar, descartar) como filas nuevas de solo inserción en una ronda de
revisión, rondas para la consolidación de U7 (C11), `propose` para U4 (C10) y métricas de descarte para
la señal AIR (C15). U5 no tiene proceso propio: es un módulo de la API de `session-api`, solo usa
PostgreSQL y no llama a Redis, a modelos ni fuera del clúster (logical-components §4, security-design §1).

**Lo que ya está decidido y no se vuelve a preguntar.** De las etapas anteriores de U5: 1 réplica de la
API mientras la razón AIR se calcule en el proceso (scalability-design §4), ≤ 32 MiB de RSS sumados al
`limits.memory` de la API con ≥ 20 % de margen, migración de U5 (tablas, permisos, *trigger*, índices y
columna `change_seq`) como `Job` aparte en su propio PR, ajustes `VERIDICUS_AIR_WINDOW`,
`VERIDICUS_REVIEW_TEXT_MAX_CHARS` y `VERIDICUS_DB_LOCK_TIMEOUT_MS` en los *values* de `session-api`,
orden de bloqueo sesión → ronda (P1 = A de NFR Design), y panel AIR y regla `VeridicusAirThresholdProposal`
en U2. De esta etapa: Minikube + Calico en un solo nodo en las dos máquinas, namespace `veridicus`,
máquina de desarrollo con Minikube de 20 GiB y 10 CPU, máquina de demostración con 28 GiB, `ingress-nginx`
con TLS de `mkcert`, CloudNativePG con los roles `veridicus_owner`/`veridicus_app`/`veridicus_judge_ro`,
respaldo con `pg_dump` a pedido (antes de la sustentación y de cada cambio de esquema, U2 §6),
`kube-prometheus-stack` sin Alertmanager en el módulo 8, despliegue de `session-api` de U3 (1 réplica,
sondas con `/readyz?probe=kubernetes` sin Redis, recursos 0,5/384 MiB – 2/768 MiB, *workflow*
`session-api.yml` con `test-perf`) y límites de memoria con ≥ 20 % sobre el pico medido.

## Sin preguntas abiertas

La infraestructura de U5 cabe entera en lo ya decidido: no añade procesos, volúmenes, colas, Secrets ni
salidas de red, y los únicos valores nuevos (ajustes del `ConfigMap`, margen de memoria, índices y
métricas) ya los fijan los diseños de NFR de U5 y los de U2, U3 y U4.

---

# Segunda pasada — cambio 01, adenda 02 y NFR Design revisión vigente (2026-11-23)

## Lo que ya está decidido

- **U5 sigue sin proceso propio.** Su código corre en la API de `session-api` (rutas `decisions` y
  `observation-views`, C11 para U7, métricas de C15 v2), en el trabajador (`propose`, código de U4) y en el
  `Job` de retención de U13 (`purge_session`, C24). Solo usa PostgreSQL; ni Redis, ni modelos, ni red externa
  (NFR Design revisión 2: `logical-components.md` §1 y §4, `security-design.md` §1).
- **Lo que fija el NFR Design revisión 2 de U5:** 1 réplica de la API mientras la razón se calcule en el
  proceso; ≤ 32 MiB de RSS sumados a la API; migración de U5 como `Job` aparte en su propio PR (columnas de
  `review_round`, `review_decision`, `observations_view`, permisos de `veridicus_app` y `veridicus_retention`,
  disparadores `review_decision_round_open` y `review_round_guard`, `CHECK` con la lista de `str.isspace()` e
  índices de NFRD-U5-06); `VERIDICUS_DB_LOCK_TIMEOUT_MS` = 2000 en `session_api/shared/db.py` para todos los
  procesos (NFRD-U5-10); cifras de C25 sin variable propia (NFRD-U5-03); reconciliación de series cada 60 s.
- **Lo que ya fijaron en esta etapa U2, U3 y U4:** una sola máquina de 64 GB con Minikube de 50 GiB y 16 CPU
  (IDS-U2-01); API con 0,5/512 MiB → 2/1,125 GiB (U2 §4); `veridicus-session-api` y su `ConfigMap`
  `veridicus-session-api-config` (IDS-U2-14, U3 §1); `/readyz` completo como sonda (IDS-U3-01); reglas y
  paneles en `charts/monitoring-rules/` de U2 (IDS-U3-10), con la regla AIR `> 0.25` y los *fixtures* de U5
  (U2 `monitoring-design.md` §3); trabajador con `Recreate` y *pool* de 4 (IDS-U4-02).
- **Supuesto de máquina** (brief del 2026-11-22): una sola máquina de 64 GB, solo CPU, sin máquina GPU; el
  tamaño de Minikube lo decidió U2, la única unidad que lo pregunta.

## Cómo se registra la revisión

Revisión 2 de los cuatro artefactos de esta carpeta, que sustituye a la revisión 1 del 2026-10-03 (queda en
el historial de Git). Las secciones conservan su número; lo que sale queda «Retirado». La tabla de precisiones
de la revisión 1 (§5) se retira entera y la sustituye la tabla IDS-U5-01 en adelante; los hallazgos R-01 a
R-05 de `reviews/review-01.md` se cierran en §6 de `infrastructure-specification.md`.

## Lo que el diseño resolverá sin preguntar

- La suma de memoria de la API con U5 frente al límite de 1,125 GiB de U2.
- El nombre del `ConfigMap`, la única clave nueva de U5 y en qué procesos tiene que estar.
- El empate de `lock_timeout` y `statement_timeout` (R-03), manteniendo los 2 s aprobados.
- La regla AIR: un solo dueño (U2) y la retirada de la precisión `max by (session_id)` de la revisión 1
  (R-01), y la ventana del relevo de pods como riesgo aceptado (R-02).
- La restauración de un volcado anterior a una consolidación (R-05) y el escaneo de nivel 0 (R-04).
- Lo que U5 pide a U2 y no está en su revisión 2, como petición sin darlo por aplicado.

Sin preguntas: todo lo fijan las fuentes.
