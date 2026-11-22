<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->

- 2026-10-03T03:03:51Z — La cookie Secure de U3 obliga a HTTPS en el ingress; P1 = A lo resuelve con una CA local de mkcert en la anfitriona y el certificado como Secret, sin certificados en el repositorio.
- 2026-11-22T15:40:36Z — Segunda pasada sin preguntas: los fixtures AIR de U2 (5 y 6 de 20) y de U5 (0,25 y 0,375) no se contradicen porque la regla compara un cociente; se usan los dos (NFRD-U2-12).
- 2026-11-22T15:40:36Z — NFR1.5 (proxy solo desde semantic-agent) y NFR15.1 de U10 (métricas del proxy) se concilian por puerto: Prometheus solo en el puerto de métricas (NFRD-U2-03).

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->

- 2026-10-03T03:03:51Z — Kyverno solo como CLI (P2 = A): se evita un controlador más en la máquina, a costa de que un manifiesto aplicado a mano fuera del chart solo lo frene Pod Security restricted.
- 2026-11-22T15:40:36Z — Patrón único sin disco en todo /api/ con tope por grupo (C25 + margen) en vez de un Ingress por ruta: menos regex y un solo control, a costa de que use-regex del Ingress de voz valga para todo el host, por lo que el enrutamiento se prueba en nivel 3.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
