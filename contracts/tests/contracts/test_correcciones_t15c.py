"""Lecturas de vuelta de las correcciones de U01-T15c (E-16, E-17, P-T15-5).

C2 acota el texto de cada turno de `entrada` con una rama de refinamiento hermana del `$ref` a C6, y
declara el tope en bytes del mensaje; C25 marca sus dos usos. Cada corrección tiene un caso positivo
que lee el contrato real, una validacion real con el registro de esquemas y controles negativos
sobre copias en memoria. Nunca se escribe en los contratos versionados.
"""

import copy
from collections.abc import Callable
from typing import Any

from helpers import (
    cargar_fixture,
    errores_de,
    load_contract,
    puntero_de_mensaje,
    validador_de,
)

from veridicus_contracts.validators import extract_message_payloads

RUNS = "queues/runs.v2.yaml"
LIMITES = "limits.v1.yaml"
C6_ENTRADA = "analyzer/v1/entrada.schema.json"
REF_C6 = "/veridicus/contracts/analyzer/v1/entrada"
MENSAJE = "RunRequested"

Comprobacion = Callable[[Any], list[str]]


def _copia(relativa: str) -> Any:
    return copy.deepcopy(load_contract(relativa))


def _carga(c2: Any) -> Any:
    cargas = extract_message_payloads(c2)
    ruta = next(r for r in cargas if r.endswith("/" + MENSAJE))
    return cargas[ruta]


# ---- 1. C2: forma de `entrada` (E-16, P-T15-5) --------------------------------------------------

HOJA = {"maxLength", "x-veridicus-limit"}


def _problemas_de_rama(nodo: Any, c6: Any, ruta: str, es_raiz: bool = False) -> list[str]:
    """La rama solo trae `properties` e `items` por el camino de C6, y solo nombres que C6 declara."""
    if not isinstance(nodo, dict) or not isinstance(c6, dict):
        return [f"{ruta}: no es un objeto"]
    permitidas = {"properties", "items"} if not es_raiz else {"properties"}
    problemas: list[str] = []
    if "texto" in ruta.rsplit("/", 1)[-1:]:
        permitidas = HOJA
    sobrantes = set(nodo) - permitidas
    if sobrantes:
        problemas.append(f"{ruta}: claves que la rama no puede traer: {sorted(sobrantes)}")
    for nombre, hijo in nodo.get("properties", {}).items():
        declarada = c6.get("properties", {}).get(nombre)
        if declarada is None:
            problemas.append(f"{ruta}/{nombre}: propiedad que C6 no declara")
        else:
            problemas += _problemas_de_rama(hijo, declarada, f"{ruta}/{nombre}")
    if "items" in nodo:
        problemas += _problemas_de_rama(nodo["items"], c6.get("items", {}), f"{ruta}/items")
    return problemas


def comprobar_entrada(c2: Any, c6: Any) -> list[str]:
    problemas: list[str] = []
    entrada = _carga(c2)["properties"]["entrada"]
    if set(entrada) != {"allOf", "description"}:
        return [f"entrada trae {sorted(entrada)} en vez de allOf y description"]
    ramas = entrada["allOf"]
    if len(ramas) != 2:
        return [f"allOf trae {len(ramas)} ramas en vez de 2"]
    if ramas[0] != {"$ref": REF_C6}:
        problemas.append(f"la primera rama no es el $ref sin tocar: {ramas[0]!r}")
    rama = ramas[1]
    problemas += _problemas_de_rama(rama, c6, "rama", es_raiz=True)
    try:
        texto = rama["properties"]["transcripcion"]["properties"]["turnos"]["items"]["properties"]["texto"]
    except (KeyError, TypeError):
        return [*problemas, "no se llega a texto por transcripcion/turnos/items"]
    if texto.get("maxLength") != 20000:
        problemas.append(f"texto: maxLength {texto.get('maxLength')!r}")
    if texto.get("x-veridicus-limit") != "turn_max_chars":
        problemas.append(f"texto: x-veridicus-limit {texto.get('x-veridicus-limit')!r}")
    if not entrada["description"]:
        problemas.append("entrada sin description")
    return problemas


def _rama(c2: Any) -> Any:
    return _carga(c2)["properties"]["entrada"]["allOf"][1]


def _texto(c2: Any) -> Any:
    rama = _rama(c2)
    return rama["properties"]["transcripcion"]["properties"]["turnos"]["items"]["properties"]["texto"]


def test_c2_entrada_es_allof_con_el_ref_intacto_y_la_rama_del_tope_de_texto() -> None:
    assert comprobar_entrada(load_contract(RUNS), load_contract(C6_ENTRADA)) == []


def test_c2_control_negativo_sin_marca_otra_cifra_o_propiedad_nueva_se_detecta() -> None:
    c6 = load_contract(C6_ENTRADA)
    sin_marca = _copia(RUNS)
    del _texto(sin_marca)["x-veridicus-limit"]
    assert comprobar_entrada(sin_marca, c6)
    otra_cifra = _copia(RUNS)
    _texto(otra_cifra)["maxLength"] = 20001
    assert comprobar_entrada(otra_cifra, c6)
    nueva = _copia(RUNS)
    _rama(nueva)["properties"]["transcripcion"]["properties"]["campo_nuevo"] = {"type": "string"}
    assert comprobar_entrada(nueva, c6)
    con_required = _copia(RUNS)
    _rama(con_required)["required"] = ["transcripcion"]
    assert comprobar_entrada(con_required, c6)


# ---- 2. C2: validacion real del mensaje --------------------------------------------------------


def _mensaje_con_texto(longitud: int) -> dict[str, Any]:
    fixture = cargar_fixture("queues/fixtures/runs/run.valid.yaml", "C2.RunRequested")
    mensaje: dict[str, Any] = copy.deepcopy(fixture["payload"])
    mensaje["entrada"]["transcripcion"]["turnos"][1]["texto"] = "a" * longitud
    return mensaje


def test_c2_el_validador_acepta_20000_caracteres_y_rechaza_20001() -> None:
    validador = validador_de(RUNS, puntero_de_mensaje(RUNS, MENSAJE))
    assert errores_de(validador, _mensaje_con_texto(20000)) == []
    rechazados = errores_de(validador, _mensaje_con_texto(20001))
    assert any(e.validator == "maxLength" for e in rechazados), [e.message[:60] for e in rechazados]


# ---- 3. C2: tope del mensaje (E-16) --------------------------------------------------------------


def comprobar_tope_mensaje(c2: Any) -> list[str]:
    marca = _carga(c2).get("x-veridicus-max-bytes")
    if marca != "run_message_max_bytes":
        return [f"RunRequested sin x-veridicus-max-bytes: run_message_max_bytes ({marca!r})"]
    return []


def test_c2_run_requested_declara_el_tope_de_bytes_del_mensaje() -> None:
    assert comprobar_tope_mensaje(load_contract(RUNS)) == []


def test_c2_control_negativo_sin_la_marca_del_mensaje_o_con_otra_cifra_se_detecta() -> None:
    sin_marca = _copia(RUNS)
    del _carga(sin_marca)["x-veridicus-max-bytes"]
    assert comprobar_tope_mensaje(sin_marca)
    otra = _copia(RUNS)
    _carga(otra)["x-veridicus-max-bytes"] = "session_body_max_bytes"
    assert comprobar_tope_mensaje(otra)


# ---- 4. C25: used_in (E-17) ------------------------------------------------------------------------

ESPERADO_USED_IN = {"turn_max_chars": ["C1", "C2", "C5"], "run_message_max_bytes": ["C2"]}


def comprobar_used_in(catalogo: Any) -> list[str]:
    return [
        f"{nombre}: used_in {catalogo['limits'][nombre]['used_in']!r} distinto de {esperado!r}"
        for nombre, esperado in ESPERADO_USED_IN.items()
        if catalogo["limits"][nombre]["used_in"] != esperado
    ]


def test_c25_marca_los_usos_de_turn_max_chars_y_run_message_max_bytes() -> None:
    catalogo = load_contract(LIMITES)
    assert comprobar_used_in(catalogo) == []
    assert catalogo["limits"]["turn_max_chars"]["value"] == 20000
    assert catalogo["limits"]["run_message_max_bytes"]["value"] == 2097152


def test_c25_control_negativo_un_used_in_distinto_se_detecta() -> None:
    sin_c2 = _copia(LIMITES)
    sin_c2["limits"]["run_message_max_bytes"]["used_in"] = []
    assert comprobar_used_in(sin_c2)
    otro = _copia(LIMITES)
    otro["limits"]["turn_max_chars"]["used_in"] = ["C1", "C5"]
    assert comprobar_used_in(otro)
