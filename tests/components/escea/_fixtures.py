"""Tryke fixtures for the Escea integration."""

from unittest.mock import AsyncMock, MagicMock

from tryke import fixture


@fixture
def mock_discovery_service() -> AsyncMock:
    """Mock discovery service."""
    discovery_service = AsyncMock()
    discovery_service.controllers = {}
    return discovery_service


@fixture
def mock_controller() -> MagicMock:
    """Mock controller."""
    return MagicMock()
