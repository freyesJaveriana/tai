<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-11-21T23:42:00Z — Alcance de U11 leído como la biblioteca completa del analizador (núcleo C17, ModelGateway con adaptador local y cliente HTTP de C21, ExecutionProfiles, escáner y aviso de IntegrityPolicy), la CLI con `analyze` y `evaluate`, el conjunto sintético con su manifiesto y los `.sbatch` de ZINE. Quedan fuera las colas y sesiones (U4), la seudonimización y los adaptadores nativos (U10) y las aclaraciones neutras (U8). Solo se preguntan 8 decisiones de criterio que las fuentes no fijan o en las que se contradicen: orden de filtros, contexto del verificador, vocabulario prohibido (AC3.2.4 frente al motivo de C6), permutación en B11 frente a US10.5 en U8, alterno y familias, métricas de las 3 corridas, etiquetas de sesgo frente a `bias_table` de C19, y aviso de VE-01 en la CLI.
- 2026-11-22T00:25:00Z — El archivo de entrada de la CLI se leyó como el objeto `transcripcion` de C6 (la CLI arma la entrada con modo y perfil) y el reporte identifica cada entrevista por `interview_sha256` y no por su id, porque C19 no admite texto libre (FD-U11-23).
- 2026-11-22T00:25:00Z — La regla del corpus se leyó por la ubicación del directorio de salida: dentro de un árbol de Git debe estar ignorado (`git check-ignore`); fuera de todo repositorio, como en ZINE, se permite (FD-U11-16).
- 2026-11-22T00:25:00Z — El sensor de trazabilidad sumó AC5.5.3, AC5.5.4 y AC8.3.1–AC8.3.3 por los cruces US5.5 y US8.3 del mapa; se cubrieron AC5.5.3 (BR3.4), AC8.3.2 (BR2.11) y AC8.3.3 (BR2.10), y se difirieron AC5.5.4 y AC8.3.1 a U4/U7.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-11-22T00:25:00Z — Las métricas de P6 (valores por corrida, umbrales, `passes`, `permutation_coverage`, `type_agreement`, `completed_runs`, sensibilidad por distancia, sección adversarial) no caben en C19 v1: se propone C19 v2 como cambio mayor por un PR de U1 antes del código de B11 (FD-U11-09) y un código de salida 6 (FD-U11-10).

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-11-22T00:25:00Z — Con permutación se hacen siempre las dos llamadas del verificador, aunque la directa rechace: el doble de llamadas a cambio de medir sin sesgo la consistencia al invertir el orden (BR6.1, BR12.4).
- 2026-11-22T00:25:00Z — Los veredictos se capturan con un envoltorio del gateway que solo guarda booleanos, en vez de añadirlos a la salida de C6: el contrato no cambia, a costa de que la métrica solo exista dentro de `evaluate` (BR12.4).
- 2026-11-22T00:25:00Z — En `estado: error`, `registro.descartes` va vacío igual que `hallazgos`: nada de una corrida fallida se interpreta como resultado, a costa de perder el diagnóstico de los descartes previos al fallo (BR7.1, FD-U11-13).

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
- 2026-11-22T00:25:00Z — Listas iniciales de `tipo_hecho` y `perfil_persona` (BR13.3) propuestas por el diseño; las aprueba el autor.
- 2026-11-22T00:25:00Z — Umbrales de las métricas estadísticas y composición mínima del conjunto: los fija NFR Requirements en `evaluation/thresholds.v1.yaml`.
- 2026-11-22T00:25:00Z — Tramos de distancia para la sensibilidad (hasta el solapamiento, hasta la ventana, más de la ventana) por confirmar en NFR Requirements (BR12.5).
- 2026-11-22T00:25:00Z — El riesgo de una sola palabra citada en el escáner depende de FD-U1-14, aún pendiente en U1 (BR9.2).
