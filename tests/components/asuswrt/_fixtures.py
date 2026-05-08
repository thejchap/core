"""Tryke fixtures for the AsusWrt integration."""

from collections.abc import Generator
from unittest.mock import patch

from tryke import fixture

from .common import ASUSWRT_BASE


@fixture
def patch_get_host() -> Generator:
    """Mock call to socket gethostbyname function.

    Patches the wrapper function ``_get_ip`` rather than the global
    ``socket.gethostbyname`` to avoid leaking into other modules.
    """
    with patch(
        f"{ASUSWRT_BASE}.config_flow._get_ip", return_value="192.168.1.1"
    ) as get_host_mock:
        yield get_host_mock


@fixture
def patch_is_file() -> Generator:
    """Mock call to os path.isfile function.

    Patches the wrapper ``_is_file`` rather than the global
    ``os.path.isfile`` (which would corrupt e.g. zoneinfo tzdata
    lookups via shared ``os.path``).
    """
    with patch(
        f"{ASUSWRT_BASE}.config_flow._is_file", return_value=True
    ) as is_file_mock:
        yield is_file_mock
