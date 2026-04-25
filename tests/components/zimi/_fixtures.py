"""Tryke fixtures for Zimi tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from tryke import fixture


@fixture
def discovery_mock() -> Generator[MagicMock]:
    """Mock the ControlPointDiscoveryService."""
    with patch(
        "homeassistant.components.zimi.config_flow.ControlPointDiscoveryService",
        autospec=True,
    ) as mock:
        mock.return_value = mock
        yield mock


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.zimi.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry
