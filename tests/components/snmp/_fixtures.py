"""Tryke fixtures for SNMP tests."""

from collections.abc import Generator
import socket
from unittest.mock import patch

from tryke import fixture


@fixture
def patch_getaddrinfo() -> Generator[None]:
    """Patch getaddrinfo to avoid DNS lookups in SNMP tests."""
    with patch.object(socket, "getaddrinfo"):
        yield
