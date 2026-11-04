# Bitácora de desarrollo

Estado de trabajo entre sesiones. Solo cifras y referencias: nada de texto de las entrevistas ni salidas de los modelos.

## 2026-11-03 · Validación de modelos locales en ZINE (US14.1, FR16.3)

**Dónde está AI-DLC:** intent `261002-veridicus-mvp` (scope `classic`), aparcado en `domain-design` tras aprobar
Refined Mockups (`14c0b77`). Domain Design **no empieza** hasta que `docs/validacion-zine/reporte.md` tenga M1–M6
completas y la sección `## Revisión` llena por el humano, y pase
`python3 docs/validacion-zine/comprobar_reporte.py docs/validacion-zine/reporte.md --revision` (código 0).

**Hecho hoy**
- Scripts de validación en `docs/validacion-zine/` (`dae50d5`, con push). El humano los lanzó en el clúster.
- Resultados copiados a `/insumos/app/out/validacion-zine/` (fuera de Git), revisados: sin errores en los logs; el
  SHA-256 de Qwen3.6-35B-A3B Q8_0 (`d1a39580…2794a59`) coincide en M1 y M3.

| Medición | Trabajos | Estado | Cifra |
|---|---|---|---|
| M0 · entorno | 12957 | Terminado | Python 3.12.16, jsonschema 4.23.0, llama.cpp 7e2fea0 |
| M1 · velocidad | 12963 (hpc02-w008) | Terminado | pp2048 32,05 ± 0,17 t/s; tg128 6,77 ± 0,01 t/s |
| M1 · 4L `--array=8` | 12958 parcial; 12959 al terminar | **Parcial** (12948 y 12955 sin terminar) | 8 llamadas, 0 errores, 14,83 h; con contexto real: lectura ~18,5 t/s, generación 0,85–1,25 t/s |
| M2 · API | 12964 | **En curso** | — |
| M3 · tokens | 12960 (hpchead02) | Terminado | máx. 67 769 (bloque JSON), mediana 37 022; con prompt v2 (14 832) y reserva (16 384) = 98 985 de 163 840: cabe |
| M4 · repetibilidad | 12964 | **En curso** | — |
| M5 · sin internet | 12961 y 12965 (hpc02-w008) | Terminado | entry point código 0, sin internet, 0 descargas, 18 ruedas |
| M6 · otra familia | 12962 y 12966 | **En curso** (descarga) | — |

**Observaciones para la revisión**
- (a) La cifra de `llama-bench` es de contexto corto. Con las cifras reales de la 4L, un modo final sobre la
  entrevista más larga ronda 3 h por llamada (~1 h de lectura a 18,5 t/s + ~6 600 *tokens* de salida a ~1 t/s).
  Los modelos locales sirven para lotes, no para análisis en vivo.
- (c) La entrevista más larga cabe entera con el prompt v2: el modo fragmentado no es obligatorio por tamaño, solo
  conveniente por tiempo.
- (e) La *wheelhouse* trajo jsonschema 4.26.0 porque `m5-wheelhouse` no fija versiones; no afecta la medición.
- Hay además una prueba complementaria del TG (llama.cpp repartido entre nodos por Infiniband) en
  `/insumos/app/out/infraestructura/` (`20261103-Comparativa_IngSistemas_ZINE.md`, `20261103-Prueba_RPC_ZINE.md`),
  aún sin leer.

**Siguiente paso**
1. El humano copia a `/insumos/app/out/validacion-zine/` los resultados de 12964 (`m2/`, `m4/`, sin
   `peticiones.jsonl`), 12966 (`m6/`) y, si quiere cifras completas de la 4L, 12959 (`m1/resumen_4l.txt`).
2. El agente verifica los resultados, llena las seis secciones de `reporte.md` y corre `comprobar_reporte.py`
   (sin `--revision`).
3. El humano llena `## Revisión` (revisor, fecha, decisión y respuestas (a)–(f)); se comprueba con `--revision`.
4. Commit `aidlc(validacion-zine): …` con push, y `/aidlc --resume` para Domain Design (salvo «Repetir mediciones»).
