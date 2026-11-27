# Visor de la demo como pod de Minikube

Solo para la demo. La página no pide contraseña, porque la VM es local y solo para la demo. La imagen
no la publica la CI: se construye dentro de Minikube. El visor es el mismo
`scripts/humano/visor-demo.py`, sin cambios. El análisis sigue ocurriendo en el Job de
`deploy/demo-analyzer`, que es el único que monta la clave.

## Requisitos

- La demo del analizador aplicada al menos una vez: el namespace `veridicus-demo` y sus dos Secrets
  (scripts 1 y 2 de `deploy/demo-analyzer/README.md`).
- Salida a internet desde Minikube durante la construcción: la imagen descarga `kubectl` de `dl.k8s.io`
  y lo verifica con su SHA-256.

## Desplegar o actualizar

Desde la raíz del repositorio, en la VM:

```bash
git pull
bash scripts/humano/visor-pod.sh ~/escudo.png   # el escudo es opcional
```

El script hace estos pasos:

1. Arma el contexto de la imagen en una carpeta temporal: el visor, `deploy/demo-analyzer`, los ejemplos
   y el escudo, si se da.
2. Construye `veridicus-visor:demo` con `minikube image build`, con el `kubectl` de la versión del servidor.
   La versión se escribe en la copia del Dockerfile, porque con containerd `minikube image build` no acepta
   `build-arg`. Si la imagen no queda en Minikube, el script se detiene antes de aplicar nada.
3. Aplica esta carpeta y reinicia el pod.
4. Imprime la URL, `http://<minikube ip>:30851`.

Se vuelve a correr después de cada `git pull`.

Desde otra máquina, con el driver docker de Minikube, la IP de Minikube solo se ve dentro de la VM. En ese
caso se abre un túnel: `ssh -L 8501:<minikube ip>:30851 <usuario>@<vm>`, y luego `http://127.0.0.1:8501`.

## Qué puede hacer su cuenta

La ServiceAccount `veridicus-visor` hace lo mismo que el humano con el visor, y nada más:

- dentro de `veridicus-demo`:
  - crear, parchear, leer y borrar el Job;
  - aplicar su ConfigMap, su ServiceAccount y su NetworkPolicy;
  - leer los pods y sus logs;
- leer por nombre los dos Secrets, solo para comprobar que existen; la clave la sigue montando el Job;
- leer y parchear el Namespace `veridicus-demo`.

## Bucle GitOps con Argo CD

Después del primer despliegue, el humano instala Argo CD una vez con
`bash scripts/humano/argocd-instalar.sh` (versión v3.2.12, la última probada con Kubernetes 1.31). El script
registra `deploy/argocd/veridicus-visor.yaml`: Argo CD lee `deploy/demo-visor` de `main` y lo reconcilia
solo (`prune` y `selfHeal`). El Job del análisis queda fuera a propósito: corre una vez por caso.

El bucle se muestra así: un PR cambia `deploy/demo-visor/ejemplos.json`, que viaja como ConfigMap; el
humano lo fusiona en `main` protegida, Argo CD lo sincroniza (unos 3 minutos, o «Refresh» en su
interfaz) y el menú del visor muestra el ejemplo nuevo. Nadie aplica nada a mano. Estado:
`kubectl get applications --namespace argocd`.

La imagen sigue construyéndose en Minikube con `visor-pod.sh`: Argo CD aplica manifiestos, no construye.

### Demo con el color de la barra superior

Un cambio más visible: el color de la barra superior sale de `deploy/demo-visor/apariencia.properties`.
Viaja como el ConfigMap `veridicus-visor-apariencia`. Si el color no tiene la forma `#rrggbb`, el visor usa
el azul de siempre.

1. Una sola vez, después de fusionar este cambio, reconstruya la imagen en la VM con
   `bash scripts/humano/visor-pod.sh`. El código que lee el color va en la imagen.
2. Proponga el cambio desde una copia del repositorio con permiso de *push* y `gh` autenticado:
   `bash scripts/humano/gitops-color.sh '#c2410c'`. El script solo crea la rama, el commit y el PR;
   no toca el clúster.
3. Fusione el PR en GitHub cuando la CI esté en verde. Esa fusión es la aprobación humana.
4. En la VM, corra `bash scripts/humano/gitops-observar.sh`. El script:
   - pide a Argo CD un refresco;
   - espera a que la Application tenga el commit de `main`, con estado `Synced` y `Healthy`;
   - espera a que el pod nuevo esté listo;
   - comprueba que la página sirve el color nuevo.
5. Para devolver el cambio, corra `bash scripts/humano/gitops-color.sh --revertir`. Propone el
   `git revert` del último cambio de color. Fusiónelo y repita el paso 4.

## Evidencia de permisos

`bash scripts/humano/rbac-evidencia.sh` corre solo lecturas: `kubectl auth can-i`. Muestra:

- lo que pueden hacer la cuenta del visor y la del Job;
- una lista de cosas que no pueden hacer, por ejemplo crear pods, listar Secrets o leer `kube-system`;
- el nivel de Pod Security de los dos namespaces.

## Reversión

```bash
kubectl delete --namespace argocd application veridicus-visor
kubectl delete -k deploy/demo-visor
minikube image rm veridicus-visor:demo
```

Argo CD entero se quita con `kubectl delete namespace argocd`.

El visor en la VM (`python3 scripts/humano/visor-demo.py`) sigue sirviendo como respaldo.
