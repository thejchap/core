"""Tryke fixtures for Sense integration tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from tryke import fixture


@fixture
def mock_sense() -> Generator[AsyncMock]:
    """Mock Sense object for authentication."""
    with patch(
        "homeassistant.components.sense.config_flow.ASyncSenseable"
    ) as mock_sense:
        mock_sense.return_value.authenticate = AsyncMock(return_value=True)
        mock_sense.return_value.validate_mfa = AsyncMock(return_value=True)
        mock_sense.return_value.sense_access_token = "ABC"
        mock_sense.return_value.sense_user_id = "123"
        mock_sense.return_value.sense_monitor_id = "456"
        mock_sense.return_value.device_id = "789"
        mock_sense.return_value.refresh_token = "XYZ"
        yield mock_sense
