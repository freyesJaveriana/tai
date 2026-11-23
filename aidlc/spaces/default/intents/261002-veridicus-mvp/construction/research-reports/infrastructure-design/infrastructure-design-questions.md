# Preguntas de Infrastructure Design — U12 research-reports

**Unidad.** U12 `research-reports` (tipo `service`): la consola del investigador (M8) y las rutas
`/research-reports*` de `session-api`, que reciben el reporte C19 de la CLI y guardan solo metadatos y
cifras. U12 no despliega ningún proceso propio: su código corre en la API de `session-api` (U3) y en la
imagen `frontend` (U4). Es la **primera pasada** de esta etapa para U12; no hay revisión anterior que
sustituir.

---

# Segunda pasada — cambio 01, adenda 02 y NFR Design revisión vigente (2026-11-23)

## Lo que ya está decidido

- **NFR Design de U12, revisión 1 (aprobado):** tres transacciones cortas en la subida (NFRD-U12-01),
  plazo de lectura de 30 s (NFRD-U12-02), *bulkhead* de 2 huecos con espera de 5 s (NFRD-U12-04), pico de
  ≈ 230 MiB por subida y ≤ 512 MiB con dos (NFR3.8), validación en un hilo con su limitador, ninguna métrica
  nueva, ningún camino de red hacia fuera y un catálogo de referencia que se carga al arrancar. La entrega a
  Infrastructure Design está en `logical-components.md` §5: sumar 512 MiB con el 20 % de margen al
  `limits.memory` de la API, sumar ≤ 1,5 GiB por cada 1 000 reportes al volumen de PostgreSQL y montar el
  catálogo de solo lectura (NFR-U12-06).
- **Lector `multipart` en memoria compartido de U6** (`session_api/shared/multipart_memory.py`, lo entrega
  B7 y U12 lo reutiliza en B12 con su propio tope; NFRD-U6-10 aprobado).
- **Lo que ya fijaron en esta etapa U2, U3, U4, U10 y U11:** un solo equipo de 64 GB, solo CPU, con
  Minikube de 50 GiB y 16 CPU (IDS-U2-01); el `Ingress` `veridicus-research-reports` con tope de
  8 454 144 bytes, sin disco y `proxy-read-timeout 30s` (U2 §2.4); `veridicus-session-api` con 1 réplica,
  `RollingUpdate`, `/tmp` en memoria de 16 MiB y la API en 0,5 / 512 MiB → 2 / 1,125 GiB (U2 §4, U3 §1.1);
  el `ConfigMap` `veridicus-profiles` montado en `session-api` (IDS-U4-09); los *workflows*
  `session-api.yml` (U3) y `frontend.yml` (U4) con el patrón `changes` + `gate`.
- **Supuesto de máquina** (brief del 2026-11-22): una sola máquina de 64 GB, solo CPU, sin máquina GPU; el
  tamaño de Minikube lo decidió U2, la única unidad que lo pregunta.

## Cómo se registra la revisión

Revisión 1 de los cuatro artefactos de esta carpeta (`infrastructure-specification.md`,
`monitoring-design.md`, `cicd-pipeline.md` y `traceability.json`). Las precisiones a artefactos aprobados y
las peticiones a otras unidades son IDS-U12-01 en adelante, en §7 de `infrastructure-specification.md`.
Ninguna petición se da por aplicada.

## Lo que el diseño resolverá sin preguntar

- La comprobación de que la memoria actual de la API **no alcanza** para dos subidas máximas
  (944 MiB + 460 MiB > 1 152 MiB) y la petición a U2 del nuevo `limits.memory`, con el efecto en el
  presupuesto de Minikube: lo fija NFR3.8 y lo entrega `logical-components.md` §5.
- El empaquetado del catálogo de referencia (perfiles y precios desde `veridicus-profiles`; listas de
  etiquetas dentro de la imagen), que NFR-U12-06 deja abierto entre imagen y `ConfigMap`.
- La adopción del lector compartido de U6 en lugar de un lector propio de U12.
- El plazo de inactividad de la transacción de escritura, que U7 dejó a U12 como nota.
- La comprobación de que el `Ingress` de U2 y el volumen de PostgreSQL bastan sin cambios.
- Los *jobs* que U12 suma a `session-api.yml`, `frontend.yml` y `deploy-level0.yml`, y la regla de
  memoria de la API.

Sin preguntas: todo lo fijan las fuentes.
