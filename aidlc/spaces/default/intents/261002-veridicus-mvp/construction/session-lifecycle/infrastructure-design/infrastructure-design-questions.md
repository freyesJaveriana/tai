# Preguntas de Infrastructure Design — U6 session-lifecycle

**Unidad.** U6 `session-lifecycle` (tipo `service`): versiones nuevas de escenarios, transcripción
pegada con publicación por lote en la cola de turnos, lista de sesiones, latido del dueño, suspensión
automática (`SuspensionSweeper`) y reanudación, y progreso del turno en la consola. No añade procesos:
todo corre en la API y en el trabajador de `session-api` y en `frontend`, que ya despliegan U3 y U4
(`nfr-design/logical-components.md` §4).

**Lo que ya está decidido y no se vuelve a preguntar.** La infraestructura común de U2 (Minikube con
Calico en un solo nodo en las dos máquinas, namespace `veridicus`, `ingress-nginx` con TLS de mkcert y
`proxy-body-size` ≥ 1 MiB, CloudNativePG con sus roles, Redis 7.2 con AOF `everysec`, `maxmemory 384mb`
y `noeviction`, kube-prometheus-stack sin Alertmanager en el módulo 8, `pg_dump` a pedido, GHCR privado
y PR de despliegue); el despliegue de `session-api` de U3 (1 réplica, `readinessProbe` con
`/readyz?probe=kubernetes` sin Redis, recursos 0,5 CPU / 384 MiB – 2 CPU / 768 MiB, *workflow*
`session-api.yml`); el trabajador `session-api-worker`, `semantic-agent`, `frontend`, los límites con
≥ 20 % sobre el pico medido, Minikube con 20 GiB / 10 CPU en la máquina de desarrollo y 28 GiB en la de
demostración, y la evaluación de nivel 2 por `port-forward` de U4. De esta unidad ya están aprobados:
*T* = 180 s, revisión cada 30 s y escritura del latido como máximo cada 15 s con la hora de la base;
límite de 60 turnos de testimonio y 200 en total; la marca de lote `veridicus:paste-published:` con
expiración de 24 h dentro de `MULTI`/`EXEC` (P1 = A de NFR Design); latido y revisión con
`FOR UPDATE SKIP LOCKED` (P2 = A de NFR Design); los tres ajustes de U6 leídos por API y trabajador
desde el mismo `ConfigMap`; migraciones aditivas en un `Job` aparte; la corrida de 60 turnos a demanda
antes de cada entrega etiquetada; y que ningún componente de U6 sale del clúster ni añade reglas de
salida.

## Sin preguntas abiertas

Cada necesidad de infraestructura de U6 (Redis sin desalojo, recursos, red, sondas, métricas, migración
y CI) ya la fijan los insumos aprobados o la infraestructura de U2, U3 y U4; lo que queda son ajustes
que se derivan sin decisión humana (un cuarto hilo en la sonda del trabajador, el filtro de rutas de
`frontend.yml` para el archivo de división compartido y la versión de `veridicus_now()` instalada en el
clúster), y se registran en los artefactos con su tabla de precisiones.

---

# Segunda pasada — cambio 01, adenda 02 y NFR Design revisión vigente (2026-11-23)

## Lo que ya está decidido

- **U6 sigue sin procesos propios** (NFR Design revisión 2, `logical-components.md` §4): todo corre en la API
  y el trabajador de `session-api` y en `frontend`. Sale la versión nueva de un escenario, la marca de lote en
  Redis y `noeviction` por esa marca; `SuspensionSweeper` pasa a `SessionSupervisor`, cuarto hilo del
  trabajador con su conexión (NFRD-U6-05). Entran la importación con lector `multipart` en memoria, el modo
  final, la pausa, la terminación, la retirada y la cancelación por las claves de U4.
- **Cifras de U6 en C25**, no en el `ConfigMap`: `heartbeat_timeout_s` 180, `session_sweep_interval_s` 30,
  `heartbeat_write_min_s` 15, `import_file_max_bytes` y los topes de cuerpo de NFRD-U6-01; una
  `VERIDICUS_LIMIT_<NOMBRE>` solo baja.
- **Plazo de inactividad** por transacción con `SET LOCAL` (5 s en U6), nunca en el `Cluster` `veridicus-pg`
  ni en el rol (NFRD-U7-01; regla de `project.md`).
- **Lo que ya fijaron en esta etapa U2, U3, U4, U10 y U11:** una sola máquina de 64 GB, solo CPU, con
  Minikube de 50 GiB y 16 CPU (IDS-U2-01) y sin `values-gpu.yaml` (IDS-U2-02); API 0,5/512 MiB → 2/1,125 GiB;
  trabajador 0,25/384 MiB → 1/640 MiB con `Recreate` y *pool* de 4 (IDS-U4-02, IDS-U4-06); `connectionLimit`
  30 pedido a U2 (IDS-U4-03); `readinessProbe` de la API con el `/readyz` completo (IDS-U3-01); Ingress
  `veridicus-web` sin disco con tope de 2 113 536 bytes (U2 §2.4); `test-perf` en `ubuntu-24.04` (IDS-U3-09);
  `frontend.yml` con `contracts/**` en su filtro y el patrón `changes` + `gate` (U4).

## Cómo se registra la revisión

Revisión 2 de los cuatro artefactos de esta carpeta, que sustituye a la revisión 1 del 2026-10-03 (queda en el
historial de Git). Las secciones conservan su número; lo que sale queda «Retirado». La tabla de precisiones de
la revisión 1 (§6) se retira entera y la sustituye la tabla IDS-U6-01 en adelante (§6 de
`infrastructure-specification.md`); §7 cierra los hallazgos R-01 a R-04 de `reviews/review-01.md`.

## Lo que el diseño resolverá sin preguntar

- La memoria de la API y del trabajador con lo que U6 añade (≤ 100 MiB en la API), frente a los límites que ya
  fijó U2.
- El alcance del plazo de inactividad y el presupuesto de conexiones con el cuarto hilo.
- La migración de B7 (tabla, columnas, disparadores, índices y permisos, incluido `DELETE` para la retención).
- La retirada de lo que la revisión 1 ponía en U6 y ya no existe (tres ajustes `VERIDICUS_HEARTBEAT_*`,
  `veridicus_now()`, marca de lote, `values-gpu.yaml`, nivel 2 por `port-forward`, métricas y alertas viejas).
- Lo que U6 pide a U2 y no está en su revisión 2, como petición sin darlo por aplicado.

Sin preguntas: todo lo fijan las fuentes.
