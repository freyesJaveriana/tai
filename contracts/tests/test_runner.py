"""Pruebas del ejecutor: red bloqueada y árbol de contracts/ resuelto."""

import socket
from pathlib import Path

import pytest
from pytest_socket import SocketBlockedError


def test_socket_bloqueado() -> None:
    with pytest.raises(SocketBlockedError):
        socket.socket(socket.AF_INET, socket.SOCK_STREAM)


def test_raiz_de_contracts(contracts_root: Path) -> None:
    assert (contracts_root / "pyproject.toml").is_file()
    assert (contracts_root / "src" / "veridicus_contracts" / "py.typed").is_file()
