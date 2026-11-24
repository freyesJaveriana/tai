"""Marcas de los contratos y catálogo C25, en los dos sentidos (§4.4 de NFR Design; NFR10.7, NFR10.14).

Módulo guardia (100 % de ramas). Recorre C1, C2, C5, C19 (con `model-call.v1.yaml`), C21 y la ruta
interna de voz, y comprueba contra `limits.v1.yaml`:

- (a) todo campo de texto libre de un cuerpo de C1 o de C21 (salvo que el `requestBody` declare
  `x-veridicus-max-bytes`, que lo acota) y de un mensaje de C2 o C5 lleva su `x-veridicus-limit`;
  se busca bajo todo subesquema (`_openapi.hijas`) y `type` puede ser una lista con `string`; un
  `$ref` por `$id` a otro contrato (C2 → C6) se sigue, y el texto que trae se acota con la marca de
  una rama hermana del mismo `allOf` en el mismo campo de la instancia (P-T15-6); el tope
  `x-veridicus-max-bytes` del `requestBody` o del `payload` acota los textos sin marca propia,
  salvo los de `MARCA_PROPIA_OBLIGATORIA` (E-14, E-18, P-T15-8);
  la ruta interna de voz queda fuera de (a): su `tema` no necesita marca (K-15);
- (b) el valor del contrato (`maxLength`, `maxItems`) es igual al del catálogo;
- (c) la unidad es coherente con la palabra clave (`chars` con `maxLength`, `turns` o `runs` con
  `maxItems`, `bytes` con `x-veridicus-max-bytes`, `s` con las cifras de la cookie);
- todo `maxLength` y `maxItems` lleva su marca, y toda marca de `x-veridicus-limit` acompaña a una
  de las dos palabras (K-16);
- comprobación inversa: toda entrada con `used_in: [Cn]` aparece marcada al menos una vez en `Cn`,
  y toda marca nombra una entrada que incluye su contrato en `used_in`. La ruta interna de voz no
  tiene un `C<n>` (NFRD-U1-08): sus marcas se contrastan en valor y unidad, no en `used_in`.

Los mensajes nombran el archivo, el puntero y la cifra, nunca el valor. Todas las funciones
devuelven la lista de problemas (vacía si todo está bien); nunca escriben.
"""

from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import Any, NamedTuple

from veridicus_contracts.checks._openapi import (
    DEFINICION,
    PROPIEDAD,
    VALOR,
    cargar,
    cuerpos,
    desescapar,
    es_tipo,
    escapar,
    hijas,
    objeto,
    operaciones,
    resolver,
)
from veridicus_contracts.checks.strict_bodies import ESQUEMAS_ESTRICTOS, ids_de

REGLA = "§4.4"
CATALOGO = "limits.v1.yaml"
VOZ = "voz"  # la ruta interna de voz no tiene un C<n> y no entra en used_in
# Contrato -> archivos donde viven sus marcas.
CONTRATOS: dict[str, tuple[str, ...]] = {
    "C1": ("api/console.v2.yaml",),
    "C2": ("queues/runs.v2.yaml",),
    "C5": ("queues/speech.v2.yaml",),
    "C19": ("cli/report.schema.v2.yaml", "model_calls/model-call.v1.yaml"),
    "C21": ("api/anonymizer-proxy.v1.yaml",),
    VOZ: ("api/speech-internal.v1.yaml",),
}
ARCHIVOS = tuple(archivo for archivos in CONTRATOS.values() for archivo in archivos)
CON_CUERPOS_DE_PETICION = ("C1", "C21")  # (a) en los cuerpos de petición
CON_MENSAJES = ("C2", "C5")  # (a) en los mensajes de cola
# Palabra clave -> unidades del catálogo con las que es coherente (§4.4 c). `runs` mide las corridas
# de un reporte (P-T15b-1).
PALABRAS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("maxLength", ("chars",)),
    ("maxItems", ("turns", "runs")),
)
ACOTADO = ("enum", "const", "format", "pattern")
# P-T15-8: el tope de bytes del `requestBody` o del `payload` acota los textos sin marca propia
# (E-14, E-18), salvo estos, que exigen su `x-veridicus-limit` aunque haya tope. Cada entrada es
# (archivo, operación o mensaje, ruta de la instancia) con su motivo. Añadir otra requiere una
# precisión del humano.
MARCA_PROPIA_OBLIGATORIA = {
    (CONTRATOS["C2"][0], "RunRequested", "entrada.transcripcion.turnos[].texto"): (
        "cada turno lleva su propio tope turn_max_chars, además del tope del mensaje (E-16, E-18)"
    ),
}
COOKIE = ("max_age_limit", "idle_limit")


class Marca(NamedTuple):
    """Una marca de límite en un contrato: dónde está, qué cifra nombra y el nodo que la lleva."""

    contrato: str
    archivo: str
    puntero: str
    nombre: str
    tipo: str  # "limit", "bytes" o "cookie"
    nodo: dict[str, Any]


def _marcas(contrato: str, archivo: str, nodo: Any, puntero: str = "") -> Iterator[Marca]:
    if isinstance(nodo, dict):
        for clave, valor in nodo.items():
            sitio = f"{puntero}/{escapar(clave)}"
            if clave == "x-veridicus-limit":
                yield Marca(contrato, archivo, puntero, str(valor), "limit", nodo)
            elif clave == "x-veridicus-max-bytes":
                yield Marca(contrato, archivo, puntero, str(valor), "bytes", nodo)
            elif clave == "x-veridicus-cookie":
                for campo in COOKIE:
                    if campo in objeto(valor):
                        yield Marca(contrato, archivo, sitio, str(valor[campo]), "cookie", valor)
            yield from _marcas(contrato, archivo, valor, sitio)
    elif isinstance(nodo, list):
        for indice, valor in enumerate(nodo):
            yield from _marcas(contrato, archivo, valor, f"{puntero}/{indice}")


def _sin_marca(archivo: str, nodo: Any, puntero: str = "") -> Iterator[str]:
    """Los `maxLength` y `maxItems` que no llevan `x-veridicus-limit` (K-16)."""
    if isinstance(nodo, dict):
        for palabra, _ in PALABRAS:
            if palabra in nodo and "x-veridicus-limit" not in nodo:
                yield f"{archivo}: {puntero}: {palabra} sin x-veridicus-limit ({REGLA})"
        for clave, valor in nodo.items():
            yield from _sin_marca(archivo, valor, f"{puntero}/{escapar(clave)}")
    elif isinstance(nodo, list):
        for indice, valor in enumerate(nodo):
            yield from _sin_marca(archivo, valor, f"{puntero}/{indice}")


def _de_marca(catalogo: Mapping[str, Any], marca: Marca) -> Iterator[str]:
    donde = f"{marca.archivo}: {marca.puntero}"
    entrada = objeto(catalogo.get(marca.nombre))
    if not entrada:
        yield f"{donde}: la marca {marca.nombre} no es una cifra de C25 ({REGLA})"
        return
    if marca.contrato != VOZ and marca.contrato not in entrada.get("used_in", []):
        yield (
            f"{donde}: la marca {marca.nombre} no está en used_in de C25 para {marca.contrato} "
            f"({REGLA}, comprobación inversa)"
        )
    if marca.tipo == "limit":
        presentes = [(p, u) for p, u in PALABRAS if p in marca.nodo]
        if not presentes:
            yield (
                f"{donde}: la marca {marca.nombre} no acompaña a maxLength ni a maxItems ({REGLA})"
            )
        for palabra, unidades in presentes:
            if entrada.get("unit") not in unidades:
                yield _unidad(donde, marca.nombre, " o ".join(unidades), palabra)
            if marca.nodo[palabra] != entrada.get("value"):
                yield f"{donde}: valor distinto del catálogo C25 ({marca.nombre}, {REGLA} b)"
    else:
        unidad, palabra = ("bytes", "x-veridicus-max-bytes") if marca.tipo == "bytes" else (
            "s",
            "x-veridicus-cookie",
        )
        if entrada.get("unit") != unidad:
            yield _unidad(donde, marca.nombre, unidad, palabra)


def _unidad(donde: str, nombre: str, unidad: str, palabra: str) -> str:
    return f"{donde}: la unidad de {nombre} debe ser {unidad} con {palabra} ({REGLA} c)"


Ruta = tuple[str, ...]


def _paso(puntero: str, sitio: str, papel: str) -> Ruta:
    """El segmento que una hija añade a la ruta de la instancia: su propiedad, `items`, etc.

    Una rama que refina o alterna (`allOf`, `if`, `oneOf`...) mira la misma instancia y no añade nada.
    """
    resto = sitio[len(puntero) + 1 :]
    if papel == PROPIEDAD:
        return (desescapar(resto.removeprefix("properties/")),)
    if papel == VALOR:
        return (resto,)
    return ()


def _nodos(
    raiz: Any, esquema: Any, puntero: str, ruta: Ruta, vistos: set[int], externos: Mapping[str, Any]
) -> Iterator[tuple[dict[str, Any], str, Ruta]]:
    """Cada subesquema alcanzable con su puntero y su ruta de instancia, una vez por esquema.

    Una `$ref` local se resuelve en `raiz`; una `$ref` por `$id` a otro contrato (`externos`, por
    `ids_de`) se sigue y sus `$ref` locales se resuelven en ese documento (P-T15-6).
    """
    esquema = resolver(raiz, esquema)
    referencia = objeto(esquema).get("$ref")
    if isinstance(referencia, str) and referencia.lstrip("/") in externos:
        raiz = esquema = externos[referencia.lstrip("/")]
    if not isinstance(esquema, dict) or id(esquema) in vistos:
        return
    vistos.add(id(esquema))
    yield esquema, puntero, ruta
    for hija, sitio, papel in hijas(esquema, puntero):
        if papel != DEFINICION:  # los `$defs` se alcanzan por su `$ref`
            paso = _paso(puntero, sitio, papel)
            yield from _nodos(raiz, hija, sitio, (*ruta, *paso), vistos, externos)


def _ruta_en_texto(ruta: Ruta) -> str:
    """La ruta de la instancia como se escribe en `MARCA_PROPIA_OBLIGATORIA`: `a.b[].c`."""
    texto = ""
    for paso in ruta:
        texto += "[]" if paso == "items" else (f".{paso}" if texto else paso)
    return texto


def _textos_libres(
    raiz: Any, esquema: Any, puntero: str, externos: Mapping[str, Any]
) -> Iterator[tuple[str, str]]:
    """Los campos de texto libre (sin enum, const, format ni pattern) sin `x-veridicus-limit`.

    Devuelve el puntero y la ruta de la instancia (`_ruta_en_texto`) de cada uno. Un texto cuenta
    como acotado si el mismo campo de la instancia lleva la marca en otra rama del mismo esquema,
    como la rama de refinamiento de un `allOf` que acompaña al `$ref` de otro contrato (E-16,
    P-T15-6).
    """
    nodos = list(_nodos(raiz, esquema, puntero, (), set(), externos))
    marcadas = {ruta for nodo, _, ruta in nodos if "x-veridicus-limit" in nodo}
    for nodo, sitio, ruta in nodos:
        es_libre = es_tipo(nodo, "string") and not any(c in nodo for c in ACOTADO)
        if es_libre and ruta not in marcadas:
            yield sitio, _ruta_en_texto(ruta)


def _textos_sin_marca(
    archivo: str,
    donde: str,
    documento: Any,
    acota: Any,
    esquema: Any,
    base: str,
    externos: Mapping[str, Any],
) -> Iterator[str]:
    """Los textos de un cuerpo (C1, C21) o de un mensaje (C2, C5) sin marca propia ni tope de bytes.

    `acota` es el objeto que puede declarar `x-veridicus-max-bytes`: el `requestBody` de una
    petición o el `payload` de un mensaje (E-14, E-18). Con el tope, ese tope acota los textos sin
    marca propia, salvo los de `MARCA_PROPIA_OBLIGATORIA` en `donde` (la operación o el mensaje).
    """
    con_tope = "x-veridicus-max-bytes" in objeto(acota)
    propias = {r for a, d, r in MARCA_PROPIA_OBLIGATORIA if (a, d) == (archivo, donde)}
    for puntero, ruta in _textos_libres(documento, esquema, base, externos):
        if not con_tope or ruta in propias:
            yield f"{archivo}: {puntero}: campo de texto sin x-veridicus-limit ({REGLA} a)"


def _texto_de_cuerpos(
    archivo: str, documento: Any, externos: Mapping[str, Any]
) -> Iterator[str]:
    for ruta, metodo, operacion in operaciones(documento):
        for medio, cuerpo, esquema in cuerpos(documento, operacion):
            base = f"/paths/{escapar(ruta)}/{metodo}/requestBody/content/{escapar(medio)}/schema"
            donde = f"{metodo.upper()} {ruta}"
            yield from _textos_sin_marca(archivo, donde, documento, cuerpo, esquema, base, externos)


def _texto_de_mensajes(
    archivo: str, documento: Any, externos: Mapping[str, Any]
) -> Iterator[str]:
    mensajes = objeto(objeto(objeto(documento).get("components")).get("messages"))
    for nombre, mensaje in mensajes.items():
        base = f"/components/messages/{escapar(nombre)}/payload"
        carga = objeto(mensaje).get("payload")
        yield from _textos_sin_marca(archivo, nombre, documento, carga, carga, base, externos)


def _inversa(catalogo: Mapping[str, Any], marcadas: set[tuple[str, str]]) -> Iterator[str]:
    for nombre, entrada in catalogo.items():
        for contrato in objeto(entrada).get("used_in", []):
            if contrato not in CONTRATOS:
                yield f"{nombre}: used_in nombra {contrato}, que la guardia no recorre ({REGLA})"
            elif (contrato, nombre) not in marcadas:
                yield (
                    f"{nombre}: used_in nombra {contrato} y {contrato} no la marca "
                    f"({REGLA}, comprobación inversa)"
                )


def comprobar_documentos(catalogo: Mapping[str, Any], documentos: Mapping[str, Any]) -> list[str]:
    """Las comprobaciones sobre las cifras de C25 y los contratos ya cargados (por archivo)."""
    problemas: list[str] = []
    marcadas: set[tuple[str, str]] = set()
    # Los contratos que un mensaje o cuerpo referencia por `$id` (C2 trae `entrada` de C6).
    externos = ids_de(documentos.values())
    for contrato, archivos in CONTRATOS.items():
        for archivo in archivos:
            documento = documentos[archivo]
            problemas.extend(_sin_marca(archivo, documento))
            for marca in _marcas(contrato, archivo, documento):
                marcadas.add((contrato, marca.nombre))
                problemas.extend(_de_marca(catalogo, marca))
            if contrato in CON_CUERPOS_DE_PETICION:
                problemas.extend(_texto_de_cuerpos(archivo, documento, externos))
            if contrato in CON_MENSAJES:
                problemas.extend(_texto_de_mensajes(archivo, documento, externos))
    problemas.extend(_inversa(catalogo, marcadas))
    return problemas


def comprobar(contracts_root: Path) -> list[str]:
    """Lee el catálogo y los contratos bajo `contracts_root` y los comprueba; uno ausente es un problema.

    Además de los contratos con marcas, lee los esquemas estrictos (C6 entre ellos) para seguir los
    `$ref` por `$id` de los mensajes (P-T15-6).
    """
    problemas: list[str] = []
    documentos: dict[str, Any] = {}
    for relativa in (CATALOGO, *ARCHIVOS):
        documentos[relativa], faltas = cargar(contracts_root, relativa, REGLA)
        problemas.extend(faltas)
    if problemas:
        return problemas
    for relativa in ESQUEMAS_ESTRICTOS:
        if relativa not in documentos:
            documentos[relativa], faltas = cargar(contracts_root, relativa, REGLA)
            problemas.extend(faltas)
    if problemas:
        return problemas
    return comprobar_documentos(objeto(documentos[CATALOGO]).get("limits", {}), documentos)
