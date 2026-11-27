# Bitácora de B4-demo: paso 12, la demo en la VM

**Fecha:** 2026-11-27 (Job de 17:19:36Z a 17:20:06Z, 30 s).
**Lo ejecutó:** el humano, en la VM Ubuntu con Minikube y Calico (AUTONOMIA-01). El agente solo leyó por SSH
(`kubectl get`, `kubectl logs`, `kubectl get events`, `kubectl wait`).
**Commit de `main`:** 29580ea (#65). **Imagen:** `ghcr.io/freyesjaveriana/veridicus-analyzer-cli:923ecfff4b03b4168814278eb7e2bdf811016642`,
digest `sha256:7e87b25c771338ed8f0ff84b2fcfa36ed90ee3aeb40d38413ee30be17bc2f4b5`, publicada por `analyzer-image.yml`
(run 46028924313). Plan A, sin recurrir al plan B.

## Pasos

1. `bash scripts/humano/crear-secret-anthropic.sh ~/veridicus.env`: crea el namespace `veridicus-demo` y el Secret
   `veridicus-anthropic`.
2. `bash scripts/humano/crear-pull-secret-ghcr.sh ~/veridicus.env`: crea `veridicus-ghcr`.
3. `bash scripts/humano/demo-analyzer.sh`.

## Incidente del primer intento

El primer intento se quedó en `ImagePullBackOff`. GHCR respondió `403 Forbidden` al pedir el manifiesto, y desde
la VM `docker login` funcionó, pero `docker pull` dio `denied`. Causa: el token no servía para leer paquetes (no era
un PAT clásico con `read:packages`). El humano creó un PAT clásico con solo `read:packages`, volvió a correr el
script 2 y relanzó el 3. La guía ya lo exige (`deploy/demo-analyzer/README.md`, plan A). Candidata K-109: que
`crear-pull-secret-ghcr.sh` rechace un token con prefijo `github_pat_` antes de crear el Secret.

## Resultado del segundo intento

Estado del Job: `Complete`, `succeeded: 1`.

```
Aviso de propósito limitado (versión 1.0.0): …
Aviso same_family: el juez y el verificador de este perfil son de la misma familia de modelos; es un perfil de demostración y no sirve para medir.
coherente: estado=ok, 0 hallazgos
contradiccion: estado=ok, 2 hallazgos
  hecho: Dónde estuvo el hablante durante la tarde del día de la crecida: en la finca o en el pueblo
  tipo: lugar
  cita A (turno T4): «regresé a la finca a las cuatro de la tarde»
  cita B (turno T10): «Yo nunca bajé a la finca ese día, pasé toda la jornada en San Isidro hasta que oscureció.»
  hecho: Si el hablante ayudó a mover los marranos en la finca por la tarde o permaneció en el pueblo toda la jornada
  tipo: lugar
  cita A (turno T8): «Esa tarde ayudé a mover los marranos al corral alto antes de que oscureciera.»
  cita B (turno T10): «Yo nunca bajé a la finca ese día, pasé toda la jornada en San Isidro hasta que oscureció.»
curl: (6) Could not resolve host: example.com
pod veridicus-demo/veridicus-sonda-red terminated (Error)
La red está cerrada para los pods sin la etiqueta del Job (curl terminó con 6).
```

Las transcripciones son las sintéticas del ConfigMap (`deploy/demo-analyzer/entrada/`); no hay datos reales.

## Lectura

- **AUTONOMIA-05:** cada hallazgo trae `hecho`, `tipo` y dos citas literales, cada una en su turno. El relato
  coherente da 0 hallazgos. El ejemplo de la guía muestra 1 hallazgo, pero el segundo (T8 frente a T10) también es
  una contradicción real del texto sembrado, y el modelo no es determinista.
- **AUTONOMIA-03:** no aparece ninguna etiqueta de veracidad; sale el aviso de propósito limitado.
- **AUTONOMIA-04 / DP-04:** la sonda sin la etiqueta del Job no resuelve DNS (curl 6), así que `veridicus-deny-all`
  se cumple con Calico. El único pod con salida es el Job, que lleva el anonimizador dentro del proceso.
- **Perfil:** de demostración (`same_family` declarado); no sirve para medir (nivel 2).

Veredicto del paso 12: **cumplido**.
