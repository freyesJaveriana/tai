"""Marcas de los contratos y catálogo C25, en los dos sentidos (§4.4 de NFR Design; NFR10.7, NFR10.14).

Módulo guardia (100 % de ramas). Recorre C1, C2, C5, C19 (con `model-call.v1.yaml`), C21 y la ruta
interna de voz, y comprueba contra `limits.v1.yaml`:

- (a) todo campo de texto libre de un cuerpo de C1 o de C21 (salvo que el `requestBody` declare
  `x-veridicus-max-bytes`, que lo acota) y de un mensaje de C2 o C5 lleva su `x-veridicus-limit`;
  la ruta interna de voz queda fuera de (a): su `tema` no necesita marca (K-15);
- (b) el valor del contrato (`maxLength`, `maxItems`) es igual al del catálogo;
- (c) la unidad es coherente con la palabra clave (`chars` con `maxLength`, `turns` con `maxItems`,
  `bytes` con `x-veridicus-max-bytes`, `s` con las cifras de la cookie);
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
    cargar,
    cuerpos,
    escapar,
    objeto,
    operaciones,
    resolver,
)

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
PALABRAS = (("maxLength", "chars"), ("maxItems", "turns"))
ACOTADO = ("enum", "const", "format", "pattern")
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
        for palabra, unidad in presentes:
            if entrada.get("unit") != unidad:
                yield _unidad(donde, marca.nombre, unidad, palabra)
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


def _textos_libres(raiz: Any, esquema: Any, puntero: str, vistos: set[int]) -> Iterator[str]:
    """Los campos de texto libre (sin enum, const, format ni pattern) sin `x-veridicus-limit`."""
    esquema = resolver(raiz, esquema)
    if not isinstance(esquema, dict) or id(esquema) in vistos:
        return
    vistos.add(id(esquema))
    es_libre = esquema.get("type") == "string" and not any(c in esquema for c in ACOTADO)
    if es_libre and "x-veridicus-limit" not in esquema:
        yield puntero
    for nombre, hija in objeto(esquema.get("properties")).items():
        yield from _textos_libres(raiz, hija, f"{puntero}/properties/{escapar(nombre)}", vistos)
    yield from _textos_libres(raiz, esquema.get("items"), f"{puntero}/items", vistos)


def _texto_de_cuerpos(archivo: str, documento: Any) -> Iterator[str]:
    for ruta, metodo, operacion in operaciones(documento):
        for medio, cuerpo, esquema in cuerpos(documento, operacion):
            if "x-veridicus-max-bytes" in cuerpo:
                continue  # el tope de bytes del cuerpo acota sus textos
            base = f"/paths/{escapar(ruta)}/{metodo}/requestBody/content/{escapar(medio)}/schema"
            for puntero in _textos_libres(documento, esquema, base, set()):
                yield f"{archivo}: {puntero}: campo de texto sin x-veridicus-limit ({REGLA} a)"


def _texto_de_mensajes(archivo: str, documento: Any) -> Iterator[str]:
    mensajes = objeto(objeto(objeto(documento).get("components")).get("messages"))
    for nombre, mensaje in mensajes.items():
        base = f"/components/messages/{escapar(nombre)}/payload"
        for puntero in _textos_libres(documento, objeto(mensaje).get("payload"), base, set()):
            yield f"{archivo}: {puntero}: campo de texto sin x-veridicus-limit ({REGLA} a)"


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
    for contrato, archivos in CONTRATOS.items():
        for archivo in archivos:
            documento = documentos[archivo]
            problemas.extend(_sin_marca(archivo, documento))
            for marca in _marcas(contrato, archivo, documento):
                marcadas.add((contrato, marca.nombre))
                problemas.extend(_de_marca(catalogo, marca))
            if contrato in CON_CUERPOS_DE_PETICION:
                problemas.extend(_texto_de_cuerpos(archivo, documento))
            if contrato in CON_MENSAJES:
                problemas.extend(_texto_de_mensajes(archivo, documento))
    problemas.extend(_inversa(catalogo, marcadas))
    return problemas


def comprobar(contracts_root: Path) -> list[str]:
    """Lee el catálogo y los contratos bajo `contracts_root` y los comprueba; uno ausente es un problema."""
    problemas: list[str] = []
    documentos: dict[str, Any] = {}
    for relativa in (CATALOGO, *ARCHIVOS):
        documentos[relativa], faltas = cargar(contracts_root, relativa, REGLA)
        problemas.extend(faltas)
    if problemas:
        return problemas
    return comprobar_documentos(objeto(documentos[CATALOGO]).get("limits", {}), documentos)
