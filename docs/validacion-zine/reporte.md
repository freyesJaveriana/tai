# Validación de los modelos locales en el clúster Ing. Sistemas (US14.1, FR16.3)

Reporte de las seis mediciones que liberan Domain Design. **Solo cifras**: ni texto de las entrevistas, ni
fragmentos, ni salidas de los modelos. Cada sección se llena copiando las líneas de
`/zine/HPC02S1/freyes/tg4L/validacion/m<n>/resumen.txt` (el paso a paso está en [README.md](README.md)).
Un resultado «No medible:» con su motivo y una línea «Salida:» también cierra el criterio.

Se comprueba con:

```bash
python3 docs/validacion-zine/comprobar_reporte.py docs/validacion-zine/reporte.md             # las seis mediciones
python3 docs/validacion-zine/comprobar_reporte.py docs/validacion-zine/reporte.md --revision  # y la revisión
```

## M0

Entorno de la validación: entorno virtual propio con `jsonschema` para M2 (no tiene criterio propio en US14.1).

Comando: sbatch trabajos/m0-entorno.sbatch
Trabajo SLURM: 12957
Nodo: hpchead02
Resultado: python 3.12.16, jsonschema 4.23.0; llama.cpp version 0.8.0-dev (build 1, commit 7e2fea0)

## M1

Velocidad de Qwen3.6-35B-A3B Q8_0 en un SL250s y horas de la medición `--array=8` de la 4L (AC14.1.1).

Comando: sbatch trabajos/m1-velocidad.sbatch (llama-bench -m Qwen3.6-35B-A3B-Q8_0.gguf -t 16 -p 2048 -n 128 -r 3 -o json)
Trabajo SLURM: 12963
Nodo: hpc02-w008
SHA-256 del modelo: d1a395809f65a43a13ad119eb4e7acdef1ac6d68120f39902c8ab96e72794a59
Resultado: pp2048 = 32.05 ± 0.17 tokens/s; tg128 = 6.77 ± 0.01 tokens/s (3 repeticiones, 16 hilos, qwen35moe 35B.A3B Q8_0, llama.cpp 1 7e2fea0)

Medición `--array=8` de la 4L (de `m1/resumen_4l.txt`, trabajo 12959 en `hpchead02`, 2026-11-05 06:23; reemplaza el
resumen parcial del trabajo 12958). La medición terminó con el trabajo 12955; el 12948 falló a las 4 h 43 min y
sus cifras son parciales:

Resultado (4L --array=8): 25 llamadas (0 con error), 51.64 h sumando llamadas, 54.27 h entre la primera y la última
Resultado (4L --array=8): tokens de entrada 280808 (caché leída 239158), de salida 225081 (razonamiento 0)
Resultado (4L --array=8): por modo: completa 2 llamadas, 9.32 h; mixta 8 llamadas, 14.65 h; fragmentada 15 llamadas, 27.67 h
Resultado (4L --array=8): servidor del trabajo 12948 (parcial): lectura 44916 tokens en 0.68 h (18.25 tokens/s); generación 12169 tokens en 3.98 h (0.85 tokens/s)
Resultado (4L --array=8): servidor del trabajo 12955: lectura 235892 tokens en 3.34 h (19.62 tokens/s); generación 212912 tokens en 43.62 h (1.36 tokens/s)

## M2

Funciones de la API compatible con OpenAI del `llama-server` de conda-forge: esquema JSON o gramática, `seed`,
caché del *prompt*, razonamiento encendido y apagado; 20 peticiones por caso (AC14.1.2).

Comando: sbatch trabajos/m2-api-servidor.sbatch (llama-server Qwen3.6-35B-A3B-Q8_0.gguf -c 16384 -t 16 -np 1 --jinja --reasoning-format deepseek --temp 0.6 --top-p 0.95 --top-k 20; sondeo_api.py --n 20)
Trabajo SLURM: 12964 (14 h 28 min; el mismo de M4)
Nodo: hpc02-w009
SHA-256 del modelo: d1a395809f65a43a13ad119eb4e7acdef1ac6d68120f39902c8ab96e72794a59
Servidor: version 0.8.0-dev (build 1, commit 7e2fea0), 16 hilos, --parallel 1
Resultado: control sin restricción: apagado, 6/20 válidas (6 reparando, 0 cortadas); encendido, 16/20 válidas (16 reparando, 3 cortadas, 20 con razonamiento)
Resultado: response_format (json_schema): apagado aceptado, 20/20 válidas (20 reparando, 0 cortadas); encendido aceptado (efecto parcial), 17/20 válidas (17 reparando, 3 cortadas, 20 con razonamiento)
Resultado: json_schema nativo: apagado aceptado, 20/20 válidas (20 reparando, 0 cortadas); encendido aceptado (efecto parcial), 17/20 válidas (17 reparando, 3 cortadas, 20 con razonamiento)
Resultado: grammar (GBNF): apagado aceptado, 20/20 válidas (20 reparando, 0 cortadas); encendido aceptado sin efecto, 0/20 válidas (0 reparando, 0 cortadas, 20 con razonamiento)
Resultado: chat_template_kwargs.enable_thinking: aceptado (con razonamiento: 20/20 encendido, 0/20 apagado)
Resultado: seed: aceptado (misma seed, salida igual: sí; otra seed, salida distinta: sí)
Resultado: cache_prompt: aceptado (con caché: cache_n 543, prompt_n 4, 2.83 s; sin caché: cache_n 0, prompt_n 547, 21.2 s)

## M3

*Tokens* de Qwen de las entrevistas del piloto frente al contexto de 163 840, con el *prompt* (AC14.1.3).

Comando: sbatch trabajos/m3-tokens.sbatch (contar_tokens.py con llama-tokenize -m Qwen3.6-35B-A3B-Q8_0.gguf; reserva de salida 16384)
Trabajo SLURM: 12960
Nodo: hpchead02
SHA-256 del modelo: d1a395809f65a43a13ad119eb4e7acdef1ac6d68120f39902c8ab96e72794a59
Resultado: 10 entrevistas del piloto contadas (sus identificadores no se copian al repositorio)
Resultado: tokens por entrevista como bloque JSON, de menor a mayor: 4463, 12255, 21713, 23383, 36587, 37458, 37765, 37979, 55843, 67769
Resultado: tokens por entrevista solo texto, de menor a mayor: 2939, 11195, 18006, 20858, 22873, 23716, 27681, 35066, 46700, 47294
Resultado: bloque JSON: máximo 67769, mediana 37022; solo texto: máximo 47294, mediana 23294
Resultado: la más larga (67769) + prompt (14832 tokens, prompt v2 de la 4L) + reserva de salida (16384) = 98985 de 163840: cabe (margen 64855)

## M4

Repetibilidad en CPU con la misma `seed`, los mismos hilos, `--parallel 1` y la misma caché del *prompt* (AC14.1.4).

Comando: sbatch trabajos/m2-api-servidor.sbatch (llama-server Qwen3.6-35B-A3B-Q8_0.gguf -c 16384 -t 16 -np 1 --jinja --reasoning-format deepseek --temp 0.6 --top-p 0.95 --top-k 20; sondeo_api.py --n 20)
Trabajo SLURM: 12964 (el mismo de M2)
Nodo: hpc02-w009
SHA-256 del modelo: d1a395809f65a43a13ad119eb4e7acdef1ac6d68120f39902c8ab96e72794a59
Servidor: version 0.8.0-dev (build 1, commit 7e2fea0), 16 hilos, --parallel 1, seed 42
Resultado: razonamiento apagado, cache_prompt false: SHA-256 igual en el par (639d35f985c678f4…)
Resultado: razonamiento apagado, cache_prompt true: SHA-256 igual en el par (639d35f985c678f4…)
Resultado: razonamiento encendido, cache_prompt false: SHA-256 igual en el par (0baa279690abcac0…)
Resultado: razonamiento encendido, cache_prompt true: SHA-256 igual en el par (0baa279690abcac0…)
Resultado: 4 de 4 pares repetibles

## M5

Instalación sin internet en un SL250s desde una *wheelhouse* (AC14.1.5).

Comando: sbatch trabajos/m5-wheelhouse.sbatch y trabajos/m5-instalar.sbatch (pip install --no-index --find-links wheelhouse veridicus-prueba-zine)
Trabajo SLURM: 12961 (wheelhouse, en hpchead02) y 12965 (instalación)
Nodo: hpc02-w008
No aplica: M5 no usa un modelo
Resultado: wheelhouse de 18 ruedas; entry point con código 0; el nodo no tiene salida a internet (esperado); líneas de descarga en el log: 0
Resultado: versiones instaladas: python 3.12.16, veridicus-prueba-zine 0.1.0, pydantic 2.14.2, pydantic-core 2.50.2, httpx 0.28.1, jsonschema 4.26.0, pyyaml 6.0.3

## M6

Verificador de una familia distinta de Qwen: familia, modelo, cuantización, `.sha256ok`, licencia y velocidad
(AC14.1.6).

Comando: sbatch trabajos/m6-descargar.sbatch y trabajos/m6-velocidad.sbatch (llama-bench -m gpt-oss-20b-Q8_0.gguf -t 16 -p 2048 -n 128 -r 3 -o json)
Trabajo SLURM: 12962 (descarga, en hpchead02) y 12966 (velocidad)
Nodo: hpc02-w008
SHA-256 del modelo: bcd455d4034ec02f71a875b46cb17df44a97911d7258291973be4d21f98329f3
Modelo: familia gpt-oss, unsloth/gpt-oss-20b-GGUF, archivo gpt-oss-20b-Q8_0.gguf (12 GB), cuantización Q8_0, licencia declarada apache-2.0
.sha256ok: bcd455d4034ec02f71a875b46cb17df44a97911d7258291973be4d21f98329f3  gpt-oss-20b-Q8_0.gguf
Resultado: pp2048 = 7.80 ± 0.01 tokens/s; tg128 = 5.30 ± 0.00 tokens/s (3 repeticiones, 16 hilos, gpt-oss 20B Q8_0, llama.cpp 1 7e2fea0)

## Nota: referencia de Pyky

No es una medición de US14.1 (no se corrió con estos scripts): son cifras de la comparativa de los tres
clústeres de ZINE que hizo el TG el 2026-11-05 (secciones 4 y 5, fuera del repositorio), con **el mismo modelo**
de M1 (Qwen3.6-35B-A3B Q8_0) y `llama-bench`. Sirven para el perfil por papel y para el equipo mínimo del modo
local (DT19), no para cerrar M1.

| Nodo | Contexto corto: pp2048 / tg128 (tokens/s) | tg64 con 45.000 tokens ocupados, *flash attention* y caché q8_0 (tokens/s) |
|---|---:|---:|
| Ing. Sistemas SL250s, 16 hilos (M1 y medición del TG) | 32,0 / 6,74 | 3,27 |
| Pyky DL360, CPU, 26 hilos (un socket) | 114,0 / 17,8 | **7,74** |
| Pyky 2 × V100 (32 GB), parte de los expertos en la CPU (`-ncmoe 24`; con 45.000 tokens, `-ncmoe 28`) | 532 / **35,8–36,8** | 27,95 |

- En GPU, el mismo modelo genera a unos **36 tokens/s** con contexto corto y a ~28 con 45.000 tokens; en CPU,
  el mejor nodo baja a **7,7 tokens/s** con 45.000 tokens. Lo que domina el tiempo es la generación con
  contexto largo, como en la 4L de M1 (1,36 tokens/s sin caché q8_0).
- En el DL360 caben dos instancias por nodo (una por socket), de 7,4 a 7,7 tokens/s cada una con 45.000 tokens.
- Con 32 GB de GPU cabe un papel por vez, no una entrevista con todos los papeles en paralelo.

## Revisión

La llena el humano después de leer M1–M6 (AC14.1.7). Decisión: exactamente una de «Diseñar con modelos
locales», «Diseñar con limitaciones registradas» (con «Limitaciones:») o «Repetir mediciones» (con «Repetir:»,
que dice cuáles). Con «Repetir mediciones», Domain Design no empieza.

Revisor: Felipe Reyes
Fecha: 2026-11-06
Decisión: Diseñar con limitaciones registradas
Limitaciones: (1) en CPU, el modo local es por lotes (horas por entrevista: la medición `--array=8` de la 4L tomó 54 h, con 1,36 tokens/s de generación con contexto largo), no interactivo en la consola; (2) la salida JSON se fuerza con `json_schema` y el razonamiento apagado (20/20); con el razonamiento encendido da 17/20 (3 cortadas) y la gramática GBNF 0/20, así que con razonamiento hace falta más reserva de salida y validación con rechazo; (3) el verificador gpt-oss lee a 7,8 tokens/s: solo verifica citas, nunca la entrevista entera.

- (a) *Tokens*/s de generación (M1) y horas estimadas de un modo final sobre la entrevista más larga (M3): pp 32,05 y tg 6,77 tokens/s; la más larga (67 769) ≈ 0,6 h de lectura, más 16 384 de salida: 0,7 h a 6,77 tokens/s o 3,3 h a 1,36 (contexto largo), así que de 1,3 a 3,9 h.
- (b) ¿M2 fuerza el esquema JSON (20 de 20 válidas) o hace falta reparar la salida?: sí con el razonamiento apagado (20/20 con `response_format` o `json_schema`); con el razonamiento encendido, 17/20, así que hay que validar y rechazar.
- (c) ¿La entrevista más larga cabe en el contexto con el *prompt* (M3), o el modo fragmentado es obligatorio con modelos locales?: cabe, 98 985 de 163 840 (margen 64 855); el modo fragmentado no es obligatorio por contexto.
- (d) ¿M4 es repetible?: sí, 4 de 4 pares con el mismo SHA-256.
- (e) ¿M5 instala sin internet?: sí, 0 descargas y código 0.
- (f) ¿M6 deja un verificador de otra familia con velocidad útil?: sí, gpt-oss-20b (apache-2.0) a 5,30 tokens/s de generación; su lectura es lenta (7,80 tokens/s).
