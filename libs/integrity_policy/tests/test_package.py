"""Ejecutor listo (paso 2): el paquete se importa, está tipado y la red está bloqueada."""

import socket
from importlib.resources import files

import pytest
from pytest_socket import SocketBlockedError

import veridicus_integrity_policy


def test_package_imports_and_exposes_no_public_surface_yet() -> None:
    assert veridicus_integrity_policy.__all__ == []


def test_package_ships_py_typed() -> None:
    assert (files("veridicus_integrity_policy") / "py.typed").is_file()


def test_pytest_socket_blocks_connections() -> None:
    with pytest.raises(SocketBlockedError):
        socket.create_connection(("192.0.2.1", 443), timeout=1)
