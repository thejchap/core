"""Tryke fixtures for the Gree integration."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from tryke import fixture

from .common import FakeDiscovery, build_device_mock


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.gree.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def discovery() -> Generator[object]:
    """Patch the discovery object."""
    with patch("homeassistant.components.gree.coordinator.Discovery") as mock:
        mock.return_value = FakeDiscovery()
        yield mock


@fixture
def device() -> Generator[object]:
    """Patch the device search and bind."""
    with patch(
        "homeassistant.components.gree.coordinator.Device",
        return_value=build_device_mock(),
    ) as mock:
        yield mock
