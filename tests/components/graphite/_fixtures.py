"""Tryke fixtures for Graphite tests."""

from collections.abc import Generator
from unittest.mock import MagicMock, patch

from tryke import Depends, fixture

from tests.hass_fixtures import mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Module-local anchor; opts the test module into Tryke's HookExecutor path."""
    return 0


@fixture
def mock_gf() -> Generator[MagicMock]:
    """Mock Graphite Feeder fixture."""
    with patch("homeassistant.components.graphite.GraphiteFeeder") as mock_gf:
        yield mock_gf


@fixture
def mock_socket() -> Generator[MagicMock]:
    """Mock socket fixture."""
    with patch("socket.socket") as mock_socket:
        yield mock_socket


@fixture
def mock_time() -> Generator[MagicMock]:
    """Mock time fixture."""
    with patch("time.time") as mock_time:
        yield mock_time
