# Preguntas de Infrastructure Design — U8 assistant-extras

**Unidad.** U8 `assistant-extras` (tipo `service`, SHOULD/COULD): permutación del orden de lectura,
pregunta sugerida con aprobación del analista e indicio afectivo, los tres apagados por defecto. No
añade procesos, modelos, colas, puertos ni reglas de `NetworkPolicy`: vive dentro de `semantic-agent`
y de la API y el trabajador de `session-api` (U4), usa la misma ranura única del juez y suma dos
`ConfigMap` de solo lectura (*prompt* de la pregunta y lista afectiva) y una migración de dos tablas.

**Lo que ya está decidido y no se vuelve a preguntar.** Minikube con Calico en las dos máquinas, un
namespace `veridicus`, la máquina de desarrollo con 20 GiB y 10 CPU para Minikube y la de demostración
(32 GB) con 28 GiB; límites de memoria con ≥ 20 % sobre el pico medido; respaldo con `pg_dump` a pedido;
sonda de disponibilidad de `session-api` sin Redis; kube-prometheus-stack sin Alertmanager; GHCR
privado y PR de despliegue (Infrastructure Design de U2, U3 y U4). El costo de CPU de la permutación
frente a la ranura única también está resuelto: hasta tres llamadas en serie al juez por turno, p95
≤ 150 s, 24 turnos en cola sin vencer, una sola sesión a la vez con extras y los topes de memoria de U4
sin cambios (diseño de NFR de U8). Igual el plazo base de 600 s y el reclamo de 510 s cuando hay
extras activos, las banderas solo en los *values* y por PR con el reporte de nivel 2, la prueba de humo
con extras apagados (120 s) o con 300 s si un despliegue los activa, y la evaluación de nivel 2 con
`--extras all` por `port-forward`, que no cambia nada del clúster.

Queda una decisión.

---

## P1 — En qué máquina se encienden los extras para que el analista los vea en la consola

El diseño deja las tres banderas en `false` en `values-cpu.yaml` y `values-gpu.yaml`, y la corrida de
nivel 2 los mide sin tocar el clúster. Pero la demo esperada del Bolt B8 es que, en un turno con
discrepancia, el analista **vea una pregunta sugerida en la consola**, la apruebe y la use; para eso
algún despliegue tiene que llevar las banderas en `true` (con plazo base 600 s, reclamo 510 s y humo a
300 s). Nadie ha fijado cuál, y de eso dependen la `Application` de Argo CD de cada máquina, los renders
que la CI valida y dónde se miden la carga de NFR8 y el humo con los extras apagados.

A. Un archivo aparte `values-extras.yaml` (banderas, plazo, reclamo y tiempo del humo) que se suma a
   `values-gpu.yaml` en la `Application` de la máquina de demostración, de forma permanente desde que
   un PR adjunta el reporte de nivel 2 con extras que cumple sus umbrales (cada extra se enciende solo
   si pasa los suyos; la permutación, solo con > 65 % de afirmaciones sostenidas). La máquina de
   desarrollo nunca lo incluye, así que allí la carga de NFR8 y el humo siempre corren con los extras
   apagados. La CI renderiza también la combinación `values-gpu.yaml` + `values-extras.yaml`.
   (Recomendada)
B. El mismo `values-extras.yaml`, pero ninguna máquina lo incluye de forma permanente: para cada ensayo
   y para la sustentación un PR lo añade a la `Application` de la máquina que se use, y después un
   `git revert` lo quita. Las dos máquinas quedan normalmente con los extras apagados, a cambio de dos
   PR por cada ensayo.
C. Sin despliegue con extras en el MVP: las banderas siguen en `false` en todas partes y B8 se demuestra
   con el reporte de nivel 2 y una grabación de Playwright con el juez *fake*. Es lo más simple, pero
   el analista no ve los extras en la consola real, como pide la demo de B8.
X. Other (please specify)

[Answer]: A **Mode:** guided
