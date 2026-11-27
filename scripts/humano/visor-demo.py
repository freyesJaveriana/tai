# Lo ejecuta el humano (AUTONOMIA-01)
"""Visor web de la demo del analizador: envía un caso sintético al Job de Minikube y muestra el resultado.

Lo lanza el humano en la VM de la demo, desde la raíz del repositorio y con su propio kubeconfig:

    python3 scripts/humano/visor-demo.py            # escucha en http://127.0.0.1:8501
    python3 scripts/humano/visor-demo.py --host 0.0.0.0 --port 8501
    python3 scripts/humano/visor-demo.py --logo ~/escudo.png   # escudo institucional, no versionado

Desde la anfitriona se abre con un túnel: ssh -L 8501:127.0.0.1:8501 <usuario>@<vm>
y luego http://127.0.0.1:8501 en el navegador.

Cada envío copia deploy/demo-analyzer a una carpeta temporal, cambia las dos entradas sintéticas por el
caso escrito en el formulario (entrada/caso.json), borra el Job anterior, aplica la copia con kubectl,
espera a que el Job termine y muestra sus logs. El análisis sigue dentro del Job: el anonimizador va en
el proceso de la CLI y la clave la monta el Secret que ya existe (AUTONOMIA-04). Este visor no lee la
clave ni llama a ningún proveedor.

Solo para la demo y solo con casos sintéticos: el anonimizador de B10a seudonimiza con reglas y listas y
no detecta nombres que no conozca. No es la consola del producto.

Solo usa la biblioteca estándar de Python.
"""

import argparse
import base64
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

NAMESPACE = "veridicus-demo"
JOB = "veridicus-analyzer-demo"
RAIZ = Path(__file__).resolve().parents[2]
BASE = RAIZ / "deploy" / "demo-analyzer"
EJEMPLOS = RAIZ / "deploy" / "demo-visor" / "ejemplos.json"
ENTRADAS_BASE = "      - entrada/coherente.json\n      - entrada/contradiccion.json\n"
ENTRADA_CASO = "      - entrada/caso.json\n"
PLAZO_S = 900
MAX_CARACTERES = 60_000

_ocupado = threading.Lock()

UNIVERSIDAD = "Pontificia Universidad Javeriana"
ASIGNATURA = "Tópicos Avanzados de Informática"
PROFESOR = "Luis Felipe Ariza"
AUTOR = "Felipe Reyes Palacio"
CORREO = "freyes@javeriana.edu.co"
# Colores aproximados de la identidad javeriana (azul institucional y acento dorado).
AZUL = "#2c5697"
AZUL_OSCURO = "#1b3a6b"
DORADO = "#f2b705"
# Color de la barra superior: llega del ConfigMap veridicus-visor-apariencia (deploy/demo-visor/
# apariencia.properties). Es el cambio visible de la demo del bucle GitOps (scripts/humano/gitops-color.sh).
VARIABLE_COLOR_BANDA = "VERIDICUS_VISOR_COLOR_BANDA"


def color_banda(valor: str | None) -> str:
    """Un color #rrggbb; cualquier otro valor deja el azul de siempre, para que nada entre al CSS."""
    if valor is not None and re.fullmatch(r"#[0-9A-Fa-f]{6}", valor.strip()):
        return valor.strip().lower()
    return AZUL


COLOR_BANDA = color_banda(os.environ.get(VARIABLE_COLOR_BANDA))

# Escudo opcional (--logo): se incrusta como data URI; el archivo nunca entra al repositorio.
_logo: dict[str, str] = {"uri": ""}

AVISO_PROPOSITO = (
    "Los hallazgos son sugerencias de revisión sobre la coherencia interna del relato, "
    "para que una persona las lea junto con la transcripción. La decisión es siempre humana."
)


class ErrorCaso(Exception):
    """El caso escrito en el formulario no se puede convertir en una entrada C6."""


# ------------------------------------------------------------------ caso: texto ⇄ entrada C6


def relato_a_turnos(relato: str) -> list[dict[str, object]]:
    """Convierte líneas «ENT: …» / «TEST: …» en turnos C6. Una línea sin prefijo continúa el turno."""
    turnos: list[dict[str, object]] = []
    for crudo in relato.splitlines():
        linea = crudo.strip()
        if not linea:
            continue
        coincide = re.match(r"^(ENT|TEST)\s*:\s*(.*)$", linea, flags=re.IGNORECASE)
        if coincide:
            texto = coincide.group(2).strip()
            if not texto:
                raise ErrorCaso(f"El turno {len(turnos) + 1} no tiene texto.")
            turnos.append(
                {"n": len(turnos) + 1, "hablante": coincide.group(1).upper(), "texto": texto}
            )
        elif turnos:
            turnos[-1]["texto"] = f"{turnos[-1]['texto']} {linea}"
        else:
            raise ErrorCaso("La primera línea debe empezar por «ENT:» o «TEST:».")
    if not any(turno["hablante"] == "TEST" for turno in turnos):
        raise ErrorCaso("El caso necesita al menos un turno «TEST:» (el relato que se analiza).")
    return turnos


def turnos_a_relato(turnos: list[dict[str, object]]) -> str:
    return "\n".join(f"{turno['hablante']}: {turno['texto']}" for turno in turnos)


def caso_c6(entrevista: str, relato: str) -> dict[str, object]:
    entrevista = entrevista.strip()
    if not re.fullmatch(r"SINT-[A-Za-z0-9-]{1,40}", entrevista):
        raise ErrorCaso(
            "El identificador debe empezar por «SINT-» y usar solo letras, cifras y guiones."
        )
    if len(relato) > MAX_CARACTERES:
        raise ErrorCaso(f"El relato pasa de {MAX_CARACTERES} caracteres.")
    return {"entrevista": entrevista, "origen": "sintetico", "turnos": relato_a_turnos(relato)}


def ejemplos() -> list[dict[str, str]]:
    """Las dos entradas del Job (contradicción y coherente) y los casos de deploy/demo-visor/ejemplos.json."""
    lista: list[dict[str, str]] = []
    for clave, titulo, archivo in (
        ("crecida", "La crecida del río: ¿en la finca o en el pueblo?", "contradiccion.json"),
        ("crecida-coherente", "La crecida del río, versión coherente", "coherente.json"),
    ):
        try:
            documento = json.loads((BASE / "entrada" / archivo).read_text(encoding="utf-8"))
            relato = turnos_a_relato(documento["turnos"])
        except (OSError, ValueError, KeyError):
            continue
        lista.append(
            {"id": clave, "titulo": titulo, "entrevista": documento["entrevista"], "relato": relato}
        )
    try:
        lista += json.loads(EJEMPLOS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    return lista


def ejemplo(clave: str) -> tuple[str, str] | None:
    for item in ejemplos():
        if item["id"] == clave:
            return item["entrevista"], item["relato"]
    return None


# ------------------------------------------------------------------ Kubernetes (lo lanza el humano)


def _kubectl(*argumentos: str, plazo: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603 - argumentos fijos, sin shell
        ["kubectl", *argumentos],  # noqa: S607 - el kubectl del PATH del humano, como en sus scripts
        capture_output=True,
        text=True,
        timeout=plazo,
        check=False,
    )


def _estado_job() -> str:
    hecho = _kubectl(
        "get",
        "job",
        JOB,
        "--namespace",
        NAMESPACE,
        "-o",
        "jsonpath={.status.succeeded},{.status.failed}",
    )
    if hecho.returncode != 0:
        return "esperando"
    exito, _, fallo = hecho.stdout.partition(",")
    if exito.strip() not in ("", "0"):
        return "completo"
    if fallo.strip() not in ("", "0"):
        return "fallido"
    return "esperando"


def analizar(caso: dict[str, object]) -> tuple[str, str, float]:
    """Corre el Job con el caso y devuelve (estado, logs, segundos)."""
    for secreto in ("veridicus-anthropic", "veridicus-ghcr"):
        if _kubectl("get", "secret", secreto, "--namespace", NAMESPACE).returncode != 0:
            raise RuntimeError(
                f"Falta el Secret {secreto}: créelo con los scripts de scripts/humano/."
            )
    inicio = time.monotonic()
    temporal = Path(tempfile.mkdtemp(prefix="veridicus-visor-"))
    try:
        copia = temporal / "demo-analyzer"
        shutil.copytree(BASE, copia)
        for viejo in (copia / "entrada").glob("*.json"):
            viejo.unlink()
        (copia / "entrada" / "caso.json").write_text(
            json.dumps(caso, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        kustomization = (copia / "kustomization.yaml").read_text(encoding="utf-8")
        if ENTRADAS_BASE not in kustomization:
            raise RuntimeError(
                "kustomization.yaml cambió: el visor no encuentra la lista de entradas."
            )
        (copia / "kustomization.yaml").write_text(
            kustomization.replace(ENTRADAS_BASE, ENTRADA_CASO), encoding="utf-8"
        )
        borrar = _kubectl(
            "delete", "job", JOB, "--namespace", NAMESPACE, "--ignore-not-found", "--wait=true"
        )
        if borrar.returncode != 0:
            raise RuntimeError(f"No se pudo borrar el Job anterior: {borrar.stderr.strip()}")
        aplicar = _kubectl("apply", "-k", str(copia))
        if aplicar.returncode != 0:
            raise RuntimeError(f"kubectl apply falló: {aplicar.stderr.strip()}")
    finally:
        shutil.rmtree(temporal, ignore_errors=True)
    estado = "esperando"
    while estado == "esperando" and time.monotonic() - inicio < PLAZO_S:
        time.sleep(3)
        estado = _estado_job()
    if estado == "esperando":
        estado = "plazo vencido"
    logs = _kubectl("logs", f"job/{JOB}", "--namespace", NAMESPACE)
    texto = logs.stdout if logs.returncode == 0 else logs.stderr
    return estado, texto, time.monotonic() - inicio


# ------------------------------------------------------------------ logs → hallazgos

# Explicación de cada `error.codigo` de C6, para una demo académica.
MOTIVOS = {
    "salida_invalida": (
        "El modelo respondió algo que no cumple el esquema JSON del contrato (por ejemplo, un campo "
        "faltante o un JSON mal formado). El analizador no repara ni rescata respuestas a medias."
    ),
    "bloqueo_contenido": "El proveedor bloqueó la respuesta con sus filtros de contenido.",
    "tiempo_agotado": "La llamada al modelo superó el plazo configurado en el perfil.",
    "proveedor": (
        "El proveedor devolvió un error (clave, cuota, saturación o red). Revise la clave del "
        "Secret y el saldo de la cuenta."
    ),
    "anonimizador_no_disponible": (
        "El anonimizador no estaba disponible, así que no salió ninguna llamada al proveedor."
    ),
    "incidente_anonimizacion": (
        "El anonimizador detectó un problema al seudonimizar o al restaurar, y el análisis se "
        "detuvo antes de mostrar nada."
    ),
    "otro": "Motivo no reconocido por el visor.",
}

_CABECERA = re.compile(r"^(\S+): estado=(ok|error), (\d+) hallazgos?$")
_CITA = re.compile(r"^  cita ([AB]) \(turno (\S+)\): «(.*)»$")


def leer_logs(logs: str) -> dict[str, object]:
    avisos: list[str] = []
    errores: list[str] = []
    bloques: list[dict[str, object]] = []
    actual: dict[str, object] | None = None
    hallazgo: dict[str, object] | None = None
    for linea in logs.splitlines():
        if cabecera := _CABECERA.match(linea):
            actual = {
                "nombre": cabecera.group(1),
                "estado": cabecera.group(2),
                "hallazgos": [],
                "motivo": "",
                "registro": [],
            }
            bloques.append(actual)
            hallazgo = None
        elif linea.startswith("  motivo: ") and actual is not None:
            actual["motivo"] = linea[len("  motivo: ") :].strip()
        elif linea.startswith(("  llamadas: ", "  tokens: ", "  descartes: ")) and actual:
            actual["registro"].append(linea.strip())  # type: ignore[union-attr]
        elif linea.startswith("  hecho: ") and actual is not None:
            hallazgo = {"hecho": linea[len("  hecho: ") :]}
            actual["hallazgos"].append(hallazgo)  # type: ignore[union-attr]
        elif linea.startswith("  tipo: ") and hallazgo is not None:
            hallazgo["tipo"] = linea[len("  tipo: ") :]
        elif (cita := _CITA.match(linea)) and hallazgo is not None:
            hallazgo[f"cita_{cita.group(1).lower()}"] = {
                "turno": cita.group(2),
                "cita": cita.group(3),
            }
        elif linea.startswith(("El análisis terminó", "Falta un archivo", "Error inesperado")):
            errores.append(linea)
        elif linea.strip() and not linea.startswith("  "):
            # Avisos de la CLI (propósito limitado, misma familia): se muestran tal cual.
            avisos.append(linea.strip())
    return {"avisos": avisos, "errores": errores, "bloques": bloques}


# ------------------------------------------------------------------ HTML

_ESTILO = f"""
body{{font-family:system-ui,sans-serif;margin:0;color:#1f2328;background:#f4f6fa}}
main{{max-width:1100px;margin:0 auto;padding:1rem 1rem 2rem;background:#fff;min-height:70vh}}
.banda{{background:{COLOR_BANDA};color:#fff;border-bottom:5px solid {DORADO}}}
.banda .dentro{{max-width:1100px;margin:0 auto;padding:.8rem 1rem;display:flex;align-items:center;gap:1rem}}
.banda img{{height:56px;background:#fff;border-radius:4px;padding:4px}}
.banda .u{{font-size:1.15rem;font-weight:700;letter-spacing:.02em}}
.banda .a{{font-size:.9rem;opacity:.92}}
footer{{background:{AZUL_OSCURO};color:#e8edf6;font-size:.85rem}}
footer .dentro{{max-width:1100px;margin:0 auto;padding:.9rem 1rem}}
footer a{{color:#fff}}
h1{{font-size:1.4rem;margin-bottom:.2rem;color:{AZUL_OSCURO}}} h2{{font-size:1.1rem;margin-top:1.5rem;color:{AZUL_OSCURO}}}
button{{background:{AZUL};color:#fff;border:0;border-radius:4px}}
button:hover{{background:{AZUL_OSCURO}}} button:disabled{{opacity:.5;cursor:wait}}
.cargando{{position:fixed;inset:0;background:rgba(255,255,255,.88);display:flex;flex-direction:column;
align-items:center;justify-content:center;z-index:10;font-size:1.6rem;color:{AZUL_OSCURO};cursor:wait}}
.cargando[hidden]{{display:none}}
.cargando small{{font-size:.95rem;margin-top:.6rem}}
.giro{{width:56px;height:56px;border:6px solid #d6deea;border-top-color:{AZUL};border-radius:50%;
animation:giro 1s linear infinite;margin-bottom:1rem}}
@keyframes giro{{to{{transform:rotate(360deg)}}}}"""
_ESTILO += """
.aviso{background:#fff8e1;border-left:4px solid #b58100;padding:.6rem .8rem;margin:.6rem 0;font-size:.92rem}
.error{background:#fdecea;border-left:4px solid #b3261e;padding:.6rem .8rem;margin:.6rem 0}
textarea{width:100%;min-height:22rem;font-family:ui-monospace,monospace;font-size:.9rem}
input[type=text]{width:16rem} button{font-size:1rem;padding:.45rem 1rem;cursor:pointer}
.rejilla{display:grid;grid-template-columns:3fr 2fr;gap:1.2rem;align-items:start}
.turno{padding:.35rem .6rem;margin:.25rem 0;border-radius:4px;background:#f6f8fa}
.turno .quien{font-weight:600;font-size:.8rem;color:#57606a;margin-right:.4rem}
.ent{color:#57606a}
mark.a{background:#dbeafe;border-bottom:3px solid #1d4ed8;padding:0 .1rem}
mark.b{background:#ffedd5;border-bottom:3px dashed #c2410c;padding:0 .1rem}
.tarjeta{border:1px solid #d0d7de;border-radius:6px;padding:.7rem .9rem;margin-bottom:.8rem}
.tarjeta h3{font-size:.95rem;margin:0 0 .4rem}
.cita{margin:.35rem 0;padding-left:.6rem;font-size:.92rem}
.cita.a{border-left:4px solid #1d4ed8} .cita.b{border-left:4px dashed #c2410c}
.letra{font-weight:700;margin-right:.3rem}
select{font-size:1rem;padding:.4rem;max-width:100%;min-width:26rem}
.ejemplos{background:#eef2f8;border-radius:6px;padding:.2rem .9rem .8rem;margin-top:1rem}
small{color:#57606a} pre{white-space:pre-wrap;font-size:.8rem;background:#f6f8fa;padding:.6rem}
"""


# Al enviar «Analizar»: muestra el aviso a pantalla completa, bloquea los botones y cuenta segundos.
# Los campos quedan de solo lectura (no deshabilitados) para que el formulario siga enviándolos.
_GUION = """
document.addEventListener('submit', function (e) {
  if (e.target.id !== 'analizar') return;
  var capa = document.getElementById('cargando'), t0 = Date.now();
  capa.hidden = false;
  document.querySelectorAll('button').forEach(function (b) { b.disabled = true; });
  document.querySelectorAll('textarea, input[type=text]').forEach(function (c) { c.readOnly = true; });
  setInterval(function () {
    document.getElementById('segundos').textContent = Math.round((Date.now() - t0) / 1000);
  }, 1000);
});
window.addEventListener('pageshow', function () {
  var capa = document.getElementById('cargando');
  if (capa) capa.hidden = true;
  document.querySelectorAll('button').forEach(function (b) { b.disabled = false; });
});
"""
_HASH_GUION = base64.b64encode(hashlib.sha256(_GUION.encode()).digest()).decode()
CSP = (
    "default-src 'none'; style-src 'unsafe-inline'; img-src data:; form-action 'self'; "
    f"script-src 'sha256-{_HASH_GUION}'"
)


def _banda() -> str:
    escudo = f"<img src='{html.escape(_logo['uri'])}' alt='{UNIVERSIDAD}'>" if _logo["uri"] else ""
    return (
        f"<header class='banda'><div class='dentro'>{escudo}<div>"
        f"<div class='u'>{UNIVERSIDAD}</div>"
        f"<div class='a'>{html.escape(ASIGNATURA)} · Prof. {PROFESOR}</div>"
        "</div></div></header>"
    )


def _pie() -> str:
    return (
        "<footer><div class='dentro'>"
        f"Por: {AUTOR} · <a href='mailto:{CORREO}'>{CORREO}</a> · "
        f"para la asignatura «{html.escape(ASIGNATURA)}» del profesor {PROFESOR}. "
        f"{UNIVERSIDAD}."
        "</div></footer>"
    )


def _pagina(cuerpo: str) -> bytes:
    return (
        "<!doctype html><html lang='es'><head><meta charset='utf-8'>"
        "<title>Veridicus · demo del analizador</title>"
        f"<style>{_ESTILO}</style></head><body>{_banda()}<main>"
        "<h1>Veridicus · demo del analizador de incoherencias</h1>"
        "<small>Herramienta de demostración. Solo casos sintéticos.</small>"
        f"<div class='aviso'><strong>Aviso de propósito limitado.</strong> {html.escape(AVISO_PROPOSITO)}</div>"
        f"{cuerpo}</main>{_pie()}"
        "<div id='cargando' class='cargando' hidden><div class='giro'></div>Analizando…"
        "<small><span id='segundos'>0</span> s · suele tardar alrededor de un minuto</small></div>"
        f"<script>{_GUION}</script></body></html>"
    ).encode()


def _selector(actual: str) -> str:
    opciones = ["<option value=''>— Caso en blanco —</option>"]
    for item in ejemplos():
        marcado = " selected" if item["id"] == actual else ""
        opciones.append(
            f"<option value='{html.escape(item['id'])}'{marcado}>{html.escape(item['titulo'])}</option>"
        )
    return (
        "<form class='ejemplos' method='get' action='/'><h2>1. Elija un ejemplo (opcional)</h2>"
        f"<select name='ejemplo'>{''.join(opciones)}</select> <button type='submit'>Cargar</button>"
        "<small> Casos sintéticos, algunos inspirados en libros y películas.</small></form>"
    )


def pagina_formulario(entrevista: str, relato: str, error: str = "", actual: str = "") -> bytes:
    aviso_error = f"<div class='error'>{html.escape(error)}</div>" if error else ""
    return _pagina(
        f"""{aviso_error}{_selector(actual)}
<form id='analizar' method='post' action='/analizar'>
<h2>2. Escriba o ajuste el caso</h2>
<p>Un turno por línea, empezando por <code>ENT:</code> (entrevistador) o <code>TEST:</code> (relato que se
analiza). Una línea sin prefijo continúa el turno anterior. Los turnos se numeran T1, T2, … en orden.</p>
<p><label>Identificador del caso: <input type='text' name='entrevista' value='{html.escape(entrevista)}'></label>
<small>debe empezar por SINT-</small></p>
<textarea name='relato'>{html.escape(relato)}</textarea>
<div class='aviso'>El anonimizador de esta versión seudonimiza con reglas y listas y no reconoce cualquier
nombre. <strong>No escriba datos reales</strong>: el texto se envía, seudonimizado, a un proveedor externo.</div>
<p><label><input type='checkbox' name='sintetico' value='si' required> Confirmo que el caso es sintético.</label></p>
<p><button type='submit'>Analizar</button> <small>Tarda alrededor de un minuto; no cierre la página.</small></p>
</form>"""
    )


def _resaltar(texto: str, marcas: list[tuple[str, str, int]]) -> str:
    """Envuelve en <mark> cada fragmento citado que aparece literal en el texto del turno."""
    tramos: list[tuple[int, int, str, int]] = []
    for cita, letra, numero in marcas:
        for fragmento in (parte.strip() for parte in cita.split("[…]")):
            if not fragmento:
                continue
            posicion = texto.find(fragmento)
            if posicion >= 0:
                tramos.append((posicion, posicion + len(fragmento), letra, numero))
    tramos.sort()
    salida, cursor = [], 0
    for inicio, fin, letra, numero in tramos:
        if inicio < cursor:
            continue
        salida.append(html.escape(texto[cursor:inicio]))
        salida.append(
            f"<mark class='{letra}' title='Hallazgo {numero}, cita {letra.upper()}'>"
            f"{html.escape(texto[inicio:fin])}</mark>"
        )
        cursor = fin
    salida.append(html.escape(texto[cursor:]))
    return "".join(salida)


def pagina_resultado(caso: dict[str, object], estado: str, logs: str, segundos: float) -> bytes:
    leido = leer_logs(logs)
    partes = [f"<p><strong>Estado del Job:</strong> {html.escape(estado)} · {segundos:.0f} s</p>"]
    partes += [f"<div class='aviso'>{html.escape(aviso)}</div>" for aviso in leido["avisos"]]
    partes += [f"<div class='error'>{html.escape(error)}</div>" for error in leido["errores"]]
    bloque = next((b for b in leido["bloques"] if b["nombre"] == "caso"), None)
    hallazgos: list[dict[str, object]] = list(bloque["hallazgos"]) if bloque else []
    if bloque is None and not leido["errores"]:
        partes.append(
            "<div class='error'>No se encontró el resultado del caso en los logs (ver abajo).</div>"
        )
    elif bloque is not None and bloque["estado"] == "error":
        motivo = str(bloque.get("motivo") or "")
        if motivo:
            explicacion = MOTIVOS.get(motivo, MOTIVOS["otro"])
            detalle = f" Motivo: <code>{html.escape(motivo)}</code>. {html.escape(explicacion)}"
        else:
            detalle = " Esta versión de la imagen no informa el motivo."
        partes.append(
            "<div class='error'>El análisis terminó en estado «error»: por diseño no se muestra "
            f"ningún resultado parcial (AUTONOMIA-05).{detalle}</div>"
        )
    if bloque is not None and bloque.get("registro"):
        lineas = "".join(f"<li>{html.escape(str(r))}</li>" for r in bloque["registro"])  # type: ignore[attr-defined]
        partes.append(
            f"<details><summary>Detalle técnico de la corrida</summary><ul>{lineas}</ul></details>"
        )

    marcas: dict[str, list[tuple[str, str, int]]] = {}
    for numero, item in enumerate(hallazgos, start=1):
        for letra in ("a", "b"):
            cita = item.get(f"cita_{letra}")
            if isinstance(cita, dict):
                marcas.setdefault(cita["turno"], []).append((cita["cita"], letra, numero))

    turnos_html = []
    for turno in caso["turnos"]:  # type: ignore[union-attr]
        clave = f"T{turno['n']}"
        clase = "ent" if turno["hablante"] == "ENT" else ""
        turnos_html.append(
            f"<div class='turno {clase}' id='{clave}'><span class='quien'>{clave} · {turno['hablante']}</span>"
            f"{_resaltar(str(turno['texto']), marcas.get(clave, []))}</div>"
        )

    tarjetas = []
    for numero, item in enumerate(hallazgos, start=1):
        citas = []
        for letra in ("a", "b"):
            cita = item.get(f"cita_{letra}")
            if isinstance(cita, dict):
                citas.append(
                    f"<div class='cita {letra}'><span class='letra'>{letra.upper()}</span>"
                    f"<a href='#{html.escape(cita['turno'])}'>{html.escape(cita['turno'])}</a> "
                    f"«{html.escape(cita['cita'])}»</div>"
                )
        tarjetas.append(
            f"<div class='tarjeta'><h3>Sugerencia de revisión {numero}</h3>"
            f"<div><strong>Hecho:</strong> {html.escape(str(item.get('hecho', '')))}</div>"
            f"<div><strong>Tipo:</strong> {html.escape(str(item.get('tipo', '')))}</div>{''.join(citas)}</div>"
        )
    if bloque is not None and bloque["estado"] == "ok" and not hallazgos:
        tarjetas.append(
            "<div class='tarjeta'>El analizador no propuso sugerencias de revisión para este relato.</div>"
        )

    partes.append(
        f"<h2>Resultado · {html.escape(str(caso['entrevista']))} · {len(hallazgos)} sugerencias de revisión</h2>"
        f"<div class='rejilla'><div>{''.join(turnos_html)}</div><div>{''.join(tarjetas)}</div></div>"
        f"<details><summary>Logs del Job</summary><pre>{html.escape(logs)}</pre></details>"
        "<p><a href='/'>← Escribir otro caso</a></p>"
    )
    return _pagina("".join(partes))


# ------------------------------------------------------------------ servidor


class Visor(BaseHTTPRequestHandler):
    def _responder(self, cuerpo: bytes, codigo: int = 200) -> None:
        self.send_response(codigo)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Security-Policy", CSP)
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def do_GET(self) -> None:
        if urllib.parse.urlparse(self.path).path != "/":
            self._responder(_pagina("<p>No existe.</p>"), 404)
            return
        consulta = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        clave = consulta.get("ejemplo", [""])[0]
        elegido = ejemplo(clave) if clave else None
        entrevista, relato = elegido or ("SINT-VISOR-01", "ENT: \nTEST: ")
        self._responder(pagina_formulario(entrevista, relato, actual=clave if elegido else ""))

    def do_POST(self) -> None:
        if self.path != "/analizar":
            self._responder(_pagina("<p>No existe.</p>"), 404)
            return
        largo = min(int(self.headers.get("Content-Length", "0") or 0), MAX_CARACTERES * 4)
        datos = urllib.parse.parse_qs(self.rfile.read(largo).decode("utf-8", errors="replace"))
        entrevista = datos.get("entrevista", [""])[0]
        relato = datos.get("relato", [""])[0]
        if datos.get("sintetico", [""])[0] != "si":
            self._responder(
                pagina_formulario(
                    entrevista, relato, "Marque la confirmación de que el caso es sintético."
                )
            )
            return
        try:
            caso = caso_c6(entrevista, relato)
        except ErrorCaso as error:
            self._responder(pagina_formulario(entrevista, relato, str(error)))
            return
        if not _ocupado.acquire(blocking=False):
            self._responder(
                pagina_formulario(
                    entrevista, relato, "Ya hay un análisis en curso: espere a que termine."
                )
            )
            return
        try:
            estado, logs, segundos = analizar(caso)
        except (RuntimeError, OSError, subprocess.TimeoutExpired) as error:
            self._responder(
                pagina_formulario(entrevista, relato, f"No se pudo correr el análisis: {error}")
            )
            return
        finally:
            _ocupado.release()
        self._responder(pagina_resultado(caso, estado, logs, segundos))

    def log_message(self, formato: str, *argumentos: object) -> None:
        # Solo método y ruta; nunca el cuerpo, que lleva el relato.
        sys.stderr.write(f"{self.command} {self.path.split('?')[0]}\n")


def logo_data_uri(ruta: Path) -> str:
    tipos = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".svg": "image/svg+xml",
    }
    tipo = tipos.get(ruta.suffix.lower())
    if tipo is None:
        sys.exit("El escudo debe ser PNG, JPG o SVG.")
    try:
        datos = ruta.expanduser().read_bytes()
    except OSError as error:
        sys.exit(f"No se pudo leer el escudo: {error}")
    return f"data:{tipo};base64,{base64.b64encode(datos).decode()}"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Visor web de la demo del analizador (solo casos sintéticos)."
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8501)
    parser.add_argument(
        "--logo", type=Path, help="PNG, JPG o SVG del escudo (opcional, no versionado)"
    )
    opciones = parser.parse_args()
    if shutil.which("kubectl") is None:
        sys.exit("Falta kubectl en el PATH.")
    if opciones.logo is not None:
        _logo["uri"] = logo_data_uri(opciones.logo)
    servidor = ThreadingHTTPServer((opciones.host, opciones.port), Visor)
    print(f"Visor de la demo en http://{opciones.host}:{opciones.port}  (Ctrl+C para salir)")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nVisor detenido.")


if __name__ == "__main__":
    main()
