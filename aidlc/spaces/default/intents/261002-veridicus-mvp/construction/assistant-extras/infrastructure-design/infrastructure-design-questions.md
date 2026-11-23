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

---

# Segunda pasada — cambio 01, adenda 02 y NFR Design revisión vigente (2026-11-23)

## Lo que ya está decidido

- **U8 ya no tiene extras que encender** (cambio 01). El NFR Design revisión 2 de U8 sustituye la
  permutación del juez, la pregunta sugerida y el indicio afectivo por dos cosas:
  - las **aclaraciones neutras** (US10.3), que la biblioteca arma del `hecho` sin llamar a ningún modelo;
  - la **permutación del verificador**, activa en todos los perfiles de `config/profiles.yaml` (US10.5, P5 = A).
- **Lo que cambia en el despliegue.** No hay `Deployment`, puerto, `Secret`, `ConfigMap`, ajuste
  `VERIDICUS_*` ni regla de `NetworkPolicy` nuevos (logical-components §4). Quedan:
  - una migración de dos tablas;
  - dos contadores en el puerto 8081 de `session-api`;
  - dos paneles en el JSON del panel de U4.
- **P1 = A pierde su objeto.** Ya no hay `values-extras.yaml` ni dos `Application`, porque no hay banderas
  que activar. Tampoco hay máquina de demostración aparte.
- **Supuesto de máquina** (brief del 2026-11-22). Una sola máquina de 64 GB, solo CPU y sin máquina GPU.
  Minikube tiene 50 GiB y 16 CPU, como decidió U2 (IDS-U2-01), la única unidad que lo pregunta.
- **Lo que ya fijaron en esta etapa U2, U4 y U11.**
  - Recursos de `semantic-agent` y del trabajador, `Recreate` y `/tmp` en memoria de 16 MiB (U4).
  - Puerto `metrics` 8081 y sus `ServiceMonitor` (U3 y U4).
  - `analyzer.yml` y `analyzer-level2-gate.yml` con el par de evidencia en `evaluation/reports/level2/`
    (IDS-U11-04, -07).
  - El verificador de la anfitriona con `scripts/host-verifier.sh` (IDS-U11-05).
  - El interruptor `models.todoLocalJudge.enabled` (IDS-U2-11).

## Cómo se registra la revisión

- Es la revisión 2 de los cuatro artefactos de esta carpeta. Sustituye a la revisión 1 del 2026-10-03,
  que queda en el historial de Git.
- Las secciones conservan su número, y lo que sale queda «Retirado» sin renumerar: `values-extras.yaml`,
  los dos `ConfigMap`, las banderas, la regla de plazo y reclamo, las métricas y alertas de los extras, y
  la tabla de precisiones de la revisión 1.
- Las precisiones y peticiones nuevas son IDS-U8-01 en adelante.
- Los hallazgos R-01 a R-05 de `reviews/review-01.md` se cierran en una tabla propia.

## Lo que el diseño resolverá sin preguntar

- **Memoria.** El margen de `semantic-agent` con los 5 MiB del módulo, frente al límite de U2. Hoy está en
  960 MiB y el diseño comprueba que cabe.
- **Orden de la migración.** La migración de U8 va después de las de U3 y U4, en su propio PR y como `Job`.
- **Frontera de imagen.** `session-api` depende de `libs-incoherence-analyzer` sin el *extra* `cli`, y
  nunca de `libs-anonymizer`. Se comprueba sobre su `uv.lock`.
- **Evidencia de nivel 2 de B8.** Dónde se versionan los resúmenes de solo números y qué *workflow* los
  exige.
- **Medición del costo de la permutación con `todo-local` en la máquina de 64 GB** (NFR2.2, BR6.5). Se
  ordena el procedimiento del humano para que el juez y el verificador de la anfitriona quepan en WSL2. Se
  usan los mismos digests y archivos que el clúster.
- **Peticiones a otras unidades.** Lo que U8 pide a U2, U4 y U11 y no está en sus revisiones 2 se anota
  como petición, sin darlo por aplicado.

Sin preguntas: todo lo fijan las fuentes.
