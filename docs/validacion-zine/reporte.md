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

## M1

Velocidad de Qwen3.6-35B-A3B Q8_0 en un SL250s y horas de la medición `--array=8` de la 4L (AC14.1.1).

Comando:
Trabajo SLURM:
Nodo:
SHA-256 del modelo:
Resultado:

Medición `--array=8` de la 4L (de `m1/resumen_4l.txt`; si no terminó en el plazo, decirlo: cifras parciales):

Resultado (4L --array=8):

## M2

Funciones de la API compatible con OpenAI del `llama-server` de conda-forge: esquema JSON o gramática, `seed`,
caché del *prompt*, razonamiento encendido y apagado; 20 peticiones por caso (AC14.1.2).

Comando:
Trabajo SLURM:
Nodo:
SHA-256 del modelo:
Resultado:

## M3

*Tokens* de Qwen de las entrevistas del piloto frente al contexto de 163 840, con el *prompt* (AC14.1.3).

Comando:
Trabajo SLURM:
Nodo:
SHA-256 del modelo:
Resultado:

## M4

Repetibilidad en CPU con la misma `seed`, los mismos hilos, `--parallel 1` y la misma caché del *prompt* (AC14.1.4).

Comando:
Trabajo SLURM:
Nodo:
SHA-256 del modelo:
Resultado:

## M5

Instalación sin internet en un SL250s desde una *wheelhouse* (AC14.1.5).

Comando:
Trabajo SLURM:
Nodo:
No aplica:
Resultado:

## M6

Verificador de una familia distinta de Qwen: familia, modelo, cuantización, `.sha256ok`, licencia y velocidad
(AC14.1.6).

Comando:
Trabajo SLURM:
Nodo:
SHA-256 del modelo:
Resultado:

## Revisión

La llena el humano después de leer M1–M6 (AC14.1.7). Decisión: exactamente una de «Diseñar con modelos
locales», «Diseñar con limitaciones registradas» (con «Limitaciones:») o «Repetir mediciones» (con «Repetir:»,
que dice cuáles). Con «Repetir mediciones», Domain Design no empieza.

Revisor:
Fecha:
Decisión:

- (a) *Tokens*/s de generación (M1) y horas estimadas de un modo final sobre la entrevista más larga (M3):
- (b) ¿M2 fuerza el esquema JSON (20 de 20 válidas) o hace falta reparar la salida?:
- (c) ¿La entrevista más larga cabe en el contexto con el *prompt* (M3), o el modo fragmentado es obligatorio con modelos locales?:
- (d) ¿M4 es repetible?:
- (e) ¿M5 instala sin internet?:
- (f) ¿M6 deja un verificador de otra familia con velocidad útil?:
