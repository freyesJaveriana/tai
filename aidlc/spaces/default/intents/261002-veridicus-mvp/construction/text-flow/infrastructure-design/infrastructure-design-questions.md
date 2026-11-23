# Preguntas de Infrastructure Design — U4 text-flow

**Unidad.** U4 `text-flow` (sin tipo): carga e indexación de escenarios, sesiones, turnos de texto,
evaluación con la guardia del umbral y el juez, ingesta de resultados y consola M2–M4. Despliega la API
y el trabajador de `session-api`, `semantic-agent` y usa los servidores de modelos de U2.

**Lo que ya está decidido y no se vuelve a preguntar.** Procesos separados (API, trabajador y
`semantic-agent`), un turno a la vez con una sola ranura del juez, pools de conexión, *timeouts*,
reintentos acotados del juez, plazos, colas con grupos de consumidores, `ConfigMap` del *prompt* con su
SHA-256 y puertos internos de métricas (diseños de `nfr-design/`); Minikube con 18 GiB y 10 CPU, un
namespace `veridicus` y los servidores de modelos de U2 (Infrastructure Design de U2, ya respondido).

Queda una decisión.

---

## P1 — Margen de memoria de los pods de IA

El diseño de NFR de U4 (performance-design §7) pide que cada `limits.memory` deje **al menos un 20 %**
sobre el pico medido: juez ≤ 7 GiB, *embeddings* ≤ 1,5 GiB, `semantic-agent` ≤ 512 MiB y trabajador de
`session-api` ≤ 768 MiB. Los valores que fijó U2 dejan poco o ningún margen (juez con límite de
7,5 GiB), y la revisión de U2 lo señaló: con esos valores, el pico declarado ya acerca el pod a un
corte por memoria. Con el 20 % los límites suben ≈ 2 GiB en total; la suma de los `requests` sigue
cabiendo en Minikube, pero la de los `limits` pasa de ≈ 19 GiB a ≈ 21 GiB.

A. Aplicar el 20 % y subir Minikube a 20 GiB, dejando 4 GiB al sistema anfitrión: juez 8,5 GiB,
   *embeddings* 1,8 GiB, `semantic-agent` 640 MiB y trabajador 960 MiB. Menos memoria para el
   navegador y el escritorio de la demostración.
B. Aplicar el 20 % y mantener Minikube en 18 GiB: mismos límites que A; la suma de `limits` supera la
   memoria en ≈ 3 GiB, aceptable porque solo el juez se acerca a su pico, y durante la corrida de carga
   de NFR8 se apaga el monitoreo (SHOULD). Los valores de U2 quedan precisados en la tabla de
   precisiones. (Recomendada)
C. Mantener los valores de U2 sin margen; el requisito de performance-design §7 queda en la tabla de
   precisiones como no cumplido.
X. Other (please specify)

[Answer]: X. La máquina demo tiene 32 gb ram. Puedes dejar 4 gb al sistema y el resto distribuirlo en el cluster **Mode:** guided

## P2 — Seguimiento de P1: la máquina de desarrollo

En P1 respondiste que la máquina de la demostración (la de 32 GB) deja 4 GB al sistema y el resto al
clúster, es decir, Minikube con 28 GiB allí; con eso los límites con el 20 % de margen caben holgados.
Falta saber qué hacemos en la máquina de desarrollo de 24 GB, donde hoy Minikube tiene 18 GiB.

A. Misma regla: dejar 4 GB al sistema y dar 20 GiB a Minikube. Los límites con el 20 % casi caben
   (≈ 21 GiB de límites frente a 20 GiB) y los `requests` sobran.
B. Mantener 18 GiB en la máquina de desarrollo: los límites con el 20 % la superan en ≈ 3 GiB y durante
   la corrida de carga de NFR8 se apaga el monitoreo; la demostración y la carga completa se hacen en la
   máquina de 32 GB.
X. Other (please specify)

[Answer]: A **Mode:** guided

---

# Segunda pasada — cambio 01, adenda 02 y NFR Design revisión vigente (2026-11-23)

## Lo que ya está decidido

- **U4 ya no tiene juez, *embeddings*, umbral ni escenario** (cambio 01). Orquesta las corridas de la
  biblioteca de U11 (C17) en `semantic-agent`, con la cola C2/C3 en Redis, y despliega la API y el
  trabajador de `session-api` y la consola. Lo fija el NFR Design revisión 2 de U4: dos procesos de la
  misma imagen, una réplica de cada uno, una corrida a la vez, `semantic-agent` sin base ni claves de
  proveedor y sin `libs-anonymizer`, y los picos de `performance-design.md` §7.
- **Lo que trae el NFR Design de otras unidades a U4:** el cuarto hilo `SessionSupervisor` y el *pool* de 4
  del trabajador (NFRD-U6-05); `XTRIM` del *stream* de audio desde el supervisor (NFRD-U9-05); el piso de
  270 s (NFRD-U4-09); `VERIDICUS_RELEASE_POLL_MS` y `VERIDICUS_PUBLISH_RETRIES` (NFRD-U4-14); las métricas en
  `contracts/metrics/text-flow.v1.yaml` (NFRD-U4-08); y las peticiones de U5, U6, U8, U9 y U13 (NFRD-U5-07,
  NFRD-U6-06/07/15, NFRD-U8-02/08/11/12, NFRD-U9-01/05/08, NFRD-U13-05/06).
- **Lo que ya fijaron en esta etapa U2, U3, U10 y U11:** recursos del trabajador (0,25/384 MiB → 1/640 MiB) y
  de `semantic-agent` (0,25/512 MiB → 1/960 MiB), `veridicus-session-api` y `connectionLimit: 25`
  (IDS-U2-14), el `ConfigMap` `veridicus-profiles` montado en `session-api` y `semantic-agent`, los
  servidores locales con 8 hilos (IDS-U2-03), y la sustitución de `libs.yml` y `ai-eval-gate.yml` por los
  *workflows* de U11 (IDS-U11-08), con el nivel 2 como par versionado en `evaluation/reports/level2/`
  (IDS-U11-04).
- **Supuesto de máquina** (brief del 2026-11-22): una sola máquina de 64 GB, solo CPU, sin máquina GPU. El
  tamaño de Minikube lo decidió U2 (50 GiB y 16 CPU), que es la única unidad que lo pregunta.

## Cómo se registra la revisión

Revisión 2 de los cuatro artefactos de esta carpeta, que sustituye a la revisión 1 del 2026-10-03 (queda en
el historial de Git). Lo que sale queda «Retirado» con su número. Las precisiones nuevas son IDS-U4-01 en
adelante, en §7 de `infrastructure-specification.md`, y los hallazgos R-01 a R-07 de `reviews/review-01.md`
se cierran en §8.

## Lo que el diseño resolverá sin preguntar

- La estrategia de actualización de `semantic-agent` y del trabajador, y su apagado ordenado, para respetar
  una corrida a la vez (NFR8.7) y cerrar R-01 de la revisión 1.
- El presupuesto de conexiones de `veridicus_app` con el cuarto hilo del trabajador, frente al
  `connectionLimit: 25` de U3 y U2.
- Las sondas, el `/tmp` en memoria y los ajustes `VERIDICUS_*` de cada proceso a partir del NFR Design.
- La retirada de lo que la revisión 1 ponía en U4 y ahora es de U11 o sale (juez, *embeddings*, *prompt*,
  indexación, nivel 2 por `port-forward`, `libs.yml`, `ai-eval-gate.yml`).
- Lo que U4 pide a U2 y no está en su revisión 2, como petición sin darlo por aplicado.

Sin preguntas: todo lo fijan las fuentes.
