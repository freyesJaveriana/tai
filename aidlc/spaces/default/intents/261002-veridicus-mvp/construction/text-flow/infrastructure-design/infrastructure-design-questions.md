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
