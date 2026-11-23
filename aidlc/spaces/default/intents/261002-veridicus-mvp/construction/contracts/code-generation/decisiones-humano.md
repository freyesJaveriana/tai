# Decisiones del humano antes de la Parte 2 — U1 contracts

**Fecha:** 2026-11-23. **Origen:** el triage de las precisiones pendientes, que se hizo después de `Approve Plan`.

## Decisiones

| ID | Tema | Decisión | Efecto en el plan aprobado |
|---|---|---|---|
| C-3 | `PATCH /sessions/{session_id}/analysis` (NFR-U6-03, NFRD-U6-02) | Se confirma, con respuesta `202` | Deja de estar abierta (PD-3). Entra en C1 en el paso 16 |
| D-1 | `GET /notice` (FD-U4-08) | Pública, sin sesión; solo devuelve el texto versionado del aviso | Deja de estar abierta (PD-3). Entra en la lista pública de C1 en el paso 16, con su motivo |
| D-3 | NFRD-U3-09 | Queda decidida por D-1 | Ninguno |
| E-1 | Mapa `python/` → `veridicus_contracts` (functional-spec §1, D1, D15). Tres rondas NO-VERDE de U01-T01 por la misma causa: el mapa no lo ven la instalación editable (F-01), el sdist con enlaces (F-05) ni mypy (F-08) | Los módulos se mueven a `contracts/src/veridicus_contracts/`; el nombre de importación no cambia (decidido el 2026-11-23) | PD-9: cambian V-GUARD, V-TYPES y las rutas de los pasos 3, 10, 11, 12, 17 y 19. Exige un nuevo `Approve Plan`. Los originales que citan `contracts/python/` (functional-spec §1 y `entities.md` de U1, contract-summary, components, bolt-plan, unit-of-work-dependency y artefactos de U10, U7 y U9) se ponen al día al cerrar la etapa si el humano lo decide |
| E-2 | C2 (T05, ola 5) valida `effective_config` contra C18, que escribe T09 (ola 6) | Se extiende PD-8: el caso lleva el marcador `c18` y pasa a verde en el paso 11 (decidido el 2026-11-23) | Pasos 7 y 11 y PD-8; también `--no-cov` en el `--co -q` del paso 5 (A-1, corrección del orquestador). Exige un nuevo `Approve Plan` |
| E-5 | E-2 no alcanza: con un `$ref` a C18 ausente el registro no resuelve C2 entero (ronda 1 de U01-T03) | T05 escribe también `profiles/effective-config.v1.yaml`; T09 conserva perfiles, precios y `profiles.validate`. **Sustituye a E-2** (decidido el 2026-11-23) | Pasos 7 y 11 y PD-8. Exige un nuevo `Approve Plan` |
| E-6 | La verificación del paso 15 (T13) incluye casos `c19` que pone en verde T12, en la misma ola | La verificación de T13 excluye `c19` (`-m "not c1 and not c19"`); se conserva el paralelismo de la ola 7 (decidido el 2026-11-23) | Paso 15. Exige un nuevo `Approve Plan` |
| E-3 | *Payloads* de los *fixtures* de C6 en T03, antes de la copia de T04 | El codificador de T03 lee en solo lectura los dos `*.schema.json` de C6 en `/insumos` para darles forma; no copia nada (decidido el 2026-11-23) | Ninguno en el plan; nota en la tarea T03 |
| E-4 | Dónde y cuándo se copia C6 (PD-4) | En el worktree `tarea/U01-T04`, con un commit del humano, antes de despachar al codificador (decidido el 2026-11-23) | Ninguno en el plan; nota en la tarea T04 |
| D-2 | FD-U1-14 | Opción (b): un tramo entre «» que es solo un término prohibido **sí** se escanea. FD-U11-20 queda resuelta con esta misma decisión | Deja de estar abierta (PD-3). C8 (`excluded_spans`) y sus casos de escaneo la reflejan en el paso 13 |

## Precisiones que el agente resuelve sin preguntar

Las fuentes aprobadas ya las deciden.

| ID | Resolución |
|---|---|
| C-1 | FD-U11-03 y FD-U8-01 se unen siguiendo a FD-U8-01: `observaciones_conductor` lo arma el módulo de U8 dentro de la biblioteca, solo en modo incremental |
| C-2 | FD-U3-01 y NFR-U5-03 se unen en un solo texto de AC5.4.4 |
| C-4 | `connectionLimit` de `veridicus_app` es 30 (IDS-U4-03, `project.md`); IDS-U2-14 queda superada |
| P-T06-1 | C7 de `contract-summary.md` no pone `minLength` en `note` ni en `reformulation`, pero BR4.4 (functional-design de U1, aprobado después) exige que no estén vacíos. Se aplica BR4.4: `minLength: 1` en los dos campos, con dos *fixtures* negativos nuevos que escribe T06 (ronda 1 de U01-T06, F-01). La precisión se lleva a `contract-summary.md` al cerrar la etapa |
| P-T07-1 | `anonymizer.incident` no es respuesta de ninguna ruta: por CD-11, la corrida rechazada es `409 session.blocked` y `anonymizer.incident` es su causa (`blocked_code`) y el `codigo` de C6. Va con `http: false` y sin estado (ronda 1 de U01-T07, F-04) |
| P-T08-1 | El caso `c13-llamada` de `test_autonomia_03.py` lee también C8, que se escribe en el paso 13. CA-2 de T08 lo excluye y la tarea que escribe C8 debe correrlo en verde. La verificación del paso 10 del plan no cambia |
| P-T07-2 | Errata en una tabla de U12: «413 \| `research.invalid_type`» frente al 415 de NFR-U12-02. Manda NFR-U12-02 (415). La tabla se corrige al cerrar la etapa |
| NFR-U11-10 | La cifra N = 300 s no se lleva a `team.md`, que remite esa cifra a NFR Requirements |

## Cómo se llevan las precisiones a sus originales

- **Ahora, en commits propios, antes del código de U1:** `inception/contract-design/contract-summary.md` y `inception/domain-design/components.md`.
- **Con cada Bolt:** los demás originales de Inception y los artefactos de Construction de cada unidad se ponen al día como tarea previa de ese Bolt.
- **`team.md`:** las filas que le tocan, más el cambio a «`aidlc/` y `docs/` también por PR» (protección total de P0.1), se proponen como aprendizajes en la aprobación de Code Generation.
