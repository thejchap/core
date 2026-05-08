"""Tryke fixtures for the Squeezebox integration."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from tryke import fixture

SERVER_UUIDS = [
    "12345678-1234-1234-1234-123456789012",
    "87654321-4321-4321-4321-210987654321",
]


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.squeezebox.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def mock_server() -> Generator[AsyncMock]:
    """Mock pysqueezebox.Server per test run."""
    with patch("homeassistant.components.squeezebox.config_flow.Server") as server_cls:
        server_mock = server_cls.return_value
        server_mock.async_query = AsyncMock()
        yield server_mock


@fixture
def mock_discover_timeout() -> Generator[None]:
    """Mock the discovery timeout so tests run fast."""
    with patch("homeassistant.components.squeezebox.config_flow.TIMEOUT", 0):
        yield
