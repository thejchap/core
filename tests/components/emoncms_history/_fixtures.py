"""Tryke fixtures for the emoncms_history tests."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, patch

from tryke import fixture


@fixture
async def emoncms_client() -> AsyncGenerator[AsyncMock]:
    """Mock pyemoncms client with successful responses."""
    with patch(
        "homeassistant.components.emoncms_history.EmoncmsClient", autospec=True
    ) as mock_client:
        client = mock_client.return_value
        client.async_input_post.return_value = '{"success": true}'
        yield client
