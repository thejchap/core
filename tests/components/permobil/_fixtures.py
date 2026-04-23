"""Tryke fixtures for MyPermobil tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, Mock, patch

from mypermobil import MyPermobil
from tryke import fixture

from .const import MOCK_REGION_NAME, MOCK_TOKEN, MOCK_URL


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.permobil.async_setup_entry", return_value=True
    ) as mock_setup:
        yield mock_setup


@fixture
def my_permobil() -> Mock:
    """Mock spec for MyPermobilApi."""
    mock = Mock(spec=MyPermobil)
    mock.request_region_names.return_value = {MOCK_REGION_NAME: MOCK_URL}
    mock.request_application_token.return_value = MOCK_TOKEN
    mock.region = ""
    return mock
