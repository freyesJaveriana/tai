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
