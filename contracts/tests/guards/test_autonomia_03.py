"""AUTONOMIA-03: ninguna etiqueta de veracidad; todo cambio de estado con quién y cuándo.

BR3.2 (enum iguales), BR3.3 (sin términos de veracidad en nombres), BR5.1 (9 términos),
BR6.1–BR6.3 (nueve rótulos), BR7.1 (ninguna operación escribe configuración, control E15) y BR4.4.

Cada comprobación empieza cargando el contrato que recorre, así que ninguna pasa en vacío. Los
casos que recorren varios contratos se parametrizan por contrato, cada uno con un solo marcador.

Supuesto de forma que T11 debe cumplir (o ajustar aquí): `ui/result-labels.v2.yaml` tiene un mapa
`labels` de identificador a texto (o a `{text: ...}`), con `type_<tipo>` para los siete tipos.

Rojo hasta T04 (C6), T06 (C7), T09 (C18), T11 (C8 y rótulos), T12 (C19), T13 (C21) y T14 (C1).
"""

import copy
import re
import unicodedata
from typing import Any

import pytest
from helpers import load_contract, recorrer

SALIDA = "analyzer/v1/salida.schema.json"
ENTRADA = "analyzer/v1/entrada.schema.json"
C7 = "integrity/review-suggestion.v2.json"
C8 = "integrity/forbidden-vocabulary.v2.yaml"
ROTULOS = "ui/result-labels.v2.yaml"
C1 = "api/console.v2.yaml"

TERMINOS_DE_C8 = {
    "mentiroso", "mentirosa", "miente", "mintió", "falso", "falsa", "verdadero", "verdadera", "engaño",
}  # fmt: skip
CATEGORIAS_PROHIBIDAS = {"veracity_score", "is_lying", "truthfulness", "veracidad", "credibilidad"}
ROTULOS_FIJOS = {"Sugerencia de revisión", "Contradicción en el relato"}
ROTULOS_DE_TIPO = {
    "fecha": "Fecha",
    "numero": "Número",
    "lugar": "Lugar",
    "persona": "Persona",
    "negacion": "Negación",
    "secuencia": "Secuencia",
    "otro": "Otro",
}
PALABRAS_DE_CONFIGURACION = (
    "profile", "perfil", "provider", "proveedor", "prompt", "price", "precio", "limit", "limite",
)  # fmt: skip
EXCEPCIONES_DE_CONFIGURACION = {("sessions", "profile_name")}  # solo eligen un perfil aprobado


def normalizar(texto: str) -> str:
    """Minúsculas y sin tildes, para comparar sin distinguir mayúsculas ni tildes."""
    descompuesto = unicodedata.normalize("NFKD", texto.lower())
    return "".join(c for c in descompuesto if not unicodedata.combining(c))


def terminos_y_categorias() -> tuple[set[str], set[str]]:
    c8 = load_contract(C8)
    terminos = {normalizar(t) for t in c8["terms"]}
    categorias = {normalizar(c) for c in c8["categories_forbidden_in_schemas"]}
    return terminos, categorias


def enums_de_c6() -> dict[str, set[str]]:
    salida = load_contract(SALIDA)
    defs = salida["$defs"]
    registro = defs["registro"]["properties"]
    return {
        "estado": set(salida["properties"]["estado"]["enum"]),
        "tipo": set(defs["hallazgo"]["properties"]["tipo"]["enum"]),
        "codigo": set(salida["properties"]["error"]["properties"]["codigo"]["enum"]),
        "motivo": set(registro["descartes"]["items"]["properties"]["motivo"]["enum"]),
        "papel": set(registro["llamadas"]["items"]["properties"]["papel"]["enum"]),
    }


def nombres_de_un_documento(documento: Any) -> list[str]:
    """Nombres de propiedad, de parámetro y valores de enum de cadena de un contrato."""
    nombres: list[str] = []
    for _, clave, valor in recorrer(documento):
        if clave == "properties" and isinstance(valor, dict):
            nombres += list(valor)
        elif clave == "parameters" and isinstance(valor, list):
            nombres += [p["name"] for p in valor if isinstance(p, dict) and "name" in p]
        elif clave == "enum" and isinstance(valor, str):
            nombres.append(valor)
    return nombres


def con_veracidad(nombre: str, terminos: set[str], categorias: set[str]) -> bool:
    """Igualdad de palabras: el nombre, o alguno de sus segmentos, es un término prohibido."""
    normal = normalizar(nombre)
    return normal in categorias or any(segmento in terminos for segmento in re.split(r"[_\-\s]", normal))


@pytest.mark.c6
def test_c6_tiene_exactamente_los_enum_aprobados() -> None:
    """BR3.2: tipo (7), estado (2), error.codigo (6), motivo (8) y papel (3)."""
    enums = enums_de_c6()
    assert enums["tipo"] == set(ROTULOS_DE_TIPO)
    assert enums["estado"] == {"ok", "error"}
    assert enums["codigo"] == {
        "salida_invalida", "bloqueo_contenido", "tiempo_agotado", "proveedor",
        "anonimizador_no_disponible", "incidente_anonimizacion",
    }  # fmt: skip
    assert enums["motivo"] == {
        "cita_no_verificada", "cita_en_otro_turno", "marca_alterada", "campo_faltante",
        "rechazado_verificador", "rechazado_permutacion", "fuera_de_tramo", "vocabulario_prohibido",
    }  # fmt: skip
    assert enums["papel"] == {"juez", "verificador", "verificador_permutado"}


def _enums_del_documento(documento: Any) -> list[set[str]]:
    return [
        set(valor)
        for _, clave, valor in recorrer(documento)
        if clave == "enum" and isinstance(valor, list) and all(isinstance(v, str) for v in valor)
    ]


@pytest.mark.parametrize(
    "ruta",
    [
        pytest.param(C1, marks=pytest.mark.c1, id="c1"),
        pytest.param(C7, marks=pytest.mark.c7, id="c7"),
        pytest.param("cli/report.schema.v2.yaml", marks=pytest.mark.c19, id="c19"),
    ],
)
def test_los_enum_copiados_de_c6_son_iguales(ruta: str) -> None:
    """BR3.2: todo enum que comparte dos o más valores con uno de C6 es igual a él, y `tipo` está."""
    c6 = enums_de_c6()
    del c6["estado"]  # `ok`/`error` aparecen en enum ajenos: se comprueba aparte en C19
    enums = _enums_del_documento(load_contract(ruta))
    for nombre, valores in c6.items():
        for enum in enums:
            if len(enum & valores) >= 2:
                assert enum == valores, f"{ruta}: un enum difiere del de C6 ({nombre})"
    assert c6["tipo"] in enums, f"{ruta}: no declara el enum de tipo de C6"


@pytest.mark.parametrize(
    "ruta",
    [
        pytest.param(ENTRADA, marks=pytest.mark.c6, id="c6-entrada"),
        pytest.param(SALIDA, marks=pytest.mark.c6, id="c6-salida"),
        pytest.param(C7, marks=pytest.mark.c7, id="c7"),
        pytest.param("profiles/profile-base.schema.v1.yaml", marks=pytest.mark.c18, id="c18-base"),
        pytest.param("profiles/profiles.schema.v1.yaml", marks=pytest.mark.c18, id="c18-perfiles"),
        pytest.param("profiles/effective-config.v1.yaml", marks=pytest.mark.c18, id="c18-efectiva"),
        pytest.param("cli/report.schema.v2.yaml", marks=pytest.mark.c19, id="c19-reporte"),
        pytest.param("model_calls/model-call.v1.yaml", marks=pytest.mark.c19, id="c19-llamada"),
        pytest.param("api/anonymizer-proxy.v1.yaml", marks=pytest.mark.c21, id="c21"),
        pytest.param(C1, marks=pytest.mark.c1, id="c1"),
        pytest.param("queues/runs.v2.yaml", marks=pytest.mark.asyncapi, id="c2"),
        pytest.param("queues/results.v2.yaml", marks=pytest.mark.asyncapi, id="c3"),
        pytest.param("queues/speech.v2.yaml", marks=pytest.mark.asyncapi, id="c5"),
    ],
)
def test_ningun_nombre_ni_enum_declara_veracidad(ruta: str) -> None:
    """BR3.3, AC5.5.3: sin términos de C8 ni de `categories_forbidden_in_schemas` en los nombres."""
    terminos, categorias = terminos_y_categorias()
    documento = load_contract(ruta)
    nombres = nombres_de_un_documento(documento)
    assert nombres, f"{ruta}: no tiene ningún nombre que comprobar"
    culpables = [n for n in nombres if con_veracidad(n, terminos, categorias)]
    assert culpables == [], f"{ruta}: {culpables}"


@pytest.mark.c8
def test_c8_tiene_exactamente_los_nueve_terminos() -> None:
    """BR5.1: la lista aprobada y las categorías prohibidas en esquemas."""
    c8 = load_contract(C8)
    assert len(c8["terms"]) == 9
    assert set(c8["terms"]) == TERMINOS_DE_C8
    assert set(c8["categories_forbidden_in_schemas"]) == CATEGORIAS_PROHIBIDAS


def textos_de_rotulos(documento: Any) -> dict[str, str]:
    etiquetas = documento["labels"]
    return {k: (v["text"] if isinstance(v, dict) else v) for k, v in etiquetas.items()}


def problemas_de_rotulos(documento: Any) -> list[str]:
    """BR6.1, BR6.2: exactamente nueve rótulos, y un `type_<tipo>` por cada tipo de C6."""
    textos = textos_de_rotulos(documento)
    problemas = []
    if len(textos) != 9 or set(textos.values()) != ROTULOS_FIJOS | set(ROTULOS_DE_TIPO.values()):
        problemas.append(f"los rótulos no son exactamente los nueve aprobados: {sorted(textos.values())}")
    claves_de_tipo = {k for k in textos if k.startswith("type_")}
    if claves_de_tipo != {f"type_{t}" for t in enums_de_c6()["tipo"]}:
        problemas.append(f"las filas type_* no corresponden a los tipos de C6: {sorted(claves_de_tipo)}")
    return problemas


@pytest.mark.labels
def test_hay_exactamente_nueve_rotulos_y_uno_por_tipo() -> None:
    """BR6.1, BR6.2."""
    assert problemas_de_rotulos(load_contract(ROTULOS)) == []


@pytest.mark.labels
def test_control_e17_un_decimo_rotulo_se_detecta() -> None:
    """E17: el catálogo con un décimo rótulo deja la suite en rojo."""
    copia = copy.deepcopy(load_contract(ROTULOS))
    copia["labels"]["decimo"] = "Décimo rótulo"
    assert problemas_de_rotulos(copia) != []


@pytest.mark.labels
def test_los_rotulos_no_contienen_vocabulario_prohibido() -> None:
    """BR6.3: ninguna palabra de un rótulo es un término de C8 (comparación de igualdad)."""
    terminos, _ = terminos_y_categorias()
    for texto in textos_de_rotulos(load_contract(ROTULOS)).values():
        palabras = re.findall(r"[^\W\d_]+", normalizar(texto))
        assert not set(palabras) & terminos, texto


def _puntero(documento: Any, ref: str) -> Any:
    nodo = documento
    for parte in ref.removeprefix("#/").split("/"):
        nodo = nodo[parte.replace("~1", "/").replace("~0", "~")]
    return nodo


def _nombres_del_esquema(documento: Any, esquema: Any, vistos: set[str]) -> list[str]:
    if not isinstance(esquema, dict):
        return []
    ref = esquema.get("$ref")
    if isinstance(ref, str) and ref.startswith("#/"):
        if ref in vistos:
            return []
        vistos.add(ref)
        return _nombres_del_esquema(documento, _puntero(documento, ref), vistos)
    nombres: list[str] = []
    for nombre, hijo in (esquema.get("properties") or {}).items():
        nombres.append(nombre)
        nombres += _nombres_del_esquema(documento, hijo, vistos)
    for clave in ("items", "additionalProperties"):
        nombres += _nombres_del_esquema(documento, esquema.get(clave), vistos)
    for clave in ("allOf", "anyOf", "oneOf"):
        for hijo in esquema.get(clave) or []:
            nombres += _nombres_del_esquema(documento, hijo, vistos)
    return nombres


def operaciones_que_escriben_configuracion(documento: Any) -> list[str]:
    """BR7.1: operaciones POST, PUT, PATCH o DELETE con perfil, proveedor, prompt, precio o límite."""
    culpables = []
    for ruta, item in (documento.get("paths") or {}).items():
        for metodo in ("post", "put", "patch", "delete"):
            operacion = item.get(metodo)
            if not isinstance(operacion, dict):
                continue
            nombres = [ruta]
            nombres += [p["name"] for p in operacion.get("parameters", []) if "name" in p]
            cuerpo = operacion.get("requestBody", {}).get("content", {}).get("application/json", {})
            nombres += _nombres_del_esquema(documento, cuerpo.get("schema"), set())
            for nombre in nombres:
                normal = normalizar(nombre)
                if not any(palabra in normal for palabra in PALABRAS_DE_CONFIGURACION):
                    continue
                if any(f in ruta and nombre == n for f, n in EXCEPCIONES_DE_CONFIGURACION):
                    continue
                culpables.append(f"{metodo.upper()} {ruta}: {nombre}")
    return culpables


@pytest.mark.c1
def test_ninguna_operacion_de_c1_escribe_configuracion() -> None:
    """BR7.1, AC8.3.1."""
    assert operaciones_que_escriben_configuracion(load_contract(C1)) == []


@pytest.mark.c1
def test_control_e15_un_put_profiles_se_detecta() -> None:
    """E15: una copia del OpenAPI con `PUT /profiles` deja la suite en rojo."""
    copia = copy.deepcopy(load_contract(C1))
    copia.setdefault("paths", {})["/profiles"] = {"put": {"responses": {"200": {"description": "ok"}}}}
    assert operaciones_que_escriben_configuracion(copia) != []


@pytest.mark.c7
def test_c7_registra_quien_y_cuando_decidio() -> None:
    """BR4.4: `decided_by` y `decided_at` existen, no son obligatorios siempre y las condiciones los exigen."""
    documento = load_contract(C7)
    assert {"decided_by", "decided_at", "note", "reformulation"} <= set(documento["properties"])
    assert not {"decided_by", "decided_at"} & set(documento.get("required", []))
    condiciones = documento["allOf"]
    assert len(condiciones) >= 3
    texto = str(condiciones)
    for campo in ("decided_by", "decided_at", "note", "reformulation"):
        assert campo in texto
