# Control negativo: dice que el usuario de GHCR admite guion bajo

## Requisitos de la VM

`minikube start --cni=calico --memory=8g --cpus=4`

## Orden de los scripts

1. `scripts/humano/crear-secret-anthropic.sh`
2. `scripts/humano/crear-pull-secret-ghcr.sh`: el usuario y el token admiten letras, cifras, guion y guion bajo.
3. `scripts/humano/demo-analyzer.sh`

## Qué se ve en los logs

Un hallazgo con dos citas, o 0 hallazgos.

## Comprobar la NetworkPolicy

El pod de prueba no debe llegar a https://example.com.

## Reversión

`kubectl delete -k deploy/demo-analyzer`

## Frontera de datos

Solo sale texto sintético seudonimizado hacia el proveedor.

## Plan A y plan B

Plan A: la imagen de la CI. Plan B: construirla en la VM.
