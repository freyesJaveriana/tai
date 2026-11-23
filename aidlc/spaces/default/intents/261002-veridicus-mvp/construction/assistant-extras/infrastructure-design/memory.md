<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-10-03T11:00:43Z — P1 = A se materializó como dos Application (veridicus-dev sin values-extras.yaml, veridicus-demo con values-gpu.yaml + values-extras.yaml) y una comprobación offline que impide incluirlo en desarrollo.
- 2026-11-23T01:30:59Z — Segunda pasada sin preguntas: P1 = A pierde su objeto con el cambio 01 (no hay extras que encender) y U8 no añade nada al despliegue salvo la migración, dos contadores y dos paneles (IDS-U8-01).

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-10-03T11:00:43Z — La lista afectiva y el prompt de la pregunta pasan al directorio files/ del chart de semantic-agent (frente a D7 y D4) porque Helm no lee contracts/; quedó en la tabla de precisiones.
- 2026-11-23T01:30:59Z — La medición de todo-local de B8 detiene Minikube (sin delete) mientras el juez y el verificador corren en la anfitriona: el procedimiento de U11 solo levanta el verificador, y con Minikube encendido los 38 GiB de modelos no caben en WSL2 (IDS-U8-08).

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-10-03T11:00:43Z — La lista afectiva entra en el filtro de ai-eval-gate.yml aunque es determinista: más reportes de nivel 2, a cambio de medir la repetibilidad de lo que ve el analista.
- 2026-11-23T01:30:59Z — session-api pasa a depender de libs-incoherence-analyzer para la segunda línea; se pide un job lock-boundary sin libs-anonymizer en vez de copiar el validador, a costa de una dependencia más en la imagen con la base (IDS-U8-03).
- 2026-11-23T01:30:59Z — El margen de semantic-agent queda en 13 MiB (947 de 960 MiB) con el módulo; se acepta sin pedir más memoria a U2 y cualquier pico mayor medido en B8 sube el límite por PR (IDS-U8-02).

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
