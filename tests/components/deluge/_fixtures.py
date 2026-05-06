"""Tryke fixtures for Deluge."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from tryke import fixture


@fixture
def api() -> Generator[None]:
    """Mock an api."""
    with (
        patch("deluge_client.client.DelugeRPCClient.connect"),
        patch("deluge_client.client.DelugeRPCClient._create_socket"),
    ):
        yield


@fixture
def conn_error() -> Generator[None]:
    """Mock an api connection error."""
    with (
        patch(
            "deluge_client.client.DelugeRPCClient.connect",
            side_effect=ConnectionRefusedError("111: Connection refused"),
        ),
        patch("deluge_client.client.DelugeRPCClient._create_socket"),
    ):
        yield


@fixture
def unknown_error() -> Generator[None]:
    """Mock an api unknown error."""
    with (
        patch("deluge_client.client.DelugeRPCClient.connect", side_effect=Exception),
        patch("deluge_client.client.DelugeRPCClient._create_socket"),
    ):
        yield


@fixture
def deluge_setup() -> Generator[None]:
    """Mock deluge entry setup."""
    with patch("homeassistant.components.deluge.async_setup_entry", return_value=True):
        yield


@fixture
def mock_zeroconf() -> Generator[MagicMock]:
    """Mock zeroconf."""
    from zeroconf import DNSCache  # noqa: PLC0415

    with (
        patch("homeassistant.components.zeroconf.HaZeroconf") as mock_zc,
        patch(
            "homeassistant.components.zeroconf.discovery.AsyncServiceBrowser",
        ) as mock_browser,
    ):
        asb = mock_browser.return_value
        asb.async_cancel = AsyncMock()
        zc = mock_zc.return_value
        zc.cache = DNSCache()
        yield mock_zc
