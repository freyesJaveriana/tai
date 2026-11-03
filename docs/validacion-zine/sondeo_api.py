"""Sondeo de la API compatible con OpenAI de un llama-server ya levantado (US14.1, M2 y M4).

  python sondeo_api.py --url http://127.0.0.1:18100 --m2 <dir> --m4 <dir> [--n 20]

M2 (AC14.1.2): con el razonamiento de Qwen apagado y encendido, envía n peticiones por caso (control sin restricción,
`response_format` con esquema JSON, `json_schema` nativo de llama.cpp y gramática GBNF), valida cada salida con
jsonschema y clasifica cada parámetro (las restricciones, `seed`, `cache_prompt` y `chat_template_kwargs`) como
aceptado, rechazado o aceptado sin efecto.
M4 (AC14.1.4): pares de peticiones idénticas (misma seed, mismos hilos del servidor, misma caché del prompt) y
compara el SHA-256 del contenido; si difiere, busca el primer token distinto con /tokenize.

El prompt es una transcripción sintética con dos contradicciones sembradas: no usa datos del piloto. Cada petición
queda en peticiones.jsonl y las cifras en resumen.json y resumen.txt (líneas «Resultado:» de reporte.md).
"""
import argparse
import hashlib
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import jsonschema

TYPES = ["fecha", "numero", "lugar", "persona", "negacion", "secuencia", "otro"]
QUOTE = {
    "type": "object",
    "properties": {"texto": {"type": "string"}, "turno": {"type": "integer", "minimum": 1}},
    "required": ["texto", "turno"],
    "additionalProperties": False,
}
SCHEMA = {
    "type": "object",
    "properties": {
        "hallazgos": {
            "type": "array",
            "maxItems": 5,
            "items": {
                "type": "object",
                "properties": {
                    "hecho": {"type": "string"},
                    "tipo": {"type": "string", "enum": TYPES},
                    "cita_a": QUOTE,
                    "cita_b": QUOTE,
                    "observaciones": {"type": "string"},
                },
                "required": ["hecho", "tipo", "cita_a", "cita_b", "observaciones"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["hallazgos"],
    "additionalProperties": False,
}
# La misma forma que SCHEMA, escrita a mano en GBNF (con el orden de claves fijo).
GRAMMAR = r"""
root ::= "{" ws "\"hallazgos\"" ws ":" ws "[" ws ( hallazgo ( ws "," ws hallazgo ){0,4} )? ws "]" ws "}"
hallazgo ::= "{" ws "\"hecho\"" ws ":" ws string ws "," ws "\"tipo\"" ws ":" ws tipo ws "," ws "\"cita_a\"" ws ":" ws cita ws "," ws "\"cita_b\"" ws ":" ws cita ws "," ws "\"observaciones\"" ws ":" ws string ws "}"
cita ::= "{" ws "\"texto\"" ws ":" ws string ws "," ws "\"turno\"" ws ":" ws entero ws "}"
tipo ::= "\"fecha\"" | "\"numero\"" | "\"lugar\"" | "\"persona\"" | "\"negacion\"" | "\"secuencia\"" | "\"otro\""
string ::= "\"" ( [^"\\\x7F\x00-\x1F] | "\\" ( ["\\/bfnrt] | "u" [0-9a-fA-F]{4} ) )* "\""
entero ::= [1-9] [0-9]{0,3}
ws ::= | " " | "\n" [ \t]{0,20}
"""
TURNS = [
    {"n": 1, "hablante": "ENT", "texto": "¿Puede contarnos cómo llegaron a la vereda?"},
    {"n": 2, "hablante": "TEST", "texto": "Llegamos un martes por la mañana, éramos tres familias y veníamos a pie desde el río."},
    {"n": 3, "hablante": "ENT", "texto": "¿Quiénes los recibieron?"},
    {"n": 4, "hablante": "TEST", "texto": "Nos recibió don Aurelio, el de la tienda, y nos dio posada en la escuela."},
    {"n": 5, "hablante": "ENT", "texto": "¿Qué pasó después?"},
    {"n": 6, "hablante": "TEST", "texto": "Ese domingo que llegamos llovía mucho; las cinco familias dormimos en la iglesia."},
]
SYSTEM = (
    "Eres un analista de incoherencias internas de un testimonio. Lee los turnos (hablante TEST) y devuelve las "
    "contradicciones sobre hechos centrales, cada una con dos citas literales copiadas exactamente de dos turnos "
    "distintos. No juzgues la veracidad de la persona. Responde solo con un objeto JSON que cumpla este esquema: "
    + json.dumps(SCHEMA, ensure_ascii=False)
)
USER = json.dumps({"turnos": TURNS}, ensure_ascii=False)
CASES = {
    "control": {},
    "response_format": {"response_format": {"type": "json_schema", "json_schema": {"name": "hallazgos", "strict": True, "schema": SCHEMA}}},
    "json_schema": {"json_schema": SCHEMA},
    "grammar": {"grammar": GRAMMAR},
}
MAX_TOKENS = {False: 1024, True: 4096}


class Server:
    def __init__(self, url: str, log: Path):
        self.url = url.rstrip("/")
        self.log = log.open("a", encoding="utf-8")

    def post(self, path: str, body: dict, timeout: int = 3600) -> tuple[int, dict, float]:
        request = urllib.request.Request(
            self.url + path, data=json.dumps(body).encode("utf-8"), headers={"Content-Type": "application/json"}
        )
        start = time.monotonic()
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                status, data = response.status, json.loads(response.read())
        except urllib.error.HTTPError as error:
            status, data = error.code, {"error": error.read().decode("utf-8", "replace")[:1000]}
        except (urllib.error.URLError, TimeoutError) as error:
            status, data = 0, {"error": str(error)}
        return status, data, time.monotonic() - start

    def chat(self, label: str, thinking: bool, extra: dict, **overrides) -> dict:
        body = {
            "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": USER}],
            "temperature": 0.6,
            "top_p": 0.95,
            "max_tokens": MAX_TOKENS[thinking],
            "chat_template_kwargs": {"enable_thinking": thinking},
            "cache_prompt": True,
            **extra,
            **overrides,
        }
        status, data, seconds = self.post("/v1/chat/completions", body)
        message = (data.get("choices") or [{}])[0].get("message", {}) if status == 200 else {}
        timings = data.get("timings", {}) if status == 200 else {}
        content = message.get("content") or ""
        record = {
            "caso": label,
            "razonamiento": thinking,
            "seed": body.get("seed"),
            "cache_prompt": body["cache_prompt"],
            "estado_http": status,
            "segundos": round(seconds, 2),
            "fin": (data.get("choices") or [{}])[0].get("finish_reason") if status == 200 else None,
            "tokens_prompt": timings.get("prompt_n"),
            "tokens_cache": timings.get("cache_n"),
            "tokens_generados": timings.get("predicted_n"),
            "tiene_razonamiento": bool(message.get("reasoning_content")),
            "sha256_contenido": hashlib.sha256(content.encode("utf-8")).hexdigest(),
            "valida_estricta": validates(content),
            "valida_reparada": validates(repair(content)),
            "error": data.get("error") if status != 200 else None,
            "contenido": content,
        }
        self.log.write(json.dumps(record, ensure_ascii=False) + "\n")
        self.log.flush()
        return record

    def tokens(self, text: str) -> list[int]:
        status, data, _ = self.post("/tokenize", {"content": text}, timeout=120)
        return data.get("tokens", []) if status == 200 else []


def validates(content: str) -> bool:
    try:
        jsonschema.validate(json.loads(content), SCHEMA)
    except (ValueError, jsonschema.ValidationError):
        return False
    return True


def repair(content: str) -> str:
    """Lo mínimo que haría un reparador: quitar cercas de código y tomar del primer «{» al último «}»."""
    start, end = content.find("{"), content.rfind("}")
    return content[start : end + 1] if 0 <= start < end else content


def classify(records: list[dict], control_valid: int | None) -> str:
    if any(r["estado_http"] != 200 for r in records):
        codes = sorted({r["estado_http"] for r in records if r["estado_http"] != 200})
        return f"rechazado (HTTP {', '.join(map(str, codes))})"
    valid = sum(r["valida_estricta"] for r in records)
    if valid == len(records):
        return "aceptado"
    if control_valid is not None and valid > control_valid:
        return "aceptado (efecto parcial)"
    return "aceptado sin efecto"


def probe_m2(server: Server, n: int) -> dict:
    summary: dict = {"n": n, "casos": {}}
    for thinking in (False, True):
        state = "encendido" if thinking else "apagado"
        control_valid = None
        for label, extra in CASES.items():
            print(f"{time.strftime('%F %T')} M2 {label}, razonamiento {state}", flush=True)
            records = [server.chat(label, thinking, extra, seed=i + 1) for i in range(n)]
            valid = sum(r["valida_estricta"] for r in records)
            if label == "control":
                control_valid = valid
            summary["casos"][f"{label}/{state}"] = {
                "clasificacion": "referencia" if label == "control" else classify(records, control_valid),
                "validas": valid,
                "validas_reparadas": sum(r["valida_reparada"] for r in records),
                "con_razonamiento": sum(r["tiene_razonamiento"] for r in records),
                "cortadas_por_max_tokens": sum(r["fin"] == "length" for r in records),
                "segundos_mediana": sorted(r["segundos"] for r in records)[n // 2],
                "http_error": sum(r["estado_http"] != 200 for r in records),
            }
    on = sum(v["con_razonamiento"] for k, v in summary["casos"].items() if k.startswith("control/encendido"))
    off = sum(v["con_razonamiento"] for k, v in summary["casos"].items() if k.startswith("control/apagado"))
    summary["chat_template_kwargs"] = {
        "con_razonamiento_encendido": on,
        "con_razonamiento_apagado": off,
        "clasificacion": "aceptado" if on > 0 and off == 0 else "aceptado sin efecto",
    }
    summary["seed"] = probe_seed(server)
    summary["cache_prompt"] = probe_cache(server)
    return summary


def probe_seed(server: Server) -> dict:
    extra = {
        "messages": [{"role": "user", "content": "Escribe una frase de doce palabras sobre un río de montaña."}],
        "temperature": 1.0,
        "max_tokens": 48,
    }
    a, b, c = (server.chat("seed", False, extra, seed=s) for s in (7, 7, 8))
    if any(r["estado_http"] != 200 for r in (a, b, c)):
        verdict = "rechazado"
    elif a["sha256_contenido"] == b["sha256_contenido"] != c["sha256_contenido"]:
        verdict = "aceptado"
    else:
        verdict = "aceptado sin efecto"
    return {
        "misma_seed_igual": a["sha256_contenido"] == b["sha256_contenido"],
        "otra_seed_distinta": a["sha256_contenido"] != c["sha256_contenido"],
        "clasificacion": verdict,
    }


def probe_cache(server: Server) -> dict:
    cold = [server.chat("cache", False, {"max_tokens": 16}, seed=1, cache_prompt=False) for _ in range(2)]
    warm = [server.chat("cache", False, {"max_tokens": 16}, seed=1, cache_prompt=True) for _ in range(2)]
    if any(r["estado_http"] != 200 for r in cold + warm):
        verdict = "rechazado"
    elif warm[1]["tokens_cache"] is None:
        verdict = "no medible: la respuesta no trae timings.cache_n"
    elif (warm[1]["tokens_cache"] or 0) > 0 and not (cold[1]["tokens_cache"] or 0):
        verdict = "aceptado"
    else:
        verdict = "aceptado sin efecto"
    return {
        "prompt_n_sin_cache": cold[1]["tokens_prompt"],
        "prompt_n_con_cache": warm[1]["tokens_prompt"],
        "cache_n_sin_cache": cold[1]["tokens_cache"],
        "cache_n_con_cache": warm[1]["tokens_cache"],
        "segundos_sin_cache": cold[1]["segundos"],
        "segundos_con_cache": warm[1]["segundos"],
        "clasificacion": verdict,
    }


def probe_m4(server: Server) -> dict:
    results = {}
    for thinking in (False, True):
        state = "encendido" if thinking else "apagado"
        for cache in (False, True):
            print(f"{time.strftime('%F %T')} M4 razonamiento {state}, cache_prompt {cache}", flush=True)
            if cache:  # calentamiento: las dos peticiones del par encuentran la misma caché
                server.chat("m4-calentamiento", thinking, {}, seed=42, cache_prompt=True)
            a, b = (server.chat("m4", thinking, {}, seed=42, cache_prompt=cache) for _ in range(2))
            same = a["sha256_contenido"] == b["sha256_contenido"] and a["estado_http"] == b["estado_http"] == 200
            entry = {"igual": same, "sha256_a": a["sha256_contenido"], "sha256_b": b["sha256_contenido"]}
            if not same:
                ta, tb = server.tokens(a["contenido"]), server.tokens(b["contenido"])
                first = next((i for i, (x, y) in enumerate(zip(ta, tb)) if x != y), min(len(ta), len(tb)))
                entry |= {"primer_token_distinto": first, "tokens_a": len(ta), "tokens_b": len(tb)}
            results[f"razonamiento {state}, cache_prompt {str(cache).lower()}"] = entry
    return results


def m2_lines(s: dict) -> list[str]:
    lines = []
    for label in CASES:
        off, on = s["casos"][f"{label}/apagado"], s["casos"][f"{label}/encendido"]
        name = {"control": "control sin restricción", "response_format": "response_format (json_schema)",
                "json_schema": "json_schema nativo", "grammar": "grammar (GBNF)"}[label]
        lines.append(
            f"Resultado: {name}: apagado {off['clasificacion']}, {off['validas']}/{s['n']} válidas "
            f"({off['validas_reparadas']} reparando, {off['cortadas_por_max_tokens']} cortadas); encendido "
            f"{on['clasificacion']}, {on['validas']}/{s['n']} válidas ({on['validas_reparadas']} reparando, "
            f"{on['cortadas_por_max_tokens']} cortadas, {on['con_razonamiento']} con razonamiento)"
        )
    k, seed, cache = s["chat_template_kwargs"], s["seed"], s["cache_prompt"]
    lines.append(
        f"Resultado: chat_template_kwargs.enable_thinking: {k['clasificacion']} (con razonamiento: "
        f"{k['con_razonamiento_encendido']}/{s['n']} encendido, {k['con_razonamiento_apagado']}/{s['n']} apagado)"
    )
    lines.append(
        f"Resultado: seed: {seed['clasificacion']} (misma seed igual: {seed['misma_seed_igual']}; "
        f"otra seed distinta: {seed['otra_seed_distinta']})"
    )
    lines.append(
        f"Resultado: cache_prompt: {cache['clasificacion']} (con caché: cache_n {cache['cache_n_con_cache']}, "
        f"prompt_n {cache['prompt_n_con_cache']}; sin caché: cache_n {cache['cache_n_sin_cache']}, "
        f"prompt_n {cache['prompt_n_sin_cache']}; "
        f"{cache['segundos_con_cache']} s frente a {cache['segundos_sin_cache']} s)"
    )
    return lines


def m4_lines(results: dict) -> list[str]:
    lines = []
    for label, r in results.items():
        if r["igual"]:
            lines.append(f"Resultado: {label}: SHA-256 igual ({r['sha256_a'][:16]}…)")
        else:
            lines.append(
                f"Resultado: {label}: SHA-256 distinto; primer token distinto en la posición "
                f"{r['primer_token_distinto']} (de {r['tokens_a']} y {r['tokens_b']} tokens)"
            )
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--url", required=True)
    parser.add_argument("--m2", type=Path, required=True)
    parser.add_argument("--m4", type=Path, required=True)
    parser.add_argument("--n", type=int, default=20)
    args = parser.parse_args()
    for folder in (args.m2, args.m4):
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "peticiones.jsonl").unlink(missing_ok=True)

    m2 = probe_m2(Server(args.url, args.m2 / "peticiones.jsonl"), args.n)
    (args.m2 / "resumen.json").write_text(json.dumps(m2, ensure_ascii=False, indent=1), encoding="utf-8")
    with (args.m2 / "resumen.txt").open("a", encoding="utf-8") as fh:
        fh.write("\n".join(m2_lines(m2)) + "\n")

    m4 = probe_m4(Server(args.url, args.m4 / "peticiones.jsonl"))
    (args.m4 / "resumen.json").write_text(json.dumps(m4, ensure_ascii=False, indent=1), encoding="utf-8")
    with (args.m4 / "resumen.txt").open("a", encoding="utf-8") as fh:
        fh.write("\n".join(m4_lines(m4)) + "\n")
    print("M2 y M4 terminados", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
