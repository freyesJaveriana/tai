# Imagen de la CLI del analizador para el Job de la demo (B4-demo, U02-T01).
# El contexto del build es la raíz del repositorio; .dockerignore deja solo contracts/, libs/ y deploy/.
# La imagen lleva el anonimizador dentro del proceso (DP-04, AUTONOMIA-04) y NO lleva ninguna clave:
# el Secret lo monta el Job en ejecución. La publica la CI con el SHA del commit, nunca con latest.

# Índice multiarquitectura de python:3.12-slim (digest dado por `docker buildx imagetools inspect`).
FROM python:3.12-slim@sha256:191083cdf6c7bda8c76158983163ead5d5cf7b77cf3033e805bb0f5296f51b4b AS build

ENV UV_PROJECT_ENVIRONMENT=/app/.venv \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# uv 0.13.9 desde su imagen oficial, fijado por versión y digest (F-01). El digest es el del índice
# OCI multiarquitectura, dado por `docker buildx imagetools inspect ghcr.io/astral-sh/uv:0.13.9`.
COPY --from=ghcr.io/astral-sh/uv:0.13.9@sha256:d3b601f0c7b118bc1753febf7c41cc80981df678445e0254284eecf84db79a7d /uv /usr/local/bin/uv

WORKDIR /src
COPY contracts /src/contracts
COPY libs /src/libs
COPY deploy /src/deploy

WORKDIR /src/deploy
RUN uv sync --frozen --no-dev --no-editable


FROM python:3.12-slim@sha256:191083cdf6c7bda8c76158983163ead5d5cf7b77cf3033e805bb0f5296f51b4b AS final

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Vincula el paquete de GHCR a este repositorio: sin ella el GITHUB_TOKEN del workflow no puede publicarlo.
LABEL org.opencontainers.image.source="https://github.com/freyesJaveriana/tai"

# Trivy: CVE-2026-124851 (HIGH, con corrección) en libzstd1 de la base, cuyo digest no ha cambiado.
# Se actualiza solo ese paquete, fijado por versión, y no se conservan las listas de apt. Va en el mismo
# RUN que crea el usuario para no abrir una capa más (hadolint DL3059).
RUN apt-get update \
    && apt-get install --only-upgrade -y --no-install-recommends libzstd1=1.5.7+dfsg-1+deb13u1 \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 demo \
    && useradd --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin demo

COPY --from=build /app/.venv /app/.venv

USER 10001:10001
ENTRYPOINT ["/app/.venv/bin/python", "-m", "veridicus_demo.entrypoint"]
