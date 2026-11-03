# Validación de los modelos locales en ZINE (US14.1, FR16.3)

Seis mediciones en el clúster Ing. Sistemas que **deben estar hechas y revisadas antes de Domain Design**, para
que el diseño (ventana del modo fragmentado, tiempos de espera, adaptador de modelos, perfil por papel) no se
apoye en cifras supuestas. Los scripts los escribe el agente y **los lanza el humano** (AUTONOMIA-01). Esta carpeta
va por commit directo; los `.sbatch` de producción (US14.2) entrarán por PR.

## Reglas que respetan los trabajos

- Todo paso es un `.sbatch`. En el nodo de entrada solo se usan `scp`, `sbatch`, `squeue` y `sacct`.
- Reutilizan **sin modificarlos** el entorno conda de la 4L (`tg4L/envs/tg4L`) y sus modelos (`tg4L/modelos`, con
  `.sha256ok`). Escriben solo bajo `/zine/HPC02S1/freyes/tg4L/validacion/`, con `HOME` y cachés allí mismo. La
  única excepción es la copia del GGUF en el `/tmp` local del nodo: la misma `/tmp/tg4L` que usa la 4L, o
  `/tmp/tg4L-validacion` para el modelo de M6.
- Los trabajos que van a un SL250s piden el nodo completo (`--cpus-per-task=16 --exclusive --mem=58G`), igual que
  la 4L: SLURM no hace cumplir la memoria pedida. Los que no necesitan AVX corren en `hpchead02`.
- Las entrevistas del piloto solo se copian al clúster, a `validacion/entrevistas/`, nunca a Git. Al repositorio
  vuelven solo cifras, en [reporte.md](reporte.md).

## Archivos

| Archivo | Dónde corre | Qué hace | Salida |
|---|---|---|---|
| `enviar.ps1` | este equipo | Copia por `scp` los trabajos y las 10 entrevistas del piloto. No lanza nada | `validacion/trabajos/`, `entrevistas/`, `logs/` |
| `comun.sh` | — | Rutas, `HOME`, activación del entorno y funciones comunes | — |
| `m0-entorno.sbatch` | `hpchead02` | Entorno virtual propio con `jsonschema` (lo necesita M2) | `validacion/venv`, `m0/` |
| `m1-velocidad.sbatch` | SL250s | `llama-bench` de Qwen3.6-35B-A3B Q8_0: `-p 2048 -n 128 -t 16 -r 3` | `m1/` |
| `m1-resumen-4l.sbatch` | `hpchead02` | Cifras de la medición `--array=8` de la 4L (registro y log del servidor). Se puede volver a lanzar | `m1/resumen_4l.txt` |
| `m2-api-servidor.sbatch` | SL250s | Un solo `llama-server` para M2 (API, 20 peticiones por caso) y M4 (repetibilidad) | `m2/`, `m4/` |
| `m3-tokens.sbatch` | `hpchead02` | `llama-tokenize` sobre las entrevistas, más el *prompt* y una reserva de salida, frente a 163 840 | `m3/` |
| `m5-wheelhouse.sbatch` | `hpchead02` | `pip download` de pydantic, httpx, jsonschema y pyyaml, más la rueda de `paquete_prueba/` | `m5/wheelhouse/` |
| `m5-instalar.sbatch` | SL250s | `pip install --no-index --find-links`, ejecuta el *entry point* y cuenta las descargas en el log | `m5/` |
| `m6-descargar.sbatch` | `hpchead02` | Baja un GGUF de otra familia, comprueba su SHA-256 y registra la licencia | `validacion/modelos/`, `m6/` |
| `m6-velocidad.sbatch` | SL250s | `llama-bench` de ese modelo con los parámetros de M1 | `m6/` |
| `sondeo_api.py`, `contar_tokens.py`, `resumen_4l.py`, `resumir_bench.py` | (los llaman los `.sbatch`) | Peticiones y cifras | — |
| `comprobar_reporte.py` | este equipo | Comprueba que `reporte.md` está completo (con `--revision`, también la revisión) | — |

Cada medición deja en `validacion/m<n>/resumen.txt` las líneas `Comando:`, `Trabajo SLURM:`, `Nodo:`,
`SHA-256 del modelo:` y `Resultado:` listas para copiar a `reporte.md`. Lo que está en `peticiones.jsonl`,
`bench.json` y `tokens.csv` es el detalle, y se queda en el clúster.

## Orden de lanzamiento

**1. Copiar** (en este equipo, desde `docs\validacion-zine`):

```powershell
.\enviar.ps1 -Piloto <repo del TG>\02-procedimientos\03-Corpus\salida\piloto
```

**2. Trabajos en `hpchead02`** (no compiten con la 4L; desde `/zine/HPC02S1/freyes/tg4L/validacion`):

```bash
sbatch trabajos/m0-entorno.sbatch            # anota el ID: <m0>
sbatch trabajos/m1-resumen-4l.sbatch         # otra vez cuando termine la medición --array=8
sbatch trabajos/m3-tokens.sbatch
sbatch trabajos/m5-wheelhouse.sbatch         # <wh>
sbatch trabajos/m6-descargar.sbatch          # <dl>; gpt-oss-20b Q8_0 por defecto (ver M6)
```

**3. Trabajos en un SL250s.** Compiten con la 4L, que ocupa los nodos con `--exclusive`. Tú decides el orden. Se
pueden lanzar mientras solo corra la medición `--array=8`, o encadenarlos detrás de un trabajo concreto con
`--dependency=afterany:<id>`:

```bash
sbatch trabajos/m1-velocidad.sbatch                                  # ~1 h (copia de 36,9 GB a /tmp y 3 repeticiones)
sbatch --dependency=afterok:<m0> trabajos/m2-api-servidor.sbatch     # M2 y M4; puede pasar de 15 h
sbatch --dependency=afterok:<wh> trabajos/m5-instalar.sbatch         # minutos
sbatch --dependency=afterok:<dl> trabajos/m6-velocidad.sbatch        # ~1 h
```

Para probar M2 antes de la corrida completa: `sbatch --export=ALL,N=5 --dependency=afterok:<m0>
trabajos/m2-api-servidor.sbatch` manda 5 peticiones por caso en lugar de 20. AC14.1.2 exige la corrida de 20.

**4. Seguimiento**: `squeue -u $USER` y `sacct -u $USER -S now-2days -X`. Los logs quedan en
`validacion/logs/<trabajo>_<id>.out`.

## Detalles por medición

- **M1.** `m1/resumen.txt` trae el `llama-bench`. El trabajo 12946 de la 4L sirve de referencia, pero no reemplaza
  esta medición, que es con 3 repeticiones. `m1/resumen_4l.txt` dice si la medición `--array=8` terminó; si no
  terminó en el plazo que fijaste, sus cifras son parciales y el reporte debe decirlo (pregunta 15).
- **M2.** Hay cuatro casos (control sin restricción, `response_format` con `json_schema`, `json_schema` nativo y
  `grammar` GBNF), cada uno con 20 peticiones con el razonamiento apagado y 20 con el razonamiento encendido
  (`chat_template_kwargs.enable_thinking`). Se miden aparte `seed` (dos peticiones con la misma semilla y una con
  otra) y `cache_prompt` (`timings.cache_n`). Las clasificaciones son:
  - **rechazado**: algún HTTP de error;
  - **aceptado**: 20 de 20 válidas, o «efecto parcial» si hay más válidas que en el control;
  - **aceptado sin efecto**: el resto.

  «Reparando» cuenta cuántas salidas quedan válidas al quitar las cercas de código y tomar del primer `{` al
  último `}`. Eso responde a la pregunta (b).
- **M3.** Cada entrevista se cuenta como bloque JSON de turnos (`n`, `hablante`, `pagina`, `texto`), que es lo que
  recibiría el analizador, y como texto solo. Como *prompt* de referencia se cuenta el v2 congelado de la 4L,
  porque el del analizador aún no existe. La reserva de salida es de 16 384 *tokens*. Las dos cifras se cambian con
  `--export=ALL,PROMPT=…,RESERVA=…`. Si `llama-tokenize` no corre en `hpchead02` (no tiene AVX), el script trae el
  comando para correrlo en un SL250s.
- **M4.** Se envían cuatro pares de peticiones idénticas: razonamiento apagado y encendido, cada uno con
  `cache_prompt` falso o verdadero. Cuando la caché está activa, primero va una petición de calentamiento, para que
  las dos del par encuentren la misma caché. Todas usan `seed` 42, 16 hilos y `--parallel 1`. Si los SHA-256
  difieren, se informa la posición del primer *token* distinto.
- **M5.** La *wheelhouse* se arma en `hpchead02` con el mismo Python 3.12 y la misma glibc 2.17 de los SL250s. El
  trabajo de instalación comprueba primero que el nodo no tiene internet. La línea de resultado incluye el conteo
  `grep -c -E "Downloading|Collecting .* from https?://"` sobre su propio log, que debe dar 0.
- **M6.** El modelo predeterminado es `unsloth/gpt-oss-20b-GGUF`, archivo `gpt-oss-20b-Q8_0.gguf`: familia gpt-oss
  de OpenAI, Apache 2.0, MoE con ~3,6B parámetros activos y ~12 GB. Se eligió porque, al ser MoE como Qwen3.6, debería
  tener una velocidad útil en CPU, y un modelo denso de más de 20B no la tendría. La licencia la juzgas tú frente a
  DT10; el trabajo registra la que declara el repositorio. Para otro modelo:
  `sbatch --export=ALL,REPO=<usuario/repo>,ARCHIVO=<archivo.gguf> trabajos/m6-descargar.sbatch`. Si el archivo no
  existe en el repositorio, el trabajo lista los `.gguf` que sí hay.

## Reporte y revisión

1. Copia a [reporte.md](reporte.md) las líneas de cada `resumen.txt`. Solo cifras: nada de `peticiones.jsonl`
   (lleva salidas del modelo) ni texto de las entrevistas. M2 y M4 comparten el trabajo SLURM. M5 y M6 tienen dos
   trabajos cada uno: anota los dos ID en `Trabajo SLURM:`.
2. Comprueba las seis mediciones:
   `python3 docs/validacion-zine/comprobar_reporte.py docs/validacion-zine/reporte.md`. El control negativo de la
   comprobación es `python3 docs/validacion-zine/comprobar_reporte.py --autoprueba`.
3. Llena `## Revisión`: revisor, fecha, decisión y respuestas (a)–(f). Para (a), las horas de un modo final se
   pueden estimar como *tokens* de la entrevista más larga ÷ lectura (pp) + *tokens* de salida previstos ÷ generación
   (tg). La generación cae con el contexto lleno: en la 4L bajó de 6,7 a 0,9 *tokens*/s con 45K de contexto
   (`05_bench_contexto`).
4. Comprueba con `--revision` (código 0) y haz el commit `aidlc(validacion-zine): …`. Domain Design empieza después
   de ese commit, salvo con «Repetir mediciones».
