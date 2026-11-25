"""Cobertura de fixtures por regla de nivel 0 (security-design §4.10, NFR10.10, BR1.5).

Reglas que protege: NFR10.10 (cada regla de nivel 0 tiene al menos un *fixture* positivo y uno
negativo, y el negativo falla por la regla que declara) y BR1.5 (cada cambio trae sus *fixtures*
positivos y negativos). Que los *fixtures* sean sintéticos (NFR12.1, BR1.6) lo comprueba `synthetic`.

Módulo guardia (100 % de ramas). Exige, por cada regla de `REGLAS`, un fixture `accept` y uno `reject`, y
falla si:

- un `accept` no se acepta o un `reject` no falla al validarlo contra su contrato;
- un `reject` falla solo por palabras clave del validador que su regla no declara (falla por otra regla).

Un `accept` cubre una regla si es de la misma familia de contrato que alguno de sus `reject` (`C6.entrada`
y `C6.salida` son de la familia `C6`). Quedan fuera (`EXCLUIDAS`) BR5.2 a BR5.6 (solo la forma, BR5.8),
BR1.4 (E-27), BR1.5, BR1.8 y BR12.2 (revisión del PR); cada una con su motivo en `MOTIVOS_DE_EXCLUSION`. Las reglas de nivel 0 que se prueban con código y no con documentos
van en la lista cerrada `REGLAS_CON_CODIGO`, cada una con la prueba que la cubre (E-24); `comprobar_pruebas`
verifica que esa prueba existe.

Los mensajes nombran el archivo y la regla, nunca el contenido del fixture.
"""

import ast
import importlib.resources
from collections.abc import Iterator
from functools import cache
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

from jsonschema import Draft202012Validator
from referencing import Resource
from referencing.jsonschema import DRAFT202012

from veridicus_contracts.checks._recorrido import DIRECTORIOS_SALTADOS, documentos
from veridicus_contracts.loaders import load_file
from veridicus_contracts.registry import BASE_URI, build_registry
from veridicus_contracts.validators import extract_message_payloads

REGLA = "NFR12.1"
ESTRUCTURA = frozenset({"required", "additionalProperties"})
EXCLUIDAS = ("BR5.2", "BR5.3", "BR5.4", "BR5.5", "BR5.6", "BR1.4", "BR1.5", "BR1.8", "BR12.2")
_SOLO_FORMA = "solo se valida su forma (BR5.8): el escáner de U11 ejecuta los casos"
MOTIVOS_DE_EXCLUSION: dict[str, str] = {
    **dict.fromkeys(("BR5.2", "BR5.3", "BR5.4", "BR5.5", "BR5.6"), _SOLO_FORMA),
    # E-27: regla de proceso, sin código nuevo.
    "BR1.4": (
        "regla de proceso (el cambio de forma de un contrato estricto entra en un solo PR, con su versión): "
        "la cubren la revisión del PR y la huella de seguridad de §4.11 (T19)"
    ),
    "BR1.5": "regla de proceso: la cubre la revisión del PR",
    "BR1.8": "regla de proceso: la copia de C6 entra en su propio PR, que revisa el humano",
    "BR12.2": "regla de proceso: la etiqueta de la versión la revisa el autor al fusionar el PR de B1",
}

# Regla -> palabras clave del validador por las que su `reject` puede fallar.
REGLAS: dict[str, frozenset[str]] = {
    # E-28: la cubren dos reject de queues/fixtures/runs/ (sin schema_version, y con «2.0»).
    "BR1.1": frozenset({"required", "pattern"}),
    "BR1.2": frozenset({"pattern"}),
    "BR2.1": frozenset({"required"}),
    "BR2.3": frozenset({"required"}),
    "BR3.1": ESTRUCTURA,
    "BR3.2": frozenset({"enum"}),
    "BR3.5": frozenset({"required"}),
    "BR3.6": frozenset({"maxItems"}),
    "BR4.1": frozenset({"required", "minLength", "enum"}),
    "BR4.2": frozenset({"additionalProperties"}),
    "BR4.4": frozenset({"required", "minLength", "not"}),
    "BR9.1": frozenset({"pattern"}),
    "BR9.3": frozenset({"additionalProperties"}),
    "BR10.1": frozenset({"pattern"}),
    "BR10.2": frozenset({"enum"}),
    "NFR1.3": frozenset({"additionalProperties"}),
    "NFR10.2": frozenset({"required"}),
    "NFRD-U1-07": frozenset({"additionalProperties"}),
}

# Contrato del fixture -> (archivo del paquete, puntero dentro de él).
ESQUEMAS: dict[str, tuple[str, str]] = {
    "C6.entrada": ("analyzer/v1/entrada.schema.json", ""),
    "C6.salida": ("analyzer/v1/salida.schema.json", ""),
    "C7": ("integrity/review-suggestion.v2.json", ""),
    "C18.effective-config": ("profiles/effective-config.v1.yaml", ""),
    "C18.profile-base": ("profiles/profile-base.schema.v1.yaml", ""),
    "C18.profiles": ("profiles/profiles.schema.v1.yaml", ""),
    "C19": ("cli/report.schema.v2.yaml", ""),
    "model-call": ("model_calls/model-call.v1.yaml", ""),
    "C21.request": (
        "api/anonymizer-proxy.v1.yaml",
        "#/paths/~1v1~1generate/post/requestBody/content/application~1json/schema",
    ),
}
# Familia de mensajes de cola -> AsyncAPI que los declara.
COLAS = {"C2": "queues/runs.v2.yaml", "C3": "queues/results.v2.yaml", "C5": "queues/speech.v2.yaml"}
AJENOS = DIRECTORIOS_SALTADOS - {"fixtures", "tests"}


def _familia(contrato: str) -> str:
    return contrato.split(".")[0]


def _puntero_de_cola(documento: Any, mensaje: str) -> str | None:
    cargas = extract_message_payloads(documento)
    return next((f"#/{ruta}/payload" for ruta in cargas if ruta.endswith("/" + mensaje)), None)


@cache
def _validador(contrato: str) -> Draft202012Validator | None:
    """El validador del contrato de un fixture, desde los datos del paquete; `None` si no se conoce."""
    puntero: str | None
    if contrato in ESQUEMAS:
        archivo, puntero = ESQUEMAS[contrato]
    elif _familia(contrato) in COLAS and "." in contrato:
        archivo, puntero = COLAS[_familia(contrato)], None
    else:
        return None
    documento = load_file(importlib.resources.files("veridicus_contracts") / archivo)
    if puntero is None:
        puntero = _puntero_de_cola(documento, contrato.split(".", 1)[1])
        if puntero is None:
            return None
    identificador = documento.get("$id") if isinstance(documento, dict) else None
    uri = (
        urljoin(BASE_URI, identificador)
        if isinstance(identificador, str)
        else f"{BASE_URI}_documentos/{archivo}"
    )
    recurso = Resource.from_contents(documento, default_specification=DRAFT202012)
    return Draft202012Validator(
        {"$ref": uri + puntero},
        registry=_registro().with_resource(uri, recurso),
        format_checker=Draft202012Validator.FORMAT_CHECKER,
    )


@cache
def _registro() -> Any:
    return build_registry()


def _palabras(errores: Any) -> set[str]:
    palabras: set[str] = set()
    for error in errores:
        palabras.add(str(error.validator))
        palabras |= _palabras(error.context or ())
    return palabras


def _leidos(raiz: Path) -> Iterator[tuple[str, Any, bool]]:
    """Cada archivo de una carpeta `fixtures/` bajo `raiz`: ruta relativa, contenido y si se leyó."""
    for relativa, documento, legible in documentos(raiz, AJENOS):
        if "fixtures" in relativa.split("/")[:-1]:
            yield relativa, documento, legible


def _es_fixture(documento: Any) -> bool:
    return isinstance(documento, dict) and "contract" in documento and "expectation" in documento


def fixtures(raiz: Path) -> list[tuple[str, dict[str, Any]]]:
    """Los fixtures legibles bajo `raiz` (los archivos de `fixtures/` con `contract` y `expectation`)."""
    return [(r, d) for r, d, legible in _leidos(raiz) if legible and _es_fixture(d)]


def _problemas_del_fixture(
    relativa: str, fixture: dict[str, Any], reglas: dict[str, frozenset[str]]
) -> list[str]:
    esperado = fixture["expectation"]
    if esperado not in ("accept", "reject"):
        return []
    validador = _validador(str(fixture["contract"]))
    if validador is None:
        return [f"{relativa}: contrato desconocido ({REGLA})"]
    errores = list(validador.iter_errors(fixture.get("payload")))
    if esperado == "accept":
        return [] if not errores else [f"{relativa}: el accept no se acepta ({REGLA})"]
    razon = str(fixture.get("reject_reason", "sin regla"))
    if not errores:
        return [f"{relativa}: el reject no falla ({razon}, {REGLA})"]
    if razon in reglas and not _palabras(errores) & reglas[razon]:
        return [f"{relativa}: el reject falla por otra regla ({razon}, {REGLA})"]
    return []


def comprobar(raiz: Path, reglas: dict[str, frozenset[str]] | None = None) -> list[str]:
    """Los problemas de cobertura y de causa de los fixtures bajo `raiz` (la carpeta `contracts/`)."""
    reglas = REGLAS if reglas is None else reglas
    problemas: list[str] = []
    rechazados: dict[str, set[str]] = {}
    aceptados: set[str] = set()
    for relativa, documento, legible in _leidos(raiz):
        if not legible:
            problemas.append(f"{relativa}: fixture ilegible ({REGLA})")
        elif _es_fixture(documento):
            problemas.extend(_problemas_del_fixture(relativa, documento, reglas))
            familia = _familia(str(documento["contract"]))
            if documento["expectation"] == "accept":
                aceptados.add(familia)
            elif documento["expectation"] == "reject":
                rechazados.setdefault(str(documento.get("reject_reason")), set()).add(familia)
    for regla in sorted(reglas):
        contratos = rechazados.get(regla, set())
        if not (contratos & aceptados if contratos else aceptados):
            problemas.append(f"{regla}: falta un fixture accept ({REGLA}, §4.10)")
        if not contratos:
            problemas.append(f"{regla}: falta un fixture reject ({REGLA}, §4.10)")
    return problemas


# E-24: las reglas de nivel 0 que se prueban con código y no con documentos, cada una con la prueba que la
# cubre: (archivo bajo contracts/, nombre de la prueba). Lista cerrada: una prueba fija su contenido exacto
# y añadir una entrada exige una precisión aprobada. `comprobar_pruebas` verifica que cada prueba existe.
_UNA_PRUEBA: dict[str, tuple[str, str]] = {
    "BR1.3": (
        "tests/contracts/test_queue_messages.py",
        "test_cada_fixture_de_cola_se_acepta_o_se_rechaza_por_su_regla",
    ),
    "BR1.6": (
        "tests/checks/test_synthetic.py",
        "test_los_archivos_reales_de_contracts_son_sinteticos_y_sin_numeros_largos",
    ),
    "BR1.7": (
        "tests/contracts/test_analyzer_copy.py",
        "test_sha256sums_tiene_dos_lineas_y_coincide_con_los_bytes",
    ),
    "BR1.9": ("tests/test_validators.py", "test_una_palabra_clave_desconocida_se_rechaza"),
    "BR3.3": ("tests/guards/test_autonomia_03.py", "test_ningun_nombre_ni_enum_declara_veracidad"),
    "BR3.4": ("tests/checks/test_error_codes.py", "test_tabla_c6_del_arbol_real_completa"),
    "BR4.3": (
        "tests/contracts/test_review_suggestion.py",
        "test_las_citas_referencian_la_definicion_de_c6_por_id_canonico",
    ),
    "BR5.1": (
        "tests/guards/test_autonomia_03.py",
        "test_c8_tiene_exactamente_los_terminos_aprobados",
    ),
    "BR5.7": (
        "tests/checks/test_veracity.py",
        "test_el_aviso_versionado_trae_version_y_frase_base",
    ),
    "BR5.8": (
        "tests/checks/test_scan_cases.py",
        "test_el_conjunto_versionado_cubre_cada_termino_y_cada_frase",
    ),
    "BR6.1": (
        "tests/guards/test_autonomia_03.py",
        "test_hay_exactamente_nueve_rotulos_y_uno_por_tipo",
    ),
    "BR6.2": ("tests/checks/test_veracity.py", "test_rotulos_con_una_fila_type_que_no_es_de_c6"),
    "BR6.3": (
        "tests/guards/test_autonomia_03.py",
        "test_los_rotulos_no_contienen_vocabulario_prohibido",
    ),
    "BR7.1": (
        "tests/checks/test_config_write.py",
        "test_e15_put_profiles_nombra_perfil_en_la_ruta",
    ),
    "BR7.2": (
        "tests/checks/test_error_codes.py",
        "test_toda_4xx_y_5xx_de_c1_es_una_referencia_a_problem",
    ),
    "BR7.3": ("tests/contracts/test_console.py", "test_los_cuerpos_json_de_c1_son_estrictos"),
    "BR7.4": ("tests/checks/test_error_codes.py", "test_e31_code_sin_clase"),
    "BR9.2": ("tests/test_profiles.py", "test_e23_un_alias_a_un_papel_que_no_existe_se_rechaza"),
    "BR9.4": (
        "tests/test_profiles.py",
        "test_e24_otro_clave_se_rechaza_con_un_prefijo_y_se_acepta_con_otro",
    ),
    "BR9.5": ("tests/test_profiles.py", "test_e26_un_papel_con_su_propio_fallback_se_rechaza"),
    "BR9.6": (
        "tests/typing/test_role_translation.py",
        "test_la_tabla_traduce_solo_los_tres_papeles_del_analizador_y_coincide_con_c6",
    ),
    "BR9.7": (
        "tests/contracts/test_profiles_contract.py",
        "test_la_huella_jcs_de_la_configuracion_efectiva_es_la_del_fixture",
    ),
    "BR9.8": ("tests/test_profiles.py", "test_validate_no_hace_entrada_salida_ni_lee_el_entorno"),
    "BR9.9": (
        "tests/typing/test_anonymizing_provider.py",
        "test_un_doble_con_solo_generate_pasa_mypy_estricto",
    ),
    "BR11.1": ("tests/test_limits.py", "test_e33_una_variable_que_sube_la_cifra_se_rechaza"),
    "BR12.1": ("tests/test_package_map.py", "test_la_rueda_trae_el_mapa_completo_y_sin_fixtures"),
    "BR12.3": ("tests/test_registry.py", "test_la_forma_antigua_del_ref_no_se_resuelve_e36"),
}

_CONSOLA = "tests/contracts/test_console.py"
_CODES = "tests/checks/test_error_codes.py"

# Cada regla cita una prueba o más: la primera es la positiva y las siguientes, sus controles negativos.
# P-T18-10: no hay una tercera lista; toda regla de §4.10 tiene sus fixtures o una prueba aquí.
REGLAS_CON_CODIGO: dict[str, tuple[tuple[str, str], ...]] = {
    **{regla: (prueba,) for regla, prueba in _UNA_PRUEBA.items()},
    "BR3.4": (
        (_CODES, "test_tabla_c6_del_arbol_real_completa"),
        (_CODES, "test_e34_codigo_de_c6_sin_code"),
    ),
    "BR5.1": (
        ("tests/guards/test_autonomia_03.py", "test_c8_tiene_exactamente_los_terminos_aprobados"),
        ("tests/checks/test_veracity.py", "test_c8_con_un_termino_nuevo_o_repetido_da_br51"),
    ),
    "BR8.2": (
        ("tests/checks/test_metrics.py", "test_una_metrica_sin_prefijo_o_con_forma_rota_es_rojo"),
        ("tests/checks/test_metrics.py", "test_una_etiqueta_sin_values_o_de_texto_libre_es_rojo"),
    ),
    "BR8.1": (
        (_CONSOLA, "test_toda_fecha_tiene_el_formato_unico_con_el_mismo_patron"),
        (_CONSOLA, "test_las_fechas_reales_pasan_y_las_imposibles_o_con_otra_forma_no"),
    ),
}


def _define(raiz: Path, archivo: str, nombre: str) -> bool:
    """El archivo de pruebas bajo `raiz` define una función `nombre` (de módulo o de clase)."""
    try:
        arbol = ast.parse((raiz / archivo).read_text(encoding="utf-8"))
    except (OSError, SyntaxError, UnicodeDecodeError, ValueError):
        return False
    return any(
        isinstance(nodo, ast.FunctionDef | ast.AsyncFunctionDef) and nodo.name == nombre
        for nodo in ast.walk(arbol)
    )


def comprobar_pruebas(
    raiz: Path, reglas: dict[str, tuple[tuple[str, str], ...]] | None = None
) -> list[str]:
    """Las pruebas de `REGLAS_CON_CODIGO` (y sus controles negativos) que no existen en su archivo (E-24)."""
    reglas = REGLAS_CON_CODIGO if reglas is None else reglas
    return [
        f"{regla}: la prueba {nombre} no existe en {archivo} ({REGLA}, §4.10)"
        for regla, pruebas in sorted(reglas.items())
        for archivo, nombre in pruebas
        if not _define(raiz, archivo, nombre)
    ]
