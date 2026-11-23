# Preguntas de Infrastructure Design — U10 anonymizer

**Unidad.** U10 `anonymizer` (tipo `service`, COULD): adaptador anonimizador de ModelGateway que corre
como el proceso `anonymizer-proxy`, se entrega apagado (`anonymizer.enabled: false`) y, si un PR con
ADR del proveedor lo habilita, es el único pod del namespace `veridicus` con salida a internet, solo
hacia el destino declarado y solo con el *payload* enmascarado (AUTONOMIA-04).

**Lo que ya está decidido y no se vuelve a preguntar.** Minikube con Calico en las dos máquinas
(20 GiB y 10 CPU en desarrollo, 28 GiB en demostración), un namespace `veridicus` con negar todo por
defecto y la única regla `ipBlock` reservada al proxy (Infrastructure Design de U2 y U4); el chart
renderiza el proxy solo con `anonymizer.enabled: true`, que exige `providerAdr`, `upstreamHost`,
`upstreamCidrs` y `model` (D1); la credencial vive en el Secret `veridicus-anonymizer-credential`,
creado por el humano con `create-secrets.sh` y leído por `secretKeyRef` (NFR10.6); 1 réplica, CPU
100m/1, `limits.memory` = pico medido (≤ 256 MiB) + ≥ 20 %, `emptyDir` en memoria de ≤ 16 MiB, reglas
en `ConfigMap` `readOnly`, sin PVC ni credenciales de base o Redis (diseños de `nfr-design/`); las
políticas Kyverno de salida, entrada y endurecimiento con sus controles negativos; métricas, alertas
informativas y panel (observability-design); GHCR privado y despliegue por PR. Como Calico de código
abierto no tiene políticas por nombre de dominio, la regla de salida del proxy solo puede expresarse
con los CIDR estables que publique el proveedor (prefijo ≥ /24); un proveedor sin CIDR estables no se
habilita, como ya prevé `tech-stack-decisions.md`. Los volcados de memoria se desactivan en el propio
proceso (`RLIMIT_CORE = 0` y no volcable), sin tocar el *kernel* de la anfitriona.

Queda una decisión.

---

## P1 — Resolución DNS hacia fuera del clúster (amenaza T15)

NFR Design de U10 transfirió aquí la amenaza T15: con Calico de código abierto las `NetworkPolicy` no
filtran por nombre, y todo pod de `veridicus` tiene la regla `allow-dns` hacia CoreDNS, que en Minikube
reenvía **cualquier** nombre al resolvedor de la anfitriona. Un proceso comprometido sin salida IP
podría sacar datos codificados en consultas DNS (`<datos>.dominio-del-atacante`). El riesgo existe
para todo el namespace aunque el proxy siga apagado, y CoreDNS es un componente compartido del clúster
(U2).

A. CoreDNS con lista blanca: resuelve `cluster.local`, reenvía solo las zonas imprescindibles
   (`github.com` para Argo CD en el módulo 8 y, el día que se habilite el proxy, el host del ADR) y
   responde NXDOMAIN al resto. Entra como `ConfigMap` de `kube-system` revisable por PR que aplica el
   humano; verificación manual: `getaddrinfo('example.com')` desde un pod de `veridicus` falla y desde
   el proxy habilitado resuelve solo su host. Costo: se vuelve a aplicar tras `minikube delete` y cada
   nueva dependencia externa exige editar la lista. (Recomendada)
B. Más estricto: CoreDNS sin reenvío externo salvo `github.com` (Argo CD), y el proxy resuelve el host
   del proveedor con `hostAliases` fijados a las IP del ADR. Ningún pod de `veridicus` resuelve nombres
   externos. Costo: si el proveedor cambia de IP dentro de su CIDR, el proxy falla hasta que un PR
   actualice las IP.
C. Aceptar el riesgo residual: CoreDNS queda como está y la tabla de fronteras y el ADR documentan el
   canal DNS; se apoya en que ningún pod con datos tiene salida IP y en que el proxy está apagado por
   defecto. Costo: el canal de exfiltración por DNS queda abierto para todo el namespace.
X. Other (please specify)

[Answer]: A **Mode:** guided

---

# Segunda pasada — cambio 01, adenda 02 y NFR Design revisión vigente (2026-11-23)

## Lo que ya está decidido

- **U10 es MUST y forma parte del despliegue base** (D1 de `tech-stack-decisions.md` revisión 2): el
  proxy ya no se entrega apagado, y el chart que lo genera es de U2. La CLI usa el mismo módulo en su
  proceso.
- **Pasan a U2** (security-design §5 «Retirado», logical-components §4 y §5): la `NetworkPolicy` de
  salida (`0.0.0.0/0` con `except` de los rangos privados, solo 443) y la de entrada (`semantic-agent`
  a 8080 y Prometheus a 9090), la lista blanca de CoreDNS (`deploy/coredns/Corefile`, unión de
  `allowed-domains.v1.yaml` y `infra-domains.yaml`), el Secret `veridicus-provider-keys`, el
  endurecimiento del pod, el volumen de solo lectura del NER y los `requests`/`limits`. La respuesta
  P1 = A de la revisión 1 queda cumplida por U2 (NFR1.4 de U2).
- Puertos 8080 (C21, `/healthz` y `/readyz`) y 9090 (`/metrics`); el panel se empaqueta con su SHA-256
  (NFRD-U10-09); nombres de NFRD-U10-11; `VERIDICUS_ANONYMIZER_NER_THREADS` (NFRD-U10-07); Anthropic
  como primer proveedor (D10); pico de RSS ≤ 1,5 GiB (scalability-design §4); arranque ≤ 60 s y sonda
  de arranque ≥ 90 s (NFRD-U2-08).
- **Supuesto de máquina** (brief del 2026-11-22): una sola máquina de 64 GB, solo CPU, sin máquina
  GPU; el tamaño de Minikube lo decide U2, que es la única unidad que lo pregunta.

## Cómo se registra la revisión

Revisión 2 de los cuatro artefactos de esta carpeta, que sustituye a la revisión 1 del 2026-10-03 (queda
en el historial de Git). Lo que sale queda «Retirado» con su número; las precisiones nuevas son
IDS-U10-01 en adelante, en §6 de `infrastructure-specification.md`.

## Lo que el diseño resolverá sin preguntar

- El modelo NER concreto y sus criterios (lo pide D2 a esta etapa); su revisión y su `sha256` se fijan
  en `deploy/models.lock` dentro de B10.
- Las cifras que U10 propone a U2 para el pod (memoria, CPU, plazo de terminación, sondas) a partir del
  pico medido y de `model_call_timeout_s` = 270 s.
- Que el mamparo de 4 no cubra las sondas, los hilos de `torch` fijados por entorno y la puerta de CI del
  NER real.
- La retirada de lo que la revisión 1 ponía en U10 y ahora es de U2 (§1 a §5 de la revisión 1).

Sin preguntas: todo lo fijan las fuentes.
