"""Ejecutor listo (paso 2): el paquete se importa, está tipado y la red está bloqueada."""

import socket
from importlib.resources import files

import pytest
from pytest_socket import SocketBlockedError

import veridicus_execution_profiles
from veridicus_execution_profiles.floors import COMMERCIAL_MIN_CALL_TIMEOUT_S


def test_package_imports_and_exposes_no_public_surface_yet() -> None:
    assert veridicus_execution_profiles.__all__ == []


def test_package_ships_py_typed() -> None:
    assert (files("veridicus_execution_profiles") / "py.typed").is_file()


def test_commercial_floor_is_270_seconds() -> None:
    assert COMMERCIAL_MIN_CALL_TIMEOUT_S == 270


def test_pytest_socket_blocks_connections() -> None:
    with pytest.raises(SocketBlockedError):
        socket.create_connection(("192.0.2.1", 443), timeout=1)
