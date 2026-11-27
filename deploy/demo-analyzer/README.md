# Demo del analizador en Minikube (B4-demo)

La CLI del analizador corre como un Job de Kubernetes sobre dos entradas sintéticas
(`deploy/demo-analyzer/entrada/contradiccion.json` y `deploy/demo-analyzer/entrada/coherente.json`).
Todo lo que sigue lo ejecuta **el humano** en la VM (AUTONOMIA-01): ningún agente ni la CI toca el clúster.

## Requisitos de la VM

- Ubuntu con Docker, `kubectl` y `minikube` instalados, y el repositorio clonado en la rama fusionada.
- Minikube con Calico, porque sin él la `NetworkPolicy` no se cumple (DP-06, R-B4d-2):
  `minikube start --cni=calico --memory=8g --cpus=4`
- Antes de seguir, compruebe que Calico quedó activo: `kubectl get pods -n kube-system -l k8s-app=calico-node`
  debe mostrar sus pods en `Running`. Si no aparecen, no continúe: la prueba de red daría un falso resultado.
- Un `.env` fuera de Git (no lo versione) con `VERIDICUS_ANTHROPIC_API_KEY`, `VERIDICUS_GHCR_USER` y
  `VERIDICUS_GHCR_TOKEN` (token de solo lectura de paquetes). Una sola línea `LLAVE=valor` por variable.

## Orden de los scripts

Se corren desde la raíz del repositorio, con `bash`, en este orden:

1. `bash scripts/humano/crear-secret-anthropic.sh <.env>`: lee `VERIDICUS_ANTHROPIC_API_KEY` y crea el Secret
   `veridicus-anthropic` en el namespace `veridicus-demo` (crea el namespace si falta). Sale con 2 si no
   recibe un archivo existente, si falta la llave o está vacía, o si el Secret ya existe con la anotación
   `last-applied-configuration` (entonces pide borrarlo y repetir).
2. `bash scripts/humano/crear-pull-secret-ghcr.sh <.env>`: lee `VERIDICUS_GHCR_USER` y `VERIDICUS_GHCR_TOKEN`
   y crea el Secret `veridicus-ghcr` (tipo docker-registry) para descargar la imagen de GHCR. Sale con 2 por
   las mismas causas, o si falta alguna llave o no tiene la forma admitida. Usuario: letras, cifras y guion,
   sin guion bajo. Token: lo mismo, más guion bajo.
3. `bash scripts/humano/demo-analyzer.sh`: sale con 2 si falta alguno de los dos Secrets; si no, borra el Job
   anterior, aplica `deploy/demo-analyzer`, espera hasta 900 s, imprime los logs, corre la prueba de red y
   termina con el código de salida del Job (0 si el análisis salió bien).

Ningún script imprime las claves. Si un Secret falta, el script lo dice y no aplica nada más.

Para usar la demo desde el navegador, el visor puede correr en la VM (`python3 scripts/humano/visor-demo.py`)
o como un pod con NodePort; lo segundo se explica en `deploy/demo-visor/README.md`.

## Qué se ve en los logs

`demo-analyzer.sh` imprime `kubectl logs` del Job, un bloque por entrada (en orden alfabético):

```
coherente: estado=ok, 0 hallazgos
contradiccion: estado=ok, 1 hallazgo
  hecho: <el hecho>
  tipo: <uno de los 7 tipos>
  cita A (turno T4): «<cita literal>»
  cita B (turno T10): «<cita literal>»
```

- `contradiccion.json` da 1 o más hallazgos, cada uno con sus dos citas verificadas; `coherente.json` da 0.
- Un hallazgo es una sugerencia para revisar, no un veredicto. El Job termina `Complete` y el script sale con 0.
- Un `estado=error` se ve como `<nombre>: estado=error, 0 hallazgos` (nunca con hallazgos) y el Job sale con 4.
  Si la CLI falla antes, el log dice `El análisis terminó con el código N; no se muestran hallazgos.`;
  con 4 la CLI informó un incidente de anonimización y el log nombra las entradas en error. Un archivo de salida dañado
  da `Falta un archivo de salida o está dañado…` y el código 5. Fuente: `deploy/src/veridicus_demo/entrypoint.py`.

## Comprobar la NetworkPolicy

Al final, `demo-analyzer.sh` lanza un pod `curl` efímero en el mismo namespace, sin la etiqueta del Job, hacia
`https://example.com`. Debe **fallar**: el script imprime `La red está cerrada…` (curl con 6, 7 o 28).
Si imprime `La NetworkPolicy NO bloquea la salida` y sale con 1, el pod sí llegó a internet: Calico no está
activo (o no se aplicó la política). Detenga la demo, repita la comprobación de Calico y no deje claves en el clúster.

## Reversión

```
kubectl delete -k deploy/demo-analyzer
kubectl delete secret veridicus-anthropic veridicus-ghcr --namespace veridicus-demo --ignore-not-found
```

El primero elimina el Job, la `NetworkPolicy` y el namespace; los Secrets no vienen del manifiesto, así que
se borran con el segundo comando si el namespace sigue existiendo. Si usó el plan B, borre también la imagen local
con `minikube image rm ghcr.io/freyesjaveriana/veridicus-analyzer-cli:<etiqueta>`. Borre el `.env` de la VM al terminar.

## Frontera de datos (AUTONOMIA-04)

- **Job `veridicus-analyzer-demo`**: corre **dentro** del clúster. Lleva el anonimizador en el mismo proceso
  y falla cerrado: sin anonimizador o sin clave no sale ninguna llamada.
- **Qué hace cada control.** La `NetworkPolicy` deja al Job salir por HTTPS (443) hacia IP públicas (no hacia
  rangos privados) y hacer DNS hacia `kube-dns`. El destino Anthropic y la seudonimización los impone el
  anonimizador dentro del proceso del Job, no la red. Lo que cruza es texto sintético seudonimizado.
- **Otros pods.** `veridicus-deny-all` niega entrada y salida solo a los pods del namespace `veridicus-demo`, y
  solo se cumple con Calico activo; los pods de `kube-system` u otros namespaces no quedan cubiertos.
- **El Secret.** Solo el Job declara `veridicus-anthropic`. En el clúster no hay una política de admisión que lo
  impida: Kyverno corre solo en la CI.
- La imagen no lleva ninguna clave. No use transcripciones reales en esta demo.

## Plan A y plan B de la imagen

Imagen: `ghcr.io/freyesjaveriana/veridicus-analyzer-cli`, con la etiqueta fijada en
`deploy/demo-analyzer/kustomization.yaml` (`images:`). Hoy es `685b12bb38ea47418d4996a447c23578e0c47e33`, el SHA
del commit de `main` de #70 que publicó la CI (run 46056005410), que imprime el motivo del error. Para
volver a la anterior, `923ecfff4b03b4168814278eb7e2bdf811016642` (digest
`sha256:7e87b25c771338ed8f0ff84b2fcfa36ed90ee3aeb40d38413ee30be17bc2f4b5`), basta un `git revert` de este cambio.

- **Plan A (normal):** `.github/workflows/analyzer-image.yml` la publica en GHCR con el SHA del commit al
  fusionar el Bolt en `main`; un PR de una línea fija ese SHA en `kustomization.yaml` (paso 11). Requiere el paquete
  vinculado al repositorio con acceso de Actions en escritura, y el Secret `veridicus-ghcr` del script 2, cuyo
  token es un PAT clásico con `read:packages`. Sin ese Secret la descarga falla (`ImagePullBackOff`).
- **Plan B (solo para la demo, desviación de `team.md`: las imágenes salen de la CI):** si la publicación falla,
  construirla en la VM con el mismo Dockerfile y el mismo contexto (la raíz del repositorio):
  `minikube image build -t ghcr.io/freyesjaveriana/veridicus-analyzer-cli:<etiqueta de kustomization.yaml> -f deploy/images/analyzer-cli/Dockerfile .`
  - Se construye antes del script 3 (`demo-analyzer.sh`), con la etiqueta exacta de `kustomization.yaml`; no
    cambie ningún manifiesto.
  - `job.yaml` no fija `imagePullPolicy`: con una etiqueta que no es móvil, Kubernetes usa la imagen local si ya
    está en Minikube y solo descarga si falta.
  - El `imagePullSecret` `veridicus-ghcr` sigue declarado y `demo-analyzer.sh` exige que exista: cree el Secret con
    el script 2, antes de `demo-analyzer.sh`, con un `.env` que lleve `VERIDICUS_GHCR_USER=relleno` y
    `VERIDICUS_GHCR_TOKEN=relleno`; en este plan no se usa para descargar.
  - Esa imagen no pasó por Trivy ni por la CI: regístrelo como desviación en la bitácora de la demo.
