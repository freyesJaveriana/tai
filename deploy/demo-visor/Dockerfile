# Imagen del visor de la demo, solo para la demo: no la publica la CI ni pasa por GHCR.
# La construye scripts/humano/visor-pod.sh dentro de Minikube (minikube image build) con un contexto
# armado en una carpeta temporal: el visor, deploy/demo-analyzer, los ejemplos y, si se da, el escudo.
FROM python:3.12-slim

# kubectl de la misma versión que el servidor del clúster (el script la pasa como build-arg) y
# verificado contra el SHA-256 que publica dl.k8s.io.
ARG KUBECTL_VERSION=v1.31.0
ARG KUBECTL_ARCH=amd64
ADD https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/${KUBECTL_ARCH}/kubectl /usr/local/bin/kubectl
ADD https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/${KUBECTL_ARCH}/kubectl.sha256 /tmp/kubectl.sha256
RUN python3 -c "import hashlib, sys; real = hashlib.sha256(open('/usr/local/bin/kubectl', 'rb').read()).hexdigest(); esperado = open('/tmp/kubectl.sha256').read().split()[0]; sys.exit(0 if real == esperado else 'kubectl no coincide con su SHA-256')" \
    && chmod 0755 /usr/local/bin/kubectl \
    && rm /tmp/kubectl.sha256

COPY app/ /app/

USER 10001:10001
ENV HOME=/tmp PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
EXPOSE 8501

# Con escudo (/app/escudo.png, .jpg, .jpeg o .svg) lo muestra; sin él, arranca igual.
CMD ["sh", "-c", "for f in /app/escudo.*; do [ -f \"$f\" ] && exec python3 /app/scripts/humano/visor-demo.py --host 0.0.0.0 --logo \"$f\"; done; exec python3 /app/scripts/humano/visor-demo.py --host 0.0.0.0"]
