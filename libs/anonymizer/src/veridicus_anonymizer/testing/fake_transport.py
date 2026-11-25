"""Transporte HTTP falso sobre `httpx.MockTransport` (BR5.5, R-07).

Captura cada petición **cruda** (método, dominio, puerto, ruta, cabeceras y cuerpo) y devuelve
respuestas grabadas sintéticas o errores simulados, en el orden en que se guionaron. Nunca abre
red. La clave de API se guarda tal cual en la captura, para que una prueba pueda comprobar que
viaja solo en la cabecera de autenticación; solo se oculta al **representar** la petición
(`repr` y mensajes de aserción).
"""

import json
from dataclasses import dataclass, field
from typing import Any

import httpx

# Cabeceras cuyo valor es una credencial y no se muestra al representar la petición.
HIDDEN_HEADERS = frozenset({"x-api-key", "authorization", "api-key", "x-goog-api-key"})
HIDDEN_VALUE = "***"
_DEFAULT_PORTS = {"https": 443, "http": 80}


@dataclass(frozen=True, repr=False)
class CapturedRequest:
    """Petición cruda: guarda la clave tal cual y solo la oculta al representarla."""

    method: str
    scheme: str
    host: str
    port: int
    path: str
    headers: dict[str, str]
    body: bytes

    def __repr__(self) -> str:
        shown = {
            name: HIDDEN_VALUE if name.lower() in HIDDEN_HEADERS else value
            for name, value in self.headers.items()
        }
        return (
            f"CapturedRequest({self.method} {self.scheme}://{self.host}:{self.port}{self.path}, "
            f"headers={shown}, body=<{len(self.body)} bytes>)"
        )


@dataclass(frozen=True)
class FakeResponse:
    """Una respuesta guionada: grabada o un error simulado."""

    status: int = 200
    body: bytes = b""
    headers: dict[str, str] = field(default_factory=dict)
    raises: Exception | None = None

    @classmethod
    def ok_json(cls, payload: Any) -> "FakeResponse":
        """200 con un cuerpo JSON (por ejemplo, un sobre de la Messages API)."""
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        return cls(status=200, body=body, headers={"content-type": "application/json"})

    @classmethod
    def http_error(cls, status: int) -> "FakeResponse":
        """Un error HTTP del proveedor (5xx, 4xx) con el cuerpo de error de la Messages API."""
        payload = {
            "type": "error",
            "error": {"type": "api_error", "message": "error sintético"},
            "request_id": "req_sintetico_0001",
        }
        return cls(
            status=status,
            body=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"content-type": "application/json"},
        )

    @classmethod
    def not_json(cls) -> "FakeResponse":
        """200 con un cuerpo que no es JSON."""
        return cls(
            status=200, body=b"<html>esto no es json</html>", headers={"content-type": "text/html"}
        )

    @classmethod
    def timeout(cls) -> "FakeResponse":
        """El proveedor no responde a tiempo: el transporte lanza `httpx.ReadTimeout`."""
        return cls(raises=httpx.ReadTimeout("plazo agotado sintético"))

    @classmethod
    def redirect(cls, location: str) -> "FakeResponse":
        """307 hacia otra URL; un cliente sin `follow_redirects` no la sigue."""
        return cls(status=307, headers={"location": location})


class FakeTransport(httpx.MockTransport):
    """Captura cada petición y devuelve las respuestas guionadas, en orden. Nunca abre red."""

    requests: list[CapturedRequest]

    def __init__(self, *responses: FakeResponse) -> None:
        self.requests = []
        self._pending = list(responses)
        super().__init__(self._handle)

    @property
    def request_count(self) -> int:
        """Cuántas peticiones llegaron al transporte."""
        return len(self.requests)

    def __repr__(self) -> str:
        return f"FakeTransport(requests={self.requests!r})"

    def _handle(self, request: httpx.Request) -> httpx.Response:
        scheme = request.url.scheme
        port = request.url.port if request.url.port is not None else _DEFAULT_PORTS[scheme]
        self.requests.append(
            CapturedRequest(
                method=request.method,
                scheme=scheme,
                host=request.url.host,
                port=port,
                path=request.url.path,
                headers=dict(request.headers),
                body=request.read(),
            )
        )
        if not self._pending:
            raise RuntimeError("FakeTransport sin respuestas guionadas para esta petición")
        scripted = self._pending.pop(0)
        if scripted.raises is not None:
            raise scripted.raises
        return httpx.Response(scripted.status, content=scripted.body, headers=scripted.headers)
