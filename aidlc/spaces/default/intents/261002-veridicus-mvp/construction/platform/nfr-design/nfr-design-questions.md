# Preguntas de NFR Design — U2 platform

**Unidad.** U2 `platform` (tipo `packaging`): chart Helm `deploy/veridicus`, políticas de manifiestos,
`NetworkPolicy`, servidores de modelos, PostgreSQL, Redis y *scripts* revisables. Por ser
`packaging`, en esta etapa solo produce el diseño de seguridad y la trazabilidad.

**Lo que ya está decidido y no se vuelve a preguntar.** Requisitos NFR1.1–NFR15.1 y decisiones
D1–D11 de `nfr-requirements/` (negar todo por defecto, perfil `restricted`, imágenes por digest,
modelos descargados en la anfitriona y verificados por `sha256`, Secrets solo referenciados, Redis con
contraseña, CloudNativePG sin superusuario, Argo CD sin *prune* sobre la base). La distribución de
Kubernetes, el CNI y los recursos los fija Infrastructure Design. Quedan dos decisiones de seguridad.

---

## P1 — Cómo llega la consola por HTTPS

La cookie de sesión de U3 lleva `Secure`, así que el navegador solo la envía por HTTPS (o a
`localhost`). Hay que decidir cómo se cifra la conexión entre el navegador y el clúster local, en la
máquina de desarrollo y en la demostración.

A. El *ingress* termina TLS con un certificado de una CA local creada con `mkcert` en la máquina
   anfitriona; `scripts/create-secrets.sh` carga el certificado y la clave como Secret TLS (nunca en el
   repositorio) y el navegador de la demostración confía en esa CA. El chart exige TLS en el *ingress*
   y redirige HTTP a HTTPS. (Recomendada)
B. cert-manager dentro del clúster con un emisor autofirmado; el navegador muestra la advertencia o se
   importa la CA a mano.
C. Sin TLS en el *ingress*: la consola se usa solo por `kubectl port-forward` a `localhost`, que el
   navegador trata como contexto seguro.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P2 — Si las políticas de Kyverno también se hacen cumplir dentro del clúster

Hoy las políticas corren en la CI y en la máquina de desarrollo con Kyverno CLI, sin red, sobre el
render del chart. Dentro del clúster solo actúa Pod Security `restricted` del namespace. Un manifiesto
aplicado a mano que no pasó por el chart no se revisaría contra las políticas propias (imágenes por
digest, `NetworkPolicy`, sin `ipBlock` externo).

A. Solo Kyverno CLI en CI y en desarrollo, más Pod Security `restricted` en el clúster. Todo cambio al
   clúster ya entra por PR con el render validado (AUTONOMIA-01), y no se agrega otro componente que
   consuma memoria en la máquina. (Recomendada)
B. Además, Kyverno como controlador de admisión en el clúster, en modo `Enforce`, con las mismas
   políticas.
C. Kyverno en el clúster en modo `Audit` (solo informa), sin bloquear.
X. Other (please specify)

[Answer]: A **Mode:** guided
