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
