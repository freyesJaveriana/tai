"""Guardia del reporte de la CLI C19 v2 (BR10.1, BR10.2, NFR1.4; E28, E29; FD-U1-03, FD-U1-05).

Comprueba que el esquema del reporte (`cli/report.schema.v2.yaml`) y el de las llamadas
(`model_calls/model-call.v1.yaml`) siguen cerrados: ninguna cadena de texto libre, ningún número sin
tope y las llamadas restringidas a los tres papeles del analizador. Comprueba también que los tres
*fixtures* negativos de C19 siguen ahí y se rechazan por su regla. Solo lee. Ningún mensaje lleva
valores de un reporte, solo reglas y rutas del esquema.

Límite declarado (FD-U1-05): una palabra suelta del alfabeto permitido cabe en un campo con patrón;
el esquema no puede distinguirla de un nombre de modelo. Lo cierra U12 (el *canary* no aparece en
filas ni en logs).
"""

import re
import string
from collections.abc import Iterator, Mapping
from functools import lru_cache
from pathlib import Path
from typing import Any

from veridicus_contracts.loaders import LoadError, load_file

C19 = "cli/report.schema.v2.yaml"
MODELO_DE_LLAMADA = "model_calls/model-call.v1.yaml"
DIRECTORIO_DE_FIXTURES = "cli/fixtures"

MAXIMO_ENTERO = 2**53 - 1
MAXIMO_COSTO = 10**9
MAXIMO_DE_CADENA = 128
LIMITE_DE_CADENA = "report_token_max_chars"
PAPELES = frozenset({"judge", "verifier", "verifier_permuted"})
REFERENCIA_A_LLAMADA = "/veridicus/contracts/model_calls/model-call.v1"
SITIO_DE_LLAMADAS = "$.properties.runs.items.properties.calls.items"

FIXTURES_NEGATIVOS: Mapping[str, str] = {
    "report.role-prueba-a.json": "BR10.2",
    "report.testimony-in-model.json": "BR10.1",
    "report.testimony-in-price-table.json": "BR10.1",
}

PALABRA_DEL_CANARY = "CANARIO-7f3a"
LIMITE_DECLARADO_DEL_CANARY = (
    "FD-U1-05: una palabra suelta del alfabeto permitido (p. ej. un canary sin espacios) cabe en un "
    "campo con patrón y pasa el esquema; que no aparezca en filas ni en logs lo cierra U12."
)

_CIERRES = ("type", "$ref", "enum", "const")
_ESPACIO = re.compile(r"\s")
# La ronda 2 sondeaba cuatro caracteres: espacio, tabulador,"\u00a0", salto de línea y NBSP; ahora son todos los de isspace().
# Todo carácter para el que `str.isspace()` es verdadero (el último es U+3000).
SONDAS = tuple(c for c in map(chr, range(0x3100)) if c.isspace())
_FRAGMENTO_DE_PATRON = re.compile(r"\[[^\]]*\]|\\.|.", re.DOTALL)
_LETRAS_Y_CIFRAS = string.ascii_letters + string.digits
_RANGOS = (("a", "z"), ("A", "Z"), ("0", "9"))
_LITERALES_FUERA_DE_CLASE = frozenset(_LETRAS_Y_CIFRAS + "_-:/@")
_LITERALES_EN_CLASE = frozenset(_LETRAS_Y_CIFRAS + "._:/@+")
_ESCAPES_BLANCOS = frozenset(".-+")
_CLASE = re.compile(r"\[((?:\\.|[^\]\\])*)\]")
_CUANTIFICADOR = re.compile(r"\{[0-9]{1,3}(,[0-9]{0,3})?\}")


def _recorrer(
    nodo: Any, sitio: str = "$", clave: str | None = None
) -> Iterator[tuple[str, str | None, Any]]:
    """Recorre un documento en profundidad: (ruta, clave del padre, valor)."""
    yield sitio, clave, nodo
    if isinstance(nodo, dict):
        for hija, valor in nodo.items():
            yield from _recorrer(valor, f"{sitio}.{hija}", hija)
    elif isinstance(nodo, list):
        for indice, valor in enumerate(nodo):
            yield from _recorrer(valor, f"{sitio}[{indice}]", clave)


def _bajar(nodo: Any, *claves: str) -> Any:
    """Baja por una cadena de claves; `None` si algún paso no es un objeto o no existe."""
    for clave in claves:
        if not isinstance(nodo, Mapping):
            return None
        nodo = nodo.get(clave)
    return nodo


def _tipos(nodo: Mapping[str, Any]) -> list[str]:
    tipo = nodo.get("type")
    if isinstance(tipo, str):
        return [tipo]
    return [t for t in tipo if isinstance(t, str)] if isinstance(tipo, list) else []


def _es_numero(valor: Any) -> bool:
    return isinstance(valor, int | float) and not isinstance(valor, bool)


def _valores_cerrados(nodo: Mapping[str, Any]) -> list[Any]:
    valores: list[Any] = []
    if isinstance(nodo.get("enum"), list):
        valores.extend(nodo["enum"])
    if "const" in nodo:
        valores.append(nodo["const"])
    return valores


def _problemas_de_numero(
    nodo: Mapping[str, Any], sitio: str, rotulo: str, tipos: list[str]
) -> list[str]:
    es_entero = "integer" in tipos
    if not (es_entero or "number" in tipos):
        return []
    minimo: Any = nodo.get("minimum")
    maximo: Any = nodo.get("maximum")
    tope = MAXIMO_ENTERO if es_entero else MAXIMO_COSTO
    piso = -MAXIMO_ENTERO if es_entero and sitio.endswith(".properties.seed") else 0
    if (
        _es_numero(minimo)
        and _es_numero(maximo)
        and (not es_entero or (isinstance(minimo, int) and isinstance(maximo, int)))
        and piso <= minimo <= maximo <= tope
    ):
        return []
    return [
        f"NFR1.4 {rotulo}: {'entero' if es_entero else 'número'} sin minimum o maximum acotados"
    ]


@lru_cache(maxsize=4096)
def _fragmento_admite_espacio(fragmento: str) -> bool:
    """Un fragmento del patrón (clase, escape o carácter) acepta algún carácter de espacio en blanco.

    Función pura de una cadena: los mismos fragmentos se repiten en cada patrón de los contratos.
    """
    try:
        return any(re.fullmatch(fragmento, sonda) for sonda in SONDAS)
    except re.error:
        return False  # fragmento que solo existe dentro de una construcción mayor: no acepta por sí solo


def _rango_valido(inicio: str, fin: str) -> bool:
    return any(bajo <= inicio <= fin <= alto for bajo, alto in _RANGOS)


def _clase_valida(cuerpo: str) -> bool:
    """Clase con rangos dentro de A-Za-z0-9, los literales de la lista y los escapes `\\.`, `\\-`, `\\+`."""
    elementos: list[tuple[str, bool]] = []
    posicion = 0
    while posicion < len(cuerpo):
        if cuerpo[posicion] == "\\":
            if cuerpo[posicion + 1 : posicion + 2] not in _ESCAPES_BLANCOS:
                return False
            elementos.append((cuerpo[posicion + 1], True))
            posicion += 2
        else:
            elementos.append((cuerpo[posicion], False))
            posicion += 1
    indice = 0
    while indice < len(elementos):
        letra, escapado = elementos[indice]
        guion = indice + 1 < len(elementos) and elementos[indice + 1] == ("-", False)
        if guion and indice + 2 < len(elementos):
            fin, fin_escapado = elementos[indice + 2]
            if escapado or fin_escapado or not _rango_valido(letra, fin):
                return False
            indice += 3
            continue
        extremo = indice in (0, len(elementos) - 1)
        if not (escapado or letra in _LITERALES_EN_CLASE or (letra == "-" and extremo)):
            return False
        indice += 1
    return True


@lru_cache(maxsize=4096)
def _en_la_gramatica_blanca(patron: str) -> bool:
    """Solo `^`, `$`, clases con rangos de A-Za-z0-9, `\\.`, `\\-`, `\\+`, literales, `( ) | ?` y cuantificadores.

    Limitación declarada (ReDoS sin cuantificadores anidados): la guardia rechaza un cuantificador
    sobre un grupo que ya contiene otro, pero admite `^(a|a)+$` y varios `[a-z]*` seguidos, que
    también pueden retroceder en exceso. Los patrones solo entran por PR con revisión y llevan un
    tope de 128 caracteres; la regla no se amplía.

    `(?` solo se admite como `(?:`: las banderas en línea (`(?i:`, `(?a:`, `(?-i:`) compilan en
    Python pero no en ECMA con la bandera `u`, y romperían a `contracts/ts/`.
    """
    try:
        re.compile(patron)
    except re.error:
        return False
    cuerpo = patron.removeprefix("^").removesuffix("$")
    grupos: list[bool] = []  # por grupo abierto: ¿ya contiene un cuantificador?
    posicion = 0
    while posicion < len(cuerpo):
        letra = cuerpo[posicion]
        if letra == "(":
            if (
                cuerpo[posicion + 1 : posicion + 2] == "?"
                and cuerpo[posicion + 2 : posicion + 3] != ":"
            ):
                return False
            grupos.append(False)
            posicion += 1
        elif letra == ")":
            interno = grupos.pop()  # re.compile ya garantizó que los paréntesis cuadran
            cuantificado = cuerpo[posicion + 1 : posicion + 2] in ("*", "+", "{")
            if interno and cuantificado:
                return False  # cuantificador anidado: ReDoS
            if grupos:
                grupos[-1] = grupos[-1] or interno or cuantificado
            posicion += 1
        elif letra == "|":
            if not grupos:
                return False  # una alternancia fuera de un grupo burla el anclaje
            posicion += 1
        elif letra in ("*", "+"):
            if grupos:
                grupos[-1] = True
            posicion += 1
        elif letra == "[":
            clase = _CLASE.match(cuerpo, posicion)
            if clase is None or not _clase_valida(clase.group(1)):
                return False
            posicion = clase.end()
        elif letra == "\\":
            if cuerpo[posicion + 1 : posicion + 2] not in _ESCAPES_BLANCOS:
                return False
            posicion += 2
        elif letra in _LITERALES_FUERA_DE_CLASE or letra == "?":
            posicion += 1
        elif letra == "{":
            cuantificador = _CUANTIFICADOR.match(cuerpo, posicion)
            if cuantificador is None:
                return False
            if grupos:
                grupos[-1] = True
            posicion = cuantificador.end()
        else:
            return False
    return True


def _problema_de_alfabeto(patron: str, rotulo: str) -> list[str]:
    """El patrón se juzga por lo que acepta (sondas) y por una gramática blanca, no por una lista negra."""
    if any(_fragmento_admite_espacio(f) for f in _FRAGMENTO_DE_PATRON.findall(patron)):
        return [f"BR10.1 {rotulo}: el patrón admite espacios"]
    if not _en_la_gramatica_blanca(patron):
        return [
            (
                f"BR10.1 {rotulo}: el patrón sale de la gramática cerrada (anclas, clases con rangos de "
                "A-Za-z0-9, \\., \\-, \\+, ( ) | ?, cuantificadores)"
            )
        ]
    return []


def _problemas_de_patron(nodo: Mapping[str, Any], rotulo: str, en_reporte: bool) -> list[str]:
    patron = nodo["pattern"]
    problemas: list[str] = _problema_de_alfabeto(patron, rotulo)
    if not (patron.startswith("^") and patron.endswith("$")):
        problemas.append(f"BR10.1 {rotulo}: el patrón no está anclado con ^ y $")
    largo = nodo.get("maxLength")
    if isinstance(largo, bool) or not isinstance(largo, int) or largo > MAXIMO_DE_CADENA:
        problemas.append(f"BR10.1 {rotulo}: maxLength ausente o mayor que {MAXIMO_DE_CADENA}")
    elif en_reporte and largo != MAXIMO_DE_CADENA:
        problemas.append(f"BR10.1 {rotulo}: maxLength distinto de {MAXIMO_DE_CADENA}")
    if en_reporte and nodo.get("x-veridicus-limit") != LIMITE_DE_CADENA:
        problemas.append(f"BR10.1 {rotulo}: falta x-veridicus-limit: {LIMITE_DE_CADENA}")
    return problemas


def _esquema_abierto(esquema: Any) -> bool:
    """`true` o un subesquema sin `type`, `$ref`, enum, const ni composición: acepta cualquier valor."""
    if esquema is True:
        return True
    return isinstance(esquema, dict) and not _cierra(esquema)


def _cierra(esquema: Any) -> bool:
    """Un nodo se cierra con `type`, `$ref`, `enum` o `const`; `allOf` basta con una rama que cierre.

    `false` cuenta como cerrado: no acepta ningún valor, así que no abre nada.
    """
    if esquema is False:
        return True
    if not isinstance(esquema, dict):
        return False
    if any(k in esquema for k in _CIERRES):
        return True
    todas = esquema.get("allOf")
    if isinstance(todas, list) and any(_cierra(rama) for rama in todas):
        return True
    for palabra in ("anyOf", "oneOf"):
        ramas = esquema.get(palabra)
        if isinstance(ramas, list) and ramas and all(_cierra(rama) for rama in ramas):
            return True
    return False


def _cerrado_por_nombres(nombres: Any) -> bool:
    """`propertyNames` cerrado: un `enum` no vacío o un `const`."""
    if not isinstance(nombres, Mapping):
        return False
    valores = nombres.get("enum")
    return (isinstance(valores, list) and len(valores) > 0) or "const" in nombres


def _problemas_de_subesquemas(
    nodo: Mapping[str, Any], sitio: str, prefijo: str, tipos: list[str]
) -> list[str]:
    """`items`, `additionalProperties`, `anyOf` y `oneOf` no admiten un subesquema abierto."""
    abiertos: list[str] = []
    for palabra in (
        "items",
        "contains",
        "additionalItems",
        "unevaluatedItems",
        "unevaluatedProperties",
    ):
        if _esquema_abierto(nodo.get(palabra)):
            abiertos.append(f"{sitio}.{palabra}")
    posicionales = nodo.get("prefixItems")
    for indice, rama in enumerate(posicionales if isinstance(posicionales, list) else []):
        if _esquema_abierto(rama):
            abiertos.append(f"{sitio}.prefixItems[{indice}]")
    adicionales = nodo.get("additionalProperties")
    if _esquema_abierto(adicionales) and (adicionales is not True or "object" not in tipos):
        abiertos.append(f"{sitio}.additionalProperties")
    for palabra in ("anyOf", "oneOf"):
        ramas = nodo.get(palabra)
        for indice, rama in enumerate(ramas if isinstance(ramas, list) else []):
            if _esquema_abierto(rama):
                abiertos.append(f"{sitio}.{palabra}[{indice}]")
    return [f"BR10.1 {prefijo}{a}: esquema abierto (acepta cualquier valor)" for a in abiertos]


def _problemas_de_nodo(
    nodo: Mapping[str, Any], sitio: str, prefijo: str, en_reporte: bool
) -> list[str]:
    rotulo = f"{prefijo}{sitio}"
    tipos = _tipos(nodo)
    problemas: list[str] = []
    if "object" in tipos and nodo.get("additionalProperties", True) is True:
        problemas.append(f"BR10.1 {rotulo}: objeto sin additionalProperties cerrado")
    if isinstance(nodo.get("additionalProperties"), Mapping) and not _cerrado_por_nombres(
        nodo.get("propertyNames")
    ):
        problemas.append(
            f"BR10.1 {rotulo}: additionalProperties sin propertyNames cerrado (enum o const)"
        )
    if "array" in tipos and "items" not in nodo:
        problemas.append(f"BR10.1 {rotulo}: array sin items cerrado")
    if "patternProperties" in nodo:
        problemas.append(f"BR10.1 {rotulo}: patternProperties no se admite")
    problemas.extend(_problemas_de_subesquemas(nodo, sitio, prefijo, tipos))
    for valor in _valores_cerrados(nodo):
        if isinstance(valor, str) and (_ESPACIO.search(valor) or len(valor) > MAXIMO_DE_CADENA):
            problemas.append(
                f"BR10.1 {rotulo}: un valor de enum o const lleva espacios o pasa de "
                f"{MAXIMO_DE_CADENA} caracteres"
            )
            break
    if isinstance(nodo.get("pattern"), str):
        problemas.extend(_problemas_de_patron(nodo, rotulo, en_reporte))
    elif (
        "string" in tipos
        and "enum" not in nodo
        and "const" not in nodo
        and (en_reporte or nodo.get("format") != "date-time")
    ):
        problemas.append(f"BR10.1 {rotulo}: cadena abierta (sin enum, const, formato ni patrón)")
    problemas.extend(_problemas_de_numero(nodo, sitio, rotulo, tipos))
    return problemas


def _problemas_de_forma(documento: Any, prefijo: str, en_reporte: bool) -> list[str]:
    """BR10.1 y NFR1.4 sobre todo el documento: cadenas cerradas, objetos cerrados, números con tope."""
    problemas: list[str] = []
    for sitio, clave, nodo in _recorrer(documento):
        if not isinstance(nodo, dict):
            continue
        if clave == "properties":
            for nombre, hijo in nodo.items():
                if _esquema_abierto(hijo):
                    problemas.append(
                        f"BR10.1 {prefijo}{sitio}.{nombre}: propiedad sin tipo, $ref, enum ni const"
                    )
            continue
        if clave == "$defs":
            problemas.extend(
                f"BR10.1 {prefijo}{sitio}.{nombre}: esquema abierto (acepta cualquier valor)"
                for nombre, hijo in nodo.items()
                if _esquema_abierto(hijo)
            )
            continue
        problemas.extend(_problemas_de_nodo(nodo, sitio, prefijo, en_reporte))
    return problemas


def _resolver(raiz: Any, nodo: Any) -> Any:
    """Resuelve una referencia local `#/$defs/<nombre>`; cualquier otro nodo se devuelve igual."""
    referencia = nodo.get("$ref") if isinstance(nodo, Mapping) else None
    if isinstance(referencia, str) and referencia.startswith("#/$defs/"):
        destino = _bajar(raiz, "$defs", referencia[len("#/$defs/") :])
        if isinstance(destino, Mapping):
            return destino
    return nodo


def _solo_enteros(raiz: Any, nodo: Any, sitio: str) -> list[str]:
    """Cada hoja de la sección es un entero; los objetos intermedios se recorren."""
    nodo = _resolver(raiz, nodo)
    tipo = nodo.get("type") if isinstance(nodo, Mapping) else None
    if tipo == "integer":
        return []
    if tipo != "object":
        return [f"BR10.1 {sitio}: clarifications solo admite enteros"]
    problemas: list[str] = []
    propiedades = nodo.get("properties")
    for nombre, hijo in propiedades.items() if isinstance(propiedades, Mapping) else ():
        problemas.extend(_solo_enteros(raiz, hijo, f"{sitio}.properties.{nombre}"))
    adicionales = nodo.get("additionalProperties")
    if isinstance(adicionales, Mapping):
        problemas.extend(_solo_enteros(raiz, adicionales, f"{sitio}.additionalProperties"))
    return problemas


def _problemas_de_clarifications(reporte: Any) -> list[str]:
    seccion = _bajar(reporte, "properties", "clarifications")
    if not isinstance(seccion, Mapping):
        return ["BR10.1: el reporte no declara la sección clarifications"]
    sitio = "$.properties.clarifications"
    obligatorios = _bajar(reporte, "required")
    if isinstance(obligatorios, list) and "clarifications" in obligatorios:
        return [f"BR10.1 {sitio}: la sección clarifications debe ser opcional"]
    if seccion.get("type") != "object":
        return [f"BR10.1 {sitio}: la sección clarifications debe ser un objeto"]
    return _solo_enteros(reporte, seccion, sitio)


def _restringe_el_papel(bloque: Any) -> bool:
    papeles = _bajar(bloque, "properties", "role", "enum")
    return (
        isinstance(papeles, list)
        and len(papeles) == len(PAPELES)
        and all(isinstance(p, str) for p in papeles)
        and set(papeles) == PAPELES
    )


def _problemas_de_llamadas(reporte: Any) -> list[str]:
    llamadas = _bajar(reporte, "properties", "runs", "items", "properties", "calls", "items")
    if not isinstance(llamadas, Mapping):
        return ["BR10.2: el reporte no declara runs[].calls[]"]
    todos = llamadas.get("allOf")
    bloques = todos if isinstance(todos, list) else []
    problemas: list[str] = []
    if not any(_restringe_el_papel(b) for b in bloques):
        problemas.append(
            f"BR10.2 {SITIO_DE_LLAMADAS}: las llamadas no restringen el papel a judge, verifier y "
            "verifier_permuted"
        )
    if not any(_bajar(b, "$ref") == REFERENCIA_A_LLAMADA for b in bloques):
        problemas.append(f"BR10.2 {SITIO_DE_LLAMADAS}: las llamadas no referencian model-call.v1")
    return problemas


def _problemas_de_fixtures(fixtures: Mapping[str, Any]) -> list[str]:
    problemas: list[str] = []
    for nombre, regla in FIXTURES_NEGATIVOS.items():
        if nombre not in fixtures:
            problemas.append(f"E28/E29: falta el fixture negativo {nombre}")
            continue
        fixture = fixtures[nombre]
        if not isinstance(fixture, Mapping) or not isinstance(fixture.get("payload"), Mapping):
            problemas.append(f"E28/E29: el fixture {nombre} no es un fixture con payload")
        elif fixture.get("expectation") != "reject" or fixture.get("reject_reason") != regla:
            problemas.append(f"E28/E29: {nombre} debe rechazarse con reject_reason {regla}")
    return problemas


def comprobar_documentos(reporte: Any, llamada: Any, fixtures: Mapping[str, Any]) -> list[str]:
    """Problemas de C19, de `model-call.v1` y de los *fixtures* negativos; vacío si todo está."""
    return [
        *_problemas_de_forma(reporte, "", True),
        *_problemas_de_forma(llamada, "model-call ", False),
        *_problemas_de_clarifications(reporte),
        *_problemas_de_llamadas(reporte),
        *_problemas_de_fixtures(fixtures),
    ]


def campos_que_admiten_una_palabra(documento: Any, palabra: str) -> list[str]:
    """Rutas de los campos con patrón que admiten `palabra`: el límite declarado de FD-U1-05."""
    sitios: list[str] = []
    for sitio, _, nodo in _recorrer(documento):
        if isinstance(nodo, dict) and isinstance(nodo.get("pattern"), str):
            try:
                coincide = re.search(nodo["pattern"], palabra) is not None
            except re.error:
                continue
            if coincide:
                sitios.append(sitio)
    return sitios


def _leer(ruta: Path, etiqueta: str) -> tuple[Any, list[str]]:
    try:
        documento = load_file(ruta)
    except (LoadError, OSError):
        return None, [f"{etiqueta} ilegible o ausente"]
    if not isinstance(documento, Mapping):
        return None, [f"{etiqueta} no es un objeto JSON"]
    return documento, []


def comprobar(raiz: Path) -> list[str]:
    """Lee C19, `model-call.v1` y los *fixtures* negativos bajo `raiz` (`contracts/`) y los comprueba."""
    reporte, problemas = _leer(raiz / C19, "C19")
    llamada, de_llamada = _leer(raiz / MODELO_DE_LLAMADA, "model-call.v1")
    problemas = [*problemas, *de_llamada]
    if problemas:
        return problemas
    fixtures: dict[str, Any] = {}
    for nombre in FIXTURES_NEGATIVOS:
        ruta = raiz / DIRECTORIO_DE_FIXTURES / nombre
        if ruta.is_file():
            try:
                fixtures[nombre] = load_file(ruta)
            except LoadError:
                fixtures[nombre] = "ilegible"
    return comprobar_documentos(reporte, llamada, fixtures)
