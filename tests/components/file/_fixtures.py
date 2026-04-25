"""Tryke fixtures for file platform tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from tryke import Depends, fixture

from homeassistant.core import HomeAssistant

from tests.hass_fixtures import hass as hass_fixture


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.file.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def mock_is_allowed_path_true(
    hass: HomeAssistant = Depends(hass_fixture),
) -> Generator[MagicMock]:
    """Mock is_allowed_path returning True."""
    with patch.object(
        hass.config, "is_allowed_path", return_value=True
    ) as allowed_path_mock:
        yield allowed_path_mock


@fixture
def mock_is_allowed_path_false(
    hass: HomeAssistant = Depends(hass_fixture),
) -> Generator[MagicMock]:
    """Mock is_allowed_path returning False."""
    with patch.object(
        hass.config, "is_allowed_path", return_value=False
    ) as allowed_path_mock:
        yield allowed_path_mock
