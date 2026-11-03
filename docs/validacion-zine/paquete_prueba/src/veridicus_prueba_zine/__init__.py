"""Punto de entrada de prueba de M5: importa las dependencias previstas de la biblioteca, las usa una vez y
escribe sus versiones en JSON. Termina con código 0 solo si todo se importó y validó."""
import json
import sys
from importlib.metadata import version


def main() -> int:
    import httpx
    import jsonschema
    import pydantic
    import yaml

    class Quote(pydantic.BaseModel):
        texto: str
        turno: int

    quote = Quote.model_validate({"texto": "llegamos un martes", "turno": 2})
    jsonschema.validate(quote.model_dump(), {"type": "object", "required": ["texto", "turno"]})
    yaml.safe_load("perfil: todo-local")
    httpx.Client(timeout=1.0).close()
    packages = ["veridicus-prueba-zine", "pydantic", "pydantic-core", "httpx", "jsonschema", "pyyaml"]
    print(json.dumps({"python": sys.version.split()[0], **{p: version(p) for p in packages}}))
    return 0
