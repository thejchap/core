"""Tryke fixtures for Obihai tests."""

from __future__ import annotations

from collections.abc import Generator
from socket import gaierror
from unittest.mock import AsyncMock, patch

from tryke import fixture


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.obihai.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def mock_gaierror() -> Generator[AsyncMock]:
    """Patch gethostbyname to raise gaierror."""
    with patch(
        "homeassistant.components.obihai.config_flow.gethostbyname",
        side_effect=gaierror(),
    ) as mock_setup_entry:
        yield mock_setup_entry
