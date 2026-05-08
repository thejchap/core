"""Test pushbullet integration."""

from __future__ import annotations

from unittest.mock import patch

from pushbullet import InvalidKeyError, PushbulletError
from requests_mock import Mocker
from tryke import Depends, expect, fixture, test

from homeassistant.components.pushbullet.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import EVENT_HOMEASSISTANT_START
from homeassistant.core import HomeAssistant

from . import MOCK_CONFIG
from ._fixtures import requests_mock_fixture

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Module-level anchor fixture."""


@test
async def async_setup_entry_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _requests: Mocker = Depends(requests_mock_fixture),
) -> None:
    """Test pushbullet successful setup."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_CONFIG,
    )
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    expect(entry.state).to_be(ConfigEntryState.LOADED)

    with patch(
        "homeassistant.components.pushbullet.api.PushBulletNotificationProvider.start"
    ) as mock_start:
        hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
        await hass.async_block_till_done()
        mock_start.assert_called_once()


@test
async def setup_entry_failed_invalid_key(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test pushbullet failed setup due to invalid key."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_CONFIG,
    )
    entry.add_to_hass(hass)
    with patch(
        "homeassistant.components.pushbullet.PushBullet",
        side_effect=InvalidKeyError,
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    expect(entry.state).to_be(ConfigEntryState.SETUP_ERROR)


@test
async def setup_entry_failed_conn_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test pushbullet failed setup due to conn error."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_CONFIG,
    )
    entry.add_to_hass(hass)
    with patch(
        "homeassistant.components.pushbullet.PushBullet",
        side_effect=PushbulletError,
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def async_unload_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _requests: Mocker = Depends(requests_mock_fixture),
) -> None:
    """Test pushbullet unload entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_CONFIG,
    )
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    expect(entry.state).to_be(ConfigEntryState.LOADED)

    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    expect(entry.state).to_be(ConfigEntryState.NOT_LOADED)
