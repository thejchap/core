"""Tryke fixtures for 1-Wire tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from tryke import Depends, fixture

from homeassistant.components.onewire.const import DOMAIN, MANUFACTURER_MAXIM
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.onewire.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def config_entry(
    hass: HomeAssistant = Depends(hass_fixture),
) -> MockConfigEntry:
    """Create and register mock config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        source=SOURCE_USER,
        data={
            CONF_HOST: "1.2.3.4",
            CONF_PORT: 1234,
        },
        options={
            "device_options": {
                "28.222222222222": {"precision": "temperature9"},
                "28.222222222223": {"precision": "temperature5"},
            }
        },
        entry_id="2",
    )
    entry.add_to_hass(hass)
    return entry


@fixture
def filled_device_registry(
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(config_entry),
) -> dr.DeviceRegistry:
    """Fill device registry with mock devices."""
    device_registry = dr.async_get(hass)
    for key in ("28.111111111111", "28.222222222222", "28.222222222223"):
        device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={(DOMAIN, key)},
            manufacturer=MANUFACTURER_MAXIM,
            model="DS18B20",
            name=key,
        )
    return device_registry
