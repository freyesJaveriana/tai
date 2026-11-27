# Prueba de cambio de modelo

La guía de entrega pide al menos 10 casos de prueba y demostrar que el modelo se cambia **solo
por configuración**. Esta carpeta trae las dos cosas:

- `casos/`: 12 entrevistas sintéticas en el formato de entrada C6. Ningún relato es real.
  - 7 con una contradicción sembrada, una por cada tipo de C6: `fecha`, `numero`, `lugar`,
    `persona`, `negacion`, `secuencia` y `otro`. En todas, las dos versiones están en los turnos T2 y T8.
  - 3 relatos coherentes (SINT-EVAL-08 a 10).
  - 2 casos trampa que parecen contradictorios y no lo son. En SINT-EVAL-11 el testimonio corrige
    su propia cifra; en SINT-EVAL-12 menciona dos lugares en dos años distintos, porque se mudó.
- `esperado.json`: lo que se espera de cada caso (clase, tipo y par de turnos).

## Qué cambia entre las dos corridas

Solo el archivo de perfiles, `libs/execution_profiles/config/profiles.yaml`, que se cambia por PR.
Los dos perfiles son iguales salvo en el modelo del juez y del verificador:

| Perfil                | Modelo              |
|-----------------------|---------------------|
| `demo-anthropic`      | `claude-sonnet-5-5` |
| `demo-anthropic-opus` | `claude-opus-5-5`   |

El catálogo de capacidades del anonimizador
(`libs/anonymizer/src/veridicus_anonymizer/data/capabilities.v1.yaml`) declara el modelo nuevo.
No cambia ninguna línea de código: ni el prompt, ni el adaptador, ni la CLI. Una prueba lo
comprueba: si al perfil Opus se le pone el modelo de Sonnet, queda idéntico a `demo-anthropic`.

## Cómo correrla

La corre el humano, porque sale a internet con la clave real:

```bash
VERIDICUS_ANTHROPIC_API_KEY=... bash scripts/humano/cambio-modelo.sh
```

El script:

1. Corre la CLI una vez con cada perfil sobre `casos/`. Todo pasa por el anonimizador de la CLI.
2. Guarda las salidas en `resultados-locales/cambio-modelo/<fecha>/`, carpeta que Git ignora.
3. Compara las dos corridas con `python -m veridicus_demo.cambio_modelo`.

El comparador no llama a ningún modelo. Imprime una tabla por caso y un resumen por perfil:

- citas comprobadas de nuevo contra el texto del turno;
- contradicciones detectadas, con el tipo y los turnos esperados;
- hallazgos de más en coherentes y trampas;
- errores, llamadas, tokens y segundos.

El reporte JSON lleva solo identificadores, cifras y nombres de modelo, nunca texto del relato.

Las cifras de una corrida no son un umbral: con 12 casos sirven para comparar dos modelos
sobre lo mismo, no para medir la precisión del analizador.
