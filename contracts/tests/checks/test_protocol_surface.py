"""Guardia de la puerta única (`checks/protocol_surface.py`, §4.17, BR9.9, E43).

Lee `model_calls.py` con `ast`, sin importarlo para comprobarlo. Las pruebas negativas parten del
código fuente real y le aplican una sola mutación, para que el rojo sea por esa causa y no por otra;
comparan el mensaje completo (con el ID de la regla y la firma), no una subcadena.
"""

import re
from pathlib import Path
from typing import Any

import pytest
from helpers import importar_o_fallar

pytestmark = pytest.mark.c13

GENERATE = "def generate(self, request: GenerateRequest) -> GenerateResult:"
PUERTA = "class AnonymizingProvider(Protocol):\n"
FIRMA_ESPERADA = "(self, request: GenerateRequest) -> GenerateResult"


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


def _firma_mala(parametros: str, retorno: str) -> str:
    return (
        f"la firma de generate es ({parametros}) -> {retorno} y debe ser {FIRMA_ESPERADA} (BR9.9)"
    )


HEREDADO = (
    "class _Listo(Protocol):\n    def check_ready(self) -> bool: ...\n\n\n"
    "class AnonymizingProvider(_Listo, Protocol):\n"
)

NEGATIVOS = [
    pytest.param(
        lambda f: f.replace(PUERTA, PUERTA + "    def check_ready(self) -> bool: ...\n", 1),
        "AnonymizingProvider declara miembros distintos de generate: "
        "def check_ready(self) -> bool: (BR9.9, E43)",
        id="E43-check_ready-en-el-protocol",
    ),
    pytest.param(
        lambda f: f.replace(PUERTA, PUERTA + "    ready: bool\n", 1),
        "AnonymizingProvider declara miembros distintos de generate: ready: bool (BR9.9, E43)",
        id="atributo-en-el-protocol",
    ),
    pytest.param(
        lambda f: f.replace("def generate(self", "def emitir(self", 1),
        "AnonymizingProvider no declara generate (BR9.9)",
        id="sin-generate",
    ),
    pytest.param(
        lambda f: f.replace(GENERATE, GENERATE.replace("request", "req"), 1),
        _firma_mala("self, req: GenerateRequest", "GenerateResult"),
        id="parametro-con-otro-nombre",
    ),
    pytest.param(
        lambda f: f.replace(GENERATE, GENERATE.replace("GenerateResult", "dict[str, Any]"), 1),
        _firma_mala("self, request: GenerateRequest", "dict[str, Any]"),
        id="retorno-distinto",
    ),
    pytest.param(
        lambda f: f.replace(GENERATE, GENERATE.replace(" -> GenerateResult", ""), 1),
        _firma_mala("self, request: GenerateRequest", ""),
        id="sin-retorno",
    ),
    pytest.param(
        lambda f: f.replace("    " + GENERATE, "    async " + GENERATE, 1),
        "AnonymizingProvider declara miembros distintos de generate: "
        "async " + GENERATE + " (BR9.9, E43)",
        id="generate-asincrono",
    ),
    pytest.param(
        lambda f: f.replace("    " + GENERATE, "    @staticmethod\n    " + GENERATE, 1),
        "generate lleva decoradores: @staticmethod (BR9.9, E43)",
        id="F-01-decorador-en-generate",
    ),
    pytest.param(
        lambda f: f.replace(PUERTA, "class AnonymizingProvider:\n", 1),
        "AnonymizingProvider debe heredar solo de Protocol, no de: ninguna (BR9.9, E43)",
        id="no-es-protocol",
    ),
    pytest.param(
        lambda f: f.replace(PUERTA, HEREDADO, 1),
        "AnonymizingProvider debe heredar solo de Protocol, no de: _Listo, Protocol (BR9.9, E43)",
        id="F-01-check_ready-heredado",
    ),
    pytest.param(
        lambda f: f.replace(PUERTA, "class OtraCosa(Protocol):\n", 1),
        "falta la clase AnonymizingProvider (BR9.9)",
        id="sin-la-puerta",
    ),
    pytest.param(
        lambda f: f + "\nimport os\n",
        "importa fuera del paquete de contratos: os (E43)",
        id="E43-importacion-ajena",
    ),
    pytest.param(
        lambda f: f + "\nfrom pathlib import Path\n",
        "importa fuera del paquete de contratos: pathlib (E43)",
        id="E43-importacion-ajena-con-from",
    ),
    pytest.param(
        lambda f: f + "\nfrom . import algo\n",
        "importación relativa: usa el nombre completo del paquete (E43)",
        id="importacion-relativa",
    ),
    pytest.param(
        lambda f: f + "\nos = __import__('os')\n",
        "llamada dinámica de importación: __import__ (E43)",
        id="F-01-dunder-import",
    ),
    pytest.param(
        lambda f: f + "\nmodulo = importlib.import_module('os')\n",
        "llamada dinámica de importación: importlib.import_module (E43)",
        id="F-01-importlib",
    ),
    pytest.param(
        lambda f: f.replace("class ModelCallError(Exception):", "class Raiz(Exception):", 1),
        "falta la clase ModelCallError (BR9.9)",
        id="sin-la-raiz-de-los-errores",
    ),
    pytest.param(
        lambda f: f.replace(
            "class InvalidOutput(ModelCallError):", "class Otro(ModelCallError):", 1
        ),
        "falta la clase InvalidOutput (BR9.9)",
        id="falta-un-error",
    ),
    pytest.param(
        lambda f: f.replace("class Timeout(ModelCallError):", "class Timeout(Exception):", 1),
        "Timeout debe heredar de ModelCallError (BR9.9)",
        id="error-fuera-de-la-jerarquia",
    ),
    pytest.param(
        _quitar_call("ProviderError", ""),
        "ProviderError debe declarar call: ModelCall (FD-U10-04)",
        id="error-sin-call",
    ),
    pytest.param(
        _quitar_call("ContentBlocked", "    call: int\n"),
        "ContentBlocked debe declarar call: ModelCall (FD-U10-04)",
        id="error-con-call-de-otro-tipo",
    ),
    pytest.param(
        _agregar_call("AnonymizerUnavailable"),
        "AnonymizerUnavailable no debe declarar call: no salió ninguna llamada (FD-U10-04)",
        id="anonimizador-no-disponible-con-call",
    ),
]

# F-02: lo permitido no genera problemas (cada mutante de la lista de importaciones muere aquí).
POSITIVOS = [
    pytest.param(lambda f: f + "\nfrom veridicus_contracts.x import y\n", id="from-del-paquete"),
    pytest.param(lambda f: f + "\nimport enum\n", id="import-enum"),
    pytest.param(lambda f: f + "\nimport typing.x\n", id="import-con-punto"),
    pytest.param(
        lambda f: f + "\nfrom veridicus_contracts.loaders import algo\n", id="from-con-punto"
    ),
    pytest.param(lambda f: f + "\nimport veridicus_contracts\n", id="import-del-paquete"),
    pytest.param(
        lambda f: f.replace(PUERTA, "class AnonymizingProvider(typing.Protocol):\n", 1),
        id="typing.Protocol",
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
    """E43 y BR9.9: cada desvío de la superficie da su problema exacto."""
    guardia = _guardia()
    fuente = _ruta_del_modulo().read_text(encoding="utf-8")
    mutada = mutar(fuente)
    assert mutada != fuente, "la mutación no cambió el código: la prueba no demuestra nada"
    assert esperado in guardia.comprobar_fuente(mutada)


@pytest.mark.parametrize("mutar", POSITIVOS)
def test_lo_permitido_no_da_problemas(mutar: Any) -> None:
    """F-02: control positivo; las importaciones permitidas y `typing.Protocol` pasan."""
    guardia = _guardia()
    fuente = _ruta_del_modulo().read_text(encoding="utf-8")
    mutada = mutar(fuente)
    assert mutada != fuente
    assert guardia.comprobar_fuente(mutada) == []


def test_comprobar_lee_el_archivo_que_recibe(tmp_path: Path) -> None:
    """F-02: `comprobar(ruta)` sobre un `model_calls.py` sembrado con `check_ready` da rojo."""
    guardia = _guardia()
    fuente = _ruta_del_modulo().read_text(encoding="utf-8")
    sembrado = tmp_path / "model_calls.py"
    sembrado.write_text(
        fuente.replace(PUERTA, PUERTA + "    def check_ready(self) -> bool: ...\n", 1),
        encoding="utf-8",
    )
    esperado = (
        "AnonymizingProvider declara miembros distintos de generate: "
        "def check_ready(self) -> bool: (BR9.9, E43)"
    )
    assert guardia.comprobar(sembrado) == [esperado]


def test_un_texto_ajeno_no_pasa_la_guardia() -> None:
    """Control negativo: un archivo sin la puerta y con una importación ajena da problemas."""
    guardia = _guardia()
    problemas = guardia.comprobar_fuente("import os\n")
    assert "falta la clase AnonymizingProvider (BR9.9)" in problemas
    assert "importa fuera del paquete de contratos: os (E43)" in problemas
