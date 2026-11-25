"""Ejecutor listo (paso 3): el paquete se importa, está tipado y la red está bloqueada."""

import socket
from importlib.resources import files

import pytest
from pytest_socket import SocketBlockedError

import veridicus_anonymizer


def test_package_imports_and_exposes_public_surface() -> None:
    assert veridicus_anonymizer.__all__ == ["Anonymizer", "build_anonymizer"]


def test_package_ships_py_typed() -> None:
    assert (files("veridicus_anonymizer") / "py.typed").is_file()


def test_pytest_socket_blocks_connections() -> None:
    with pytest.raises(SocketBlockedError):
        socket.create_connection(("192.0.2.1", 443), timeout=1)
