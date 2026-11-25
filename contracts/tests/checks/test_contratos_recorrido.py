"""Recorrido de los contratos propios: la mitad TypeScript no es un contrato (E-38, P-T20-11).

`contracts/ts/` lleva `package.json`, el lockfile y, tras `npm ci`, `node_modules/` con miles de YAML y
JSON ajenos. Ninguno es un contrato propio, así que el recorrido no entra en `ts/`.
"""

from pathlib import Path

from veridicus_contracts.checks import _contratos


def test_un_archivo_de_contrato_bajo_ts_no_se_recorre(tmp_path: Path) -> None:
    for relativa in (
        "api/b.yaml",
        "ts/package.json",
        "ts/node_modules/paquete/datos.yaml",
        "ts/generated/otro.json",
    ):
        archivo = tmp_path / relativa
        archivo.parent.mkdir(parents=True, exist_ok=True)
        archivo.write_text("{}\n", encoding="utf-8")
    rutas = [ruta for ruta, _ in _contratos.contratos_propios(tmp_path)]
    assert rutas == ["api/b.yaml"]
    assert "ts" in _contratos.EXCLUIDOS
