# Contenedor aislado para probar AI-DLC sobre este repositorio (tai / Veridicus).
# Ubuntu + git + GitHub CLI + Claude Code + AI-DLC (AWS, binario 'aidlc'). La
# configuración de AI-DLC en el proyecto la aplica bootstrap.sh sobre /workspace.
FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    TZ=America/Bogota

# Herramientas base. Node 22 (NodeSource) no lo exige Claude Code nativo, pero lo
# usan plugins/MCP basados en npx.
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl gnupg git jq sudo less nano vim-tiny unzip \
        ripgrep procps tzdata openssh-client python3 python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://deb.nodesource.com/setup_22.x -o /tmp/nodesource.sh \
    && bash /tmp/nodesource.sh && rm /tmp/nodesource.sh \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/* \
    && node -v && npm -v

# GitHub CLI (repo oficial de apt). Hace de credential helper de git (gh auth setup-git).
RUN mkdir -p -m 755 /etc/apt/keyrings \
    && curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
        -o /etc/apt/keyrings/githubcli-archive-keyring.gpg \
    && chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
        > /etc/apt/sources.list.d/github-cli.list \
    && apt-get update && apt-get install -y gh \
    && rm -rf /var/lib/apt/lists/* \
    && gh --version

# ubuntu:24.04 trae un usuario 'ubuntu' con UID 1000: se elimina para usar 'developer'.
ARG USERNAME=developer
ARG USER_UID=1000
ARG USER_GID=1000
RUN (userdel -r ubuntu 2>/dev/null || true) \
    && groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m -s /bin/bash $USERNAME \
    && echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME \
    && mkdir -p /workspace /home/$USERNAME/.claude-config /home/$USERNAME/.config/gh \
    && chown -R $USERNAME:$USERNAME /workspace /home/$USERNAME

# El volumen /workspace puede quedar con otro dueño; evita "dubious ownership".
RUN git config --system --add safe.directory /workspace

USER $USERNAME
WORKDIR /home/$USERNAME
ENV PATH="/home/${USERNAME}/.local/bin:${PATH}"

# Claude Code (instalador nativo, en ~/.local: el auto-update funciona sin sudo).
RUN curl -fsSL https://claude.ai/install.sh | bash \
    && claude --version

# AI-DLC de AWS (awslabs/aidlc-workflows): binario 'aidlc' + runtimes de los harness.
# Versión FIJADA a propósito: un rebuild no debe cambiar el motor a mitad de un
# workflow. Para subirla: cambia el ARG, reconstruye (aidlc.bat --rebuild) y corre
# 'aidlc config --harness claude --yes' en /workspace (lo hace bootstrap.sh).
ARG AIDLC_VERSION=2.10.0
RUN curl -fsSL "https://github.com/awslabs/aidlc-workflows/releases/download/v${AIDLC_VERSION}/install.sh" \
        -o /tmp/aidlc-install.sh \
    && sh /tmp/aidlc-install.sh --version "${AIDLC_VERSION}" --yes \
    && rm /tmp/aidlc-install.sh \
    && aidlc --version \
    && sudo ln -sf /home/${USERNAME}/.local/bin/aidlc /usr/local/bin/aidlc \
    && sudo ln -sf /home/${USERNAME}/.local/bin/claude /usr/local/bin/claude
# Los symlinks en /usr/local/bin hacen que los hooks de AI-DLC encuentren 'aidlc' y
# 'claude' con el PATH base (no interactivo); sin ellos 'aidlc doctor' los marca.

COPY --chown=${USERNAME}:${USERNAME} bootstrap.sh /usr/local/bin/aidlc-bootstrap
COPY --chown=${USERNAME}:${USERNAME} statusline.sh /usr/local/bin/aidlc-statusline
RUN sudo chmod 0755 /usr/local/bin/aidlc-bootstrap /usr/local/bin/aidlc-statusline

# Toda la config de Claude (incluido .claude.json) vive aquí: bind mount al host
# en docker/.state/claude (ver compose.yml). La de ~/.claude del host NO se toca.
ENV CLAUDE_CONFIG_DIR=/home/${USERNAME}/.claude-config

WORKDIR /workspace
CMD ["sleep", "infinity"]
