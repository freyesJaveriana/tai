"""C21, la petición de `anonymizer-proxy`: estricta, sin destino ni clave elegidos por quien llama (NFR1.3).

Rojo hasta T13 (`api/anonymizer-proxy.v1.yaml`).
"""

import pytest
from helpers import Caso, comprobar_caso, puntero_de_cuerpo, validador_de

pytestmark = pytest.mark.c21

C21 = "api/anonymizer-proxy.v1.yaml"
DIRECTORIO = "api/fixtures/anonymizer-proxy"

CASOS = [
    Caso("request.valid.yaml", "C21.request"),
    Caso(
        "request.with-destination.yaml",
        "C21.request",
        "NFR1.3",
        ("additionalProperties", "$", "destination"),
    ),
    Caso(
        "request.with-api-key-ref.yaml",
        "C21.request",
        "NFR1.3",
        ("additionalProperties", "$", "api_key_ref"),
    ),
]


@pytest.mark.parametrize("caso", [pytest.param(c, id=c.archivo) for c in CASOS])
def test_cada_peticion_del_proxy_se_acepta_o_se_rechaza_por_su_regla(caso: Caso) -> None:
    validador = validador_de(C21, puntero_de_cuerpo("/v1/generate", "post"))
    comprobar_caso(DIRECTORIO, caso, validador)
