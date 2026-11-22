# Preguntas de NFR Design — U11 incoherence-analyzer

- **Unidad:** U11 `incoherence-analyzer` (tipo `library`, MUST, XL), Bolt B11: la primera rebanada de valor
  (B1 contratos → B10 anonimizador → B11 analizador).
- **Componentes:** IncoherenceAnalyzer, AnalyzerCli, ModelGateway (puerto, adaptador local de C14, adaptador
  `anonymizer` y cliente HTTP de C21), ExecutionProfiles, IntegrityPolicy, `evaluation/` y `evaluation/zine/`.
- **Situación:** primera pasada (revisión 1, 2026-11-22), sobre el Functional Design revisión 1
  (BR1.1–BR14.5, F1–F12, E1–E66, FD-U11-01 a FD-U11-28) y el NFR Requirements revisión 1 (NFR-U11-01 a
  NFR-U11-15), los dos aprobados.
- **Artefactos para un `library`:** `security-design.md`, `logical-components.md` y `traceability.json`.
  Como el NFR Requirements añadió `performance-requirements.md` y `reliability-requirements.md`, el diseño
  añade `performance-design.md` y `reliability-design.md`. No hay diseño de escalabilidad ni de
  observabilidad: la biblioteca no escala por sí misma y no exporta métricas (NFR15.2).

## Lo que ya está decidido

| Tema | Decisión | Fuente |
|---|---|---|
| Modelos de la primera rebanada | Juez de Anthropic (externo), verificador local gpt-oss-20b Q8_0 (`family: openai`), sin alterno; generador del conjunto de Google | P1 = A de NFR Requirements (NFR-U11-01) |
| Permutación | Activa en todos los perfiles, también en `todo-local` | FD-U8-08; NFR-U11-08 |
| Umbrales del nivel 2 | Precisión ≥ 0,70, sensibilidad ≥ 0,60, acuerdo entre 3 corridas ≥ 0,60; bloquean solo con `evaluacion-comercial` | P2 = A (NFR-U11-02) |
| Conjunto sintético | 40 muestras con la composición de NFR4.11 | P3 = A (NFR-U11-03) |
| Latencias | p95 de `analyze` incremental ≤ 180 s con `comercial-piloto`; *N* de la prueba de humo = 300 s | NFR3.1; NFR-U11-10 |
| Exportación Likert | `veridicus evaluate --export-likert <dir>`, solo sobre el conjunto sintético | NFR-U11-15 |
| Tamaños | Transcripción de hasta 250 000 caracteres, turnos de hasta 20 000 y 2 000 turnos; `model_call_timeout_s` ≥ 270 s con perfil comercial | NFR-U4-01, NFR-U4-02 (P6 = A de U4); C25 v1 de U1 |
| Límites por entorno | El catálogo empaquetado es el techo; `VERIDICUS_LIMITS_PATH` y `VERIDICUS_LIMIT_<NOMBRE>` solo bajan cifras | NFRD-U1-09 |
| Cliente de C21 | Traduce `413` a `AnonymizerUnavailable` y espera el plazo efectivo más 10 s | NFRD-U10-17; NFRD-U10-10 |
| Métodos de voz | `transcribe` y `synthesize` van en el puerto de U11 y los escribe U9 en B9; B11 entrega el puerto solo con `generate` | NFR-U9-01 |
| Adaptadores comerciales | En U10, con httpx directo y sin los SDK de los proveedores | CD-04; NFR Requirements de U10 |

## Lo que el diseño resolverá sin preguntar

Cada punto sale de las fuentes aprobadas o es un hallazgo que un experto cierra. Lo que precisa un artefacto
aprobado va a la tabla NFRD-U11-xx de `security-design.md`; ningún original se edita.

1. **NFR-U11-11 queda superada** por NFR-U9-01: el puerto admite que U9 sume los métodos de voz sin tocar
   `generate`.
2. **Nombres de los límites por entorno** (`VERIDICUS_LIMIT_<NOMBRE>` en vez de `VERIDICUS_<AJUSTE>`) y papel
   de `VERIDICUS_LIMITS_PATH` como archivo que solo baja cifras (NFRD-U1-09).
3. **Mediciones con 250 000 caracteres** (NFR3.2, NFR3.4 y el presupuesto de memoria) y piso de 270 s para
   `model_call_timeout_s` con un perfil comercial, comprobado al arrancar.
4. **Margen de 10 s del cliente de C21 dentro del plazo de la corrida**, para que la espera extra de
   NFRD-U10-10 nunca pase de `run_deadline_*`.
5. **Rechazo previo por tamaño en el cliente de C21**: si el cuerpo pasa de `anonymizer_request_max_bytes`,
   `AnonymizerUnavailable` sin enviar, igual que el `413` del proxy.
6. **Presupuesto de latencia del modo incremental** repartido entre juez, verificador y biblioteca, con el
   prefijo fijo del *prompt* primero para aprovechar la caché del servidor local.
7. **Exportación Likert a ciegas**: orden barajado con semilla y clave de correspondencia aparte.
8. **Latencia y costo por llamada fuera de C6.** NFR15.1 pide la latencia en cada entrada de
   `registro.llamadas`, pero C6 es el contrato común del TG y no cambia (ADR-017). Se miden en memoria y solo
   sus agregados van a C19 v2, que es lo que pide NFR-U11-14. No hay alternativa que respete C6.
9. **Reanudación de `evaluate` por muestras**, que realiza el «se parte por muestras» de NFR2.2.
10. **Nombres que no coinciden** entre artefactos aprobados (forma del comando de nivel 2 y nombre del
    manifiesto): se sigue el Functional Design.

Ningún punto cambia el alcance, el riesgo de la compuerta ni lo que sale del clúster; los puntos 4 y 5
reducen llamadas que podrían salir.

## Preguntas

Sin preguntas: todo lo fijan las fuentes.
