"""Tryke fixtures for Tesla Wall Connector."""

from collections.abc import Generator
from unittest.mock import patch

from tesla_wall_connector.wall_connector import Version
from tryke import fixture


def get_default_version_data() -> Version:
    """Return default version data object for a wall connector."""
    return Version(
        {
            "serial_number": "abc123",
            "part_number": "part_123",
            "firmware_version": "1.2.3",
        }
    )


@fixture
def mock_wall_connector_version() -> Generator[None]:
    """Mock get_version calls to the wall connector API."""
    with patch(
        "tesla_wall_connector.WallConnector.async_get_version",
        return_value=get_default_version_data(),
    ):
        yield


@fixture
def mock_wall_connector_setup() -> Generator[None]:
    """Mock component setup."""
    with patch(
        "homeassistant.components.tesla_wall_connector.async_setup_entry",
        return_value=True,
    ):
        yield
