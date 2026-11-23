"""Guardia de la puerta única (`checks/protocol_surface.py`, §4.17, BR9.9, E43).

Lee `model_calls.py` con `ast`, sin importarlo para comprobarlo. Las pruebas negativas parten del
código fuente real y le aplican una sola mutación, para que el rojo sea por esa causa y no por otra.
"""

import re
from pathlib import Path
from typing import Any

import pytest
from helpers import importar_o_fallar

pytestmark = pytest.mark.c13

GENERATE = "def generate(self, request: GenerateRequest) -> GenerateResult:"
PUERTA = "class AnonymizingProvider(Protocol):\n"


def _guardia() -> Any:
    return importar_o_fallar("veridicus_contracts.checks.protocol_surface", "T08")


def _ruta_del_modulo() -> Path:
    modulo = importar_o_fallar("veridicus_contracts.model_calls", "T08")
    return Path(str(modulo.__file__))


def _quitar_call(clase: str, nuevo: str) -> Any:
    """Mutación: cambia la línea `call: ModelCall` de una clase por `nuevo`."""
    patron = re.compile(rf"(class {clase}\(ModelCallError\):.*?)    call: ModelCall\n", re.DOTALL)
    return lambda fuente: patron.sub(rf"\1{nuevo}", fuente, count=1)


def _agregar_call(clase: str) -> Any:
    patron = re.compile(rf"(class {clase}\(ModelCallError\):\n)")
    return lambda fuente: patron.sub(r"\1    call: ModelCall\n", fuente, count=1)


NEGATIVOS = [
    pytest.param(
        lambda f: f.replace(PUERTA, PUERTA + "    def check_ready(self) -> bool: ...\n", 1),
        "AnonymizingProvider declara miembros distintos de generate",
        id="E43-check_ready-en-el-protocol",
    ),
    pytest.param(
        lambda f: f.replace(PUERTA, PUERTA + "    ready: bool\n", 1),
        "AnonymizingProvider declara miembros distintos de generate",
        id="atributo-en-el-protocol",
    ),
    pytest.param(
        lambda f: f.replace("def generate(self", "def emitir(self", 1),
        "AnonymizingProvider no declara generate",
        id="sin-generate",
    ),
    pytest.param(
        lambda f: f.replace(GENERATE, GENERATE.replace("request", "req"), 1),
        "la firma de generate",
        id="parametro-con-otro-nombre",
    ),
    pytest.param(
        lambda f: f.replace(GENERATE, GENERATE.replace("GenerateResult", "dict[str, Any]"), 1),
        "la firma de generate",
        id="retorno-distinto",
    ),
    pytest.param(
        lambda f: f.replace("    " + GENERATE, "    async " + GENERATE, 1),
        "AnonymizingProvider declara miembros distintos de generate",
        id="generate-asincrono",
    ),
    pytest.param(
        lambda f: f.replace(PUERTA, "class AnonymizingProvider:\n", 1),
        "AnonymizingProvider no es un Protocol",
        id="no-es-protocol",
    ),
    pytest.param(
        lambda f: f.replace(PUERTA, "class OtraCosa(Protocol):\n", 1),
        "falta la clase AnonymizingProvider",
        id="sin-la-puerta",
    ),
    pytest.param(
        lambda f: f + "\nimport os\n",
        "importa fuera del paquete de contratos: os",
        id="E43-importacion-ajena",
    ),
    pytest.param(
        lambda f: f + "\nfrom pathlib import Path\n",
        "importa fuera del paquete de contratos: pathlib",
        id="E43-importacion-ajena-con-from",
    ),
    pytest.param(
        lambda f: f + "\nfrom . import algo\n",
        "importación relativa",
        id="importacion-relativa",
    ),
    pytest.param(
        lambda f: f.replace("class InvalidOutput(ModelCallError):", "class Otro(ModelCallError):", 1),
        "falta la clase InvalidOutput",
        id="falta-un-error",
    ),
    pytest.param(
        lambda f: f.replace("class ModelCallError(Exception):", "class Raiz(Exception):", 1),
        "falta la clase ModelCallError",
        id="sin-la-raiz-de-los-errores",
    ),
    pytest.param(
        lambda f: f.replace("class Timeout(ModelCallError):", "class Timeout(Exception):", 1),
        "Timeout debe heredar de ModelCallError",
        id="error-fuera-de-la-jerarquia",
    ),
    pytest.param(
        _quitar_call("ProviderError", ""),
        "ProviderError debe declarar call: ModelCall",
        id="error-sin-call",
    ),
    pytest.param(
        _quitar_call("ContentBlocked", "    call: int\n"),
        "ContentBlocked debe declarar call: ModelCall",
        id="error-con-call-de-otro-tipo",
    ),
    pytest.param(
        _agregar_call("AnonymizerUnavailable"),
        "AnonymizerUnavailable no debe declarar call",
        id="anonimizador-no-disponible-con-call",
    ),
]


def test_model_calls_cumple_la_superficie_de_la_puerta_unica() -> None:
    """§4.17: el módulo real tiene un solo `generate`, solo importa del paquete y tipa los errores."""
    guardia = _guardia()
    ruta = _ruta_del_modulo()
    assert ruta.name == "model_calls.py"
    assert guardia.comprobar(ruta) == []


@pytest.mark.parametrize(("mutar", "esperado"), NEGATIVOS)
def test_una_sola_mutacion_pone_la_guardia_en_rojo(mutar: Any, esperado: str) -> None:
    """E43 y BR9.9: cada desvío de la superficie da su problema, y solo el código real da cero."""
    guardia = _guardia()
    fuente = _ruta_del_modulo().read_text(encoding="utf-8")
    mutada = mutar(fuente)
    assert mutada != fuente, "la mutación no cambió el código: la prueba no demuestra nada"
    problemas = guardia.comprobar_fuente(mutada)
    assert any(esperado in problema for problema in problemas), (esperado, problemas)


def test_un_texto_ajeno_no_pasa_la_guardia() -> None:
    """Control negativo: un archivo sin la puerta y con una importación ajena da dos problemas."""
    guardia = _guardia()
    problemas = guardia.comprobar_fuente("import os\n")
    assert "falta la clase AnonymizingProvider (BR9.9)" in problemas
    assert any("importa fuera del paquete de contratos: os" in p for p in problemas)
