"""Tryke fixtures for Renault integration tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from tryke import Depends, fixture

from homeassistant.components.renault.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant

from .const import MOCK_ACCOUNT_ID, MOCK_CONFIG

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.renault.async_setup_entry", return_value=True
    ) as m:
        yield m


@fixture
def config_entry(
    hass: HomeAssistant = Depends(hass_fixture),
) -> MockConfigEntry:
    """Create and register mock config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        source=SOURCE_USER,
        data=MOCK_CONFIG,
        unique_id=MOCK_ACCOUNT_ID,
        options={},
        entry_id="123456",
    )
    entry.add_to_hass(hass)
    return entry
