"""Tryke fixtures for SFR Box tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from tryke import Depends, fixture

from homeassistant.components.sfr_box.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER, ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.sfr_box.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def config_entry(
    hass: HomeAssistant = Depends(hass_fixture),
) -> ConfigEntry:
    """Create and register mock config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        source=SOURCE_USER,
        data={CONF_HOST: "192.168.0.1"},
        unique_id="e4:5d:51:00:11:22",
        options={},
        entry_id="123456",
    )
    entry.add_to_hass(hass)
    return entry


@fixture
def config_entry_with_auth(
    hass: HomeAssistant = Depends(hass_fixture),
) -> ConfigEntry:
    """Create and register mock config entry with auth."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        source=SOURCE_USER,
        data={
            CONF_HOST: "192.168.0.1",
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "password",
        },
        unique_id="e4:5d:51:00:11:23",
        options={},
        entry_id="1234567",
    )
    entry.add_to_hass(hass)
    return entry
