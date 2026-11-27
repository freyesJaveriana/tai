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

## Reversión

```bash
kubectl delete -k deploy/demo-visor
minikube image rm veridicus-visor:demo
```

El visor en la VM (`python3 scripts/humano/visor-demo.py`) sigue sirviendo como respaldo.
