"""Hook de hatchling: datos del mapa visibles en la instalación editable (PD-9, CA-8).

La instalación editable de hatchling solo expone `src/`. Este hook añade, solo en
modo editable, una copia de los archivos de los directorios de datos (los de
`[tool.hatch.build.targets.wheel.sources]`, sin `fixtures/`) bajo
`veridicus_contracts/<dir>/` de site-packages. Como `veridicus_contracts` es un
paquete de espacios de nombres (sin `__init__.py`), `importlib.resources` une esa
copia con `src/veridicus_contracts/`. La copia se rehace cuando cambia un archivo
de datos (`[tool.uv] cache-keys` en pyproject.toml). La rueda no usa este hook.
"""

import tomllib
from pathlib import Path
from typing import Any

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class HookDeDatosEditables(BuildHookInterface):  # type: ignore[type-arg]  # motivo: hatchling no tipa el parámetro genérico
    PLUGIN_NAME = "custom"

    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        if version != "editable":
            return
        raiz = Path(self.root)
        configuracion = tomllib.loads((raiz / "pyproject.toml").read_text(encoding="utf-8"))
        fuentes = configuracion["tool"]["hatch"]["build"]["targets"]["wheel"]["sources"]
        for nombre in fuentes:
            if nombre == "src":
                continue
            for archivo in sorted((raiz / nombre).rglob("*")):
                relativa = archivo.relative_to(raiz)
                if archivo.is_file() and "fixtures" not in relativa.parts:
                    build_data["force_include_editable"][str(archivo)] = (
                        f"veridicus_contracts/{relativa.as_posix()}"
                    )
