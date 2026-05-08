"""Tryke fixtures for the AsusWrt integration."""

from collections.abc import Generator
from unittest.mock import patch

from tryke import fixture

from .common import ASUSWRT_BASE


@fixture
def patch_get_host() -> Generator:
    """Mock call to socket gethostbyname function."""
    with patch(
        f"{ASUSWRT_BASE}.config_flow.socket.gethostbyname", return_value="192.168.1.1"
    ) as get_host_mock:
        yield get_host_mock


@fixture
def patch_is_file() -> Generator:
    """Mock call to os path.isfile function."""
    with patch(
        f"{ASUSWRT_BASE}.config_flow.os.path.isfile", return_value=True
    ) as is_file_mock:
        yield is_file_mock
