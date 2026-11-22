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

---

# Segunda pasada — cambio 01, adenda 02 y NFR Requirements revisión vigente (2026-11-22)

## Lo que ya está decidido

- Los requisitos de la revisión 2 de `nfr-requirements/security-requirements.md` (NFR1.1–NFR1.7, NFR2.1,
  NFR8.1–NFR8.3, NFR10.1–NFR10.19, NFR11.1–NFR11.2, NFR12.1–NFR12.2 y NFR15.1–NFR15.2) y las decisiones
  D1–D17 de `nfr-requirements/tech-stack-decisions.md`, con P5 = A (Argo CD sale solo hacia `github.com`).
- P1 = A (TLS en el Ingress con una CA local de `mkcert`) y P2 = A (Kyverno solo como CLI) de la revisión 1
  siguen vigentes.
- Lo que hoy piden a U2 las tablas NFR-Ux aprobadas: NFR-U6-06, NFR-U7-05 a NFR-U7-07, NFR-U9-05,
  NFR-U10-10, NFR-U11-07, NFR-U11-10, NFR-U12-05 y NFR-U13-07 a NFR-U13-12, y las cifras de C25 del NFR
  Design de U1 (`audio_max_bytes`, `import_file_max_bytes`, `research_report_max_bytes`,
  `audio_store_max_bytes`, `retention_max_days` y `dismissal_window_w`).

## Cómo se registra la revisión

`security-design.md` pasa a la revisión 2 y sustituye a la revisión 1, que queda en el historial de Git.
Las secciones conservan su número cuando siguen; lo nuevo empieza en §11. Las precisiones nuevas toman los
IDs NFRD-U2-01 en adelante, y la tabla §15 cierra los hallazgos R-01 a R-08 de `reviews/review-01.md`.
U2 es `packaging`: la etapa solo produce `security-design.md` y `traceability.json`, así que lo que otras
unidades piden de persistencia, respaldos y métricas se diseña en ese mismo documento.

## Lo que el diseño resolverá sin preguntar

- **Prometheus** raspa el puerto interno de métricas de los cuatro servicios (`session-api`,
  `semantic-agent`, `audio-worker` y `anonymizer-proxy`), y nunca el puerto de la API ni los servidores
  de modelos (NFR15.2, NFR-U9-05 (a), NFR15.1 de U10 y NFR10.8 de U2).
- **Ingress sin disco**: un patrón único para todo lo que va a `session-api` (sin *buffering* de petición
  ni de respuesta y `proxy-max-temp-file-size: "0"`), con un tope por grupo de rutas derivado de C25 más su
  margen: 2 113 536 (`/api/`), 6 065 536 (voz) y 8 454 144 (reportes del investigador) (NFR-U6-06,
  NFR-U7-07, NFR-U12-05).
- **Redis**: AOF `everysec`, `save ""` y reescritura con `100` y `16mb` (NFR11.2, NFR-U9-05 (b)).
- **Volúmenes**: PVC de audio aparte del de reportes, ≥ 1,2 × `audio_store_max_bytes`, y una tabla
  cerrada de quién monta cada volumen, con el `Job` de retención con el mismo UID y GID que `session-api`
  (NFR-U9-05 (d), NFR-U7-06, NFR-U13-07).
- **Respaldos** de como mucho 90 días (`retention_max_days`), solo en la máquina local (NFR-U13-11).
- **PostgreSQL** sin parámetros en los logs (NFR-U13-12) y `kubectl exec` con una lista cerrada de
  comandos de solo lectura (NFR-U13-08, NFR-U7-05).
- Los *fixtures* de la regla AIR unen los de U2 (5 de 20 y 6 de 20) y los de U5 (0,25 y 0,375): no se
  contradicen, porque la regla compara un cociente.

Sin preguntas: todo lo fijan las fuentes.
