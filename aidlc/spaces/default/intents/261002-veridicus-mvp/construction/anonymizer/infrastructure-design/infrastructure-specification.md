# Especificación de infraestructura — U10 anonymizer

**Insumos.** De `nfr-design/` de esta unidad: performance-design §5 (recursos del pod),
security-design §1, §4–§6 y §10 (frontera, reglas, políticas, superficie y verificación manual),
scalability-design §1 (réplicas y semáforo), reliability-design §2 y §5 (plazos y sondas),
observability-design §2 (puerto de métricas) y logical-components §4 (entrega a Infrastructure Design:
recursos, volúmenes, Secret, volcados de memoria, T15 y CIDR estables). También:
`functional-design/functional-spec.md` (functional-spec §1 y §7), ModelGateway y la frontera del
clúster de `inception/domain-design/components.md` (components), C13, C14 y C16 de
`inception/contract-design/contract-summary.md` (contract-summary), D1 y los ajustes de
`nfr-requirements/tech-stack-decisions.md`, la respuesta **P1 = A** de
`infrastructure-design-questions.md` (CoreDNS con lista blanca), Infrastructure Design de U2 (Minikube
con Calico, `veridicus` con negar todo, `create-secrets.sh`) y de U4 (20 GiB y 10 CPU en desarrollo,
28 GiB en demostración, margen de memoria ≥ 20 %), y `## Deployment` de `team.md`.

U10 se entrega **apagado**: con los *values* de `main` el chart no renderiza ningún recurso del proxy
y este documento describe lo que rige el día que un PR con ADR lo habilite. El chart, el `Corefile` y
los *scripts* se escriben en Code Generation; aquí se fijan su forma y sus valores.

## 1. Despliegue

| Facet | Choice | Rationale |
|---|---|---|
| Modelo de cómputo | Contenedor en el clúster Minikube de U2: `Deployment` `veridicus-anonymizer-proxy` en el subchart `anonymizer-proxy` del chart paraguas, renderizado solo con `anonymizer.enabled: true` | D1 (apagado por defecto, NFR1.1); mismo chart en las dos máquinas |
| Réplicas | 0 por defecto (no se renderiza); 1 al habilitar; sin HPA ni `PodDisruptionBudget` | scalability-design §1: el cuello de botella es el juez; un solo nodo |
| Proceso | Un proceso Uvicorn, semáforo de 4 llamadas (`VERIDICUS_ANONYMIZER_MAX_CONCURRENCY`, 1–8); puerto 8080 para C14 y 8081 para `/healthz`, `/readyz` y `/metrics` | D5; security-design §6 |
| Estrategia de actualización | `RollingUpdate` con `maxSurge: 1`, `maxUnavailable: 0`; `terminationGracePeriodSeconds: 180` | Deja terminar una llamada `judge` en curso (≤ 174 s, reliability-design §2) |
| Sondas | `livenessProbe` `/healthz` y `readinessProbe` `/readyz` en 8081 (periodo 10 s, 3 fallos); `startupProbe` `/readyz` con 30 intentos de 2 s | reliability-design §5: `/readyz` nunca abre conexiones salientes (NFR10.7) |
| Imagen | `ghcr.io/<dueño>/veridicus-anonymizer-proxy` por digest, construida en CI con la etiqueta del SHA; base Python 3.12 mínima por digest con su paquete `ca-certificates` | team.md `## Deployment`; la verificación TLS (NFR10.5) usa las CA públicas de la imagen |
| Contexto de seguridad | `runAsNonRoot`, UID 10001, `readOnlyRootFilesystem`, `allowPrivilegeEscalation: false`, `capabilities.drop: [ALL]`, `seccompProfile: RuntimeDefault`, `automountServiceAccountToken: false`, sin `hostNetwork`/`hostPath`/`hostPID` | Pod Security `restricted` de U2; `veridicus-anonymizer-hardening` (NFR10.10) |
| Volcados de memoria | El arranque fija `RLIMIT_CORE = 0` y `prctl(PR_SET_DUMPABLE, 0)` antes de cargar ajustes; `instalacion.md` añade una comprobación de solo lectura del `core_pattern` de la anfitriona | logical-components §4: la tabla en memoria nunca debe acabar en disco (NFR10.2); no se toca el *kernel* compartido |
| Almacenamiento | Sin PVC. `emptyDir` con `medium: Memory` y `sizeLimit: 16Mi` en `/tmp`; `ConfigMap` `veridicus-anonymizer-rules` montado `readOnly` en `/etc/veridicus/anonymizer/` | NFR10.10, NFR10.11; el proxy no guarda nada |
| Red de salida | Una `NetworkPolicy` propia con `ipBlock` = cada CIDR IPv4 de `anonymizer.upstreamCidrs` (prefijo ≥ /24) solo a 443/TCP, más la regla común `allow-dns` hacia CoreDNS | NFR1.5; Calico de código abierto no filtra por nombre, así que el destino solo se fija por CIDR estables |
| Resolución de nombres | CoreDNS del clúster con **lista blanca** (§3): el proxy solo resuelve `anonymizer.upstreamHost`; ningún otro pod de `veridicus` resuelve nombres externos | P1 = A (amenaza T15) |
| Red de entrada | Solo `semantic-agent` y `session-api` (`session-api-worker` incluido) a 8080, y el namespace `monitoring` a 8081 | `veridicus-anonymizer-ingress` (NFR1.9) |
| Entornos | Máquina de desarrollo (`values-cpu.yaml`) y de demostración (`values-gpu.yaml`); el PR de habilitación dice en cuál se enciende y `check-provider-adr.sh` revisa los dos archivos; sin *staging* ni producción | team.md; mismo digest en ambas |
| Recursos | CPU `requests` 100m, `limits` 1; memoria `requests` 256 MiB, `limits` 320 MiB (pico ≤ 256 MiB + 25 %); sin GPU en ningún *values* | performance-design §5 (NFR8.1), NFR2.2; el PR de habilitación vuelve a medir el pico y ajusta el límite si hace falta |
| IaC | Subchart Helm con *values* validados por `values.schema.json` (`enabled: true` exige `providerAdr`, `upstreamHost`, `upstreamCidrs`, `model`); `Corefile` versionado en `deploy/cluster/coredns.yaml`; ninguno lo aplica un *script* | AUTONOMIA-01: el humano aplica lo ya fusionado |
| Clasificación | Etiqueta `veridicus.io/data-class: sensitive` (recibe texto en claro) y anotación `veridicus.io/provider-adr: <ruta del ADR>` | Tabla de fronteras de U2; regla 2 de `veridicus-egress-only-anonymizer` |

**Presupuesto.** Con el proxy habilitado se suman 0,1 CPU y 256 MiB pedidos (320 MiB de límite):
cabe en la máquina de desarrollo (20 GiB, 10 CPU) y en la de demostración (28 GiB, con los extras de
U8) sin cambiar los totales de U4. Con el proxy apagado el costo es cero.

## 2. Servicios de infraestructura

| Servicio | Rol | Configuración | Notas |
|---|---|---|---|
| `veridicus-anonymizer-proxy` (Service) | load-balancer interno | `ClusterIP`; 8080 (`http`) y 8081 (`metrics`); `http://veridicus-anonymizer-proxy.veridicus.svc.cluster.local:8080` | Cumple `internal-model-urls` de U2 (termina en `.svc.cluster.local`); `VERIDICUS_JUDGE_URL` y `VERIDICUS_EMBEDDINGS_URL` solo apuntan aquí en el PR de habilitación (NFR1.6) |
| CoreDNS (`kube-system`) | dns | `Corefile` con lista blanca (§3); `cache 30`; métricas en 9153 | Compartido con todo el clúster; la lista solo crece por PR |
| `veridicus-anonymizer-rules` (ConfigMap) | configuración | `rules.yaml` con `schema_version` semver; su SHA-256 en `VERIDICUS_ANONYMIZER_RULES_SHA256`; anotación de *checksum* en el `Deployment` para reiniciar al cambiar | NFR10.11; un cambio de reglas es un PR |
| `veridicus-anonymizer-credential` (Secret) | secreto | Clave `api-key`; leída por `secretKeyRef` en `VERIDICUS_ANONYMIZER_API_KEY`; creada por `create-secrets.sh` solo si el `.env` trae la variable | NFR10.6; nunca en el repositorio ni en la CI |
| Destino externo del proveedor | other (modelo externo) | Host y CIDR del ADR, HTTPS 443, TLS ≥ 1.2, sin redirecciones, un intento | Fuera del clúster; solo recibe marcadores |
| `veridicus-anonymizer-proxy` (PrometheusRule y ServiceMonitor) | monitoreo | Solo con `anonymizer.enabled` y `monitoring.enabled` (módulo 8) | `monitoring-design.md` |
| Base de datos, Redis, colas, caché | — | No aplica | El proxy no tiene credencial de ninguno (D4, NFR10.10) |

### 2.1 Ajustes del contenedor

| Variable | Valor |
|---|---|
| `VERIDICUS_ANONYMIZER_UPSTREAM_URL` | `https://<anonymizer.upstreamHost>` (sin usuario ni puerto distinto de 443) |
| `VERIDICUS_ANONYMIZER_MODEL` | `anonymizer.model` (`<proveedor>/<modelo>@<versión>`) |
| `VERIDICUS_ANONYMIZER_RULES_SHA256` | Calculado por el chart desde `rules.yaml` |
| `VERIDICUS_ANONYMIZER_MASKING_TIMEOUT_SECONDS` | 2 |
| `VERIDICUS_ANONYMIZER_MAX_CONCURRENCY` | 4 |
| `VERIDICUS_ANONYMIZER_MAX_*` | Sin definir: rigen los topes de `contracts/limits.v1.yaml` (solo pueden bajarse) |

## 3. Resolución DNS con lista blanca (P1 = A, T15)

El `Corefile` resuelve los servicios del clúster, reenvía solo las zonas permitidas y responde
NXDOMAIN al resto. La zona del proveedor solo existe cuando el proxy está habilitado y es
exactamente `anonymizer.upstreamHost`.

```
cluster.local:53 in-addr.arpa:53 ip6.arpa:53 {
    kubernetes cluster.local in-addr.arpa ip6.arpa
    cache 30
}
github.com:53 {
    forward . /etc/resolv.conf
}
.:53 {
    health
    ready
    prometheus :9153
    template ANY ANY {
        rcode NXDOMAIN
    }
}
```

Con el proxy habilitado se añade un bloque `<upstreamHost>:53` igual al de `github.com`. El bloque
`hosts` que Minikube inyecta para `host.minikube.internal` se conserva dentro de `.:53`, antes de
`template`, con `fallthrough`.

| Aspecto | Decisión | Razón |
|---|---|---|
| Dónde vive | `deploy/cluster/coredns.yaml` (`ConfigMap` `coredns` de `kube-system`), fuera del chart paraguas | Es un recurso del sistema de Minikube, no de `veridicus` |
| Quién lo aplica | El humano, tras fusionar el PR, con `kubectl apply` y `kubectl -n kube-system rollout restart deployment coredns`, según `docs/operacion/instalacion.md` | AUTONOMIA-01 |
| Deriva | `scripts/check-coredns.sh` (solo lectura) compara el SHA-256 del `Corefile` del clúster con el versionado; se ejecuta tras cada `minikube start`, porque Minikube reescribe el bloque `hosts` al arrancar | Detecta que el clúster volvió al reenvío abierto |
| Descargas de imágenes | No las afecta: el *runtime* del nodo usa el resolvedor del nodo, no CoreDNS | Infrastructure Design de U2 §3 |
| Riesgo residual | Las subzonas de `github.com` y del host del proveedor siguen resolviéndose hacia sus servidores autoritativos, que no controla un atacante | Aceptado; se declara en el ADR |
| Verificación manual (solo lectura) | `kubectl exec <pod> -- python -c "import socket; socket.getaddrinfo('example.com', 443)"` termina con código distinto de 0 en cada pod Python de `veridicus`; en el proxy habilitado, `getaddrinfo('<upstreamHost>', 443)` responde y `getaddrinfo('example.com', 443)` falla | P1 = A; mismo formato que security-design §10 |

## 4. Frontera de AUTONOMIA-04

| Componente | Dentro o fuera del clúster | Datos que cruzan su frontera | Control |
|---|---|---|---|
| `anonymizer-proxy` | Dentro, `veridicus`; 0 réplicas por defecto | Entra (interno): *prompt* o textos en claro, lista de nombres propios y `X-Request-Id`. Sale: solo el cuerpo enmascarado que pasó la comprobación final, hacia el CIDR del ADR por 443 | `NetworkPolicy` propia, comprobación final (security-design §2), sin cabeceras heredadas |
| `MaskTable` y `NumberingPlan` | Memoria del proceso del proxy | Nada | Sin volúmenes; `RLIMIT_CORE = 0`; borrado en `finally` |
| `AnonymizerGateway` en `semantic-agent` y `session-api` | Dentro | Texto en claro y lista de nombres hacia el proxy (HTTP interno) | `anonymizer_route` y la validación de destinos de U4 (NFR1.6) |
| CoreDNS | Dentro, `kube-system` | Hacia fuera solo consultas de `github.com` y del host del ADR | Lista blanca de §3 |
| Destino externo | **Fuera** | Recibe marcadores y la estructura del testimonio; devuelve texto con marcadores o vectores | ADR del proveedor (NFR1.2) |
| Demás pods de `veridicus` | Dentro | Nada hacia fuera: ni IP ni nombres externos | `veridicus-default-deny`, `deny-external-egress`, §3 |

Con el proxy apagado, la frontera es la de U2 y U4 más la lista blanca de CoreDNS: ningún pod de
`veridicus` sale ni resuelve nombres externos.

## 5. Infraestructura compartida

| Recurso compartido | Unidad dueña | Unidades que lo usan | Frontera de acceso |
|---|---|---|---|
| CoreDNS y su `Corefile` | U2 (clúster); U10 propone la lista blanca | Todas; Argo CD (`github.com`); el proxy (host del ADR) | Solo cambia por PR que aplica el humano; deriva comprobada por `check-coredns.sh` |
| `libs/model_gateway` | U4 | U4, U8, U9; U10 aporta `AnonymizerGateway` y `anonymizer_route.py` | Módulos propios de U10 con 100 % de ramas |
| `veridicus-default-deny` y `allow-dns` | U2 | Todas | El proxy es el único `podSelector` con `ipBlock` externo |
| Políticas Kyverno de `deploy/policies/` | U2 (motor offline) | U10 añade 4 políticas y sus controles negativos | Corren en `deploy-level0.yml`, sin clúster |
| `contracts/limits.v1.yaml` | U1 | Todas | Entradas `anonymizer.*` con U10 como dueña |
| Prometheus y Grafana (módulo 8) | U2 | U10 con su `ServiceMonitor`, reglas y fila de panel | Solo el puerto 8081 |
| `create-secrets.sh` | U2 | U10 añade `veridicus-anonymizer-credential` | Valores solo desde el `.env` no versionado |

## 6. Precisiones a artefactos ya aprobados

No edité ningún artefacto aprobado ni de otra unidad; decides en la aprobación si se actualizan.

| Artefacto | Qué precisa | Origen |
|---|---|---|
| `platform/infrastructure-design/infrastructure-specification.md` §2.1 (CoreDNS) y §1 | CoreDNS deja de ser «el del clúster»: lleva el `Corefile` con lista blanca de §3, versionado en `deploy/cluster/coredns.yaml`, aplicado por el humano y comprobado con `scripts/check-coredns.sh` tras cada `minikube start` | P1 = A; T15 |
| `platform/infrastructure-design/cicd-pipeline.md` §4.1 y `docs/operacion/instalacion.md` | Paso nuevo: aplicar el `Corefile` y reiniciar CoreDNS antes de instalar el chart; paso de comprobación del `core_pattern` de la anfitriona | P1 = A; logical-components §4 |
| `platform/infrastructure-design/monitoring-design.md` §1 | Mantener activo el `ServiceMonitor` de CoreDNS de `kube-prometheus-stack` y desactivar en Grafana la búsqueda de actualizaciones (`analytics.check_for_updates: false`) para que la alerta de NXDOMAIN no tenga ruido | `monitoring-design.md` de esta unidad |
| `anonymizer/nfr-design/security-design.md` §5 (`veridicus-egress-only-anonymizer`) | Un proveedor que publica un rango más ancho que /24 (por ejemplo un /23) se escribe en `upstreamCidrs` partido en sus /24; la política no cambia. Solo se renderizan CIDR IPv4, porque el clúster Calico es IPv4 | Prefijo mínimo de la regla 2 |
| `anonymizer/nfr-design/security-design.md` §5 y `nfr-requirements/tech-stack-decisions.md` D8 | El proxy no tiene regla DNS propia: usa la regla común `allow-dns` hacia CoreDNS y solo resuelve su host porque la lista blanca lo incluye; `check-provider-adr.sh` comprueba además que `upstreamHost` aparece como zona en `deploy/cluster/coredns.yaml` cuando el proxy está habilitado, y que no aparece cuando está apagado | P1 = A |
| `anonymizer/nfr-requirements/tech-stack-decisions.md` (riesgo de IP cambiantes) | Con Calico de código abierto no hay políticas por FQDN: el ADR exige CIDR estables publicados; un proveedor sin ellos no se habilita | Calico fijado por U2 |
