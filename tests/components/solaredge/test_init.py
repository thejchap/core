"""Tests for the SolarEdge integration."""

from unittest.mock import AsyncMock, Mock, patch

from aiohttp import ClientError
from tryke import Depends, expect, fixture, test

from homeassistant.components.solaredge.const import CONF_SITE_ID, DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_API_KEY, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from ._fixtures import recorder_mock, solaredge_api, solaredge_web_api

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

SITE_ID = "1a2b3c4d5e6f7g8h"
API_KEY = "a1b2c3d4e5f6g7h8"
USERNAME = "test-username"
PASSWORD = "test-password"


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _recorder: object = Depends(recorder_mock),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Force tryke to fully resolve hass + recorder."""
    return hass


@test
async def setup_unload_api_key(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    solaredge_api: Mock = Depends(solaredge_api),
) -> None:
    """Test successful setup and unload of a config entry with API key."""
    with patch(
        "homeassistant.config_entries.ConfigEntries.async_unload_platforms",
        return_value=True,
    ) as mock_unload_platforms:
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={CONF_SITE_ID: SITE_ID, CONF_API_KEY: API_KEY},
        )
        entry.add_to_hass(hass)

        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        expect(entry.state).to_be(ConfigEntryState.LOADED)
        expect(solaredge_api.get_details.await_count).to_equal(2)

        expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
        await hass.async_block_till_done()

        # Unloading should be attempted because sensors were set up.
        mock_unload_platforms.assert_awaited_once()
        expect(entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test
async def setup_unload_web_login(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    solaredge_web_api: AsyncMock = Depends(solaredge_web_api),
) -> None:
    """Test successful setup and unload of a config entry with web login."""
    with patch(
        "homeassistant.config_entries.ConfigEntries.async_unload_platforms",
        return_value=True,
    ) as mock_unload_platforms:
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_SITE_ID: SITE_ID,
                CONF_USERNAME: USERNAME,
                CONF_PASSWORD: PASSWORD,
            },
        )
        entry.add_to_hass(hass)

        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        expect(entry.state).to_be(ConfigEntryState.LOADED)
        solaredge_web_api.async_get_equipment.assert_awaited_once()
        solaredge_web_api.async_get_energy_data.assert_awaited_once()

        expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
        await hass.async_block_till_done()

        # Unloading should NOT be attempted because sensors were not set up.
        mock_unload_platforms.assert_not_called()
        expect(entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test
async def setup_unload_both(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    solaredge_api: Mock = Depends(solaredge_api),
    solaredge_web_api: AsyncMock = Depends(solaredge_web_api),
) -> None:
    """Test successful setup and unload of a config entry with both auth methods."""
    with patch(
        "homeassistant.config_entries.ConfigEntries.async_unload_platforms",
        return_value=True,
    ) as mock_unload_platforms:
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_SITE_ID: SITE_ID,
                CONF_API_KEY: API_KEY,
                CONF_USERNAME: USERNAME,
                CONF_PASSWORD: PASSWORD,
            },
        )
        entry.add_to_hass(hass)

        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        expect(entry.state).to_be(ConfigEntryState.LOADED)
        expect(solaredge_api.get_details.await_count).to_equal(2)
        solaredge_web_api.async_get_equipment.assert_awaited_once()
        solaredge_web_api.async_get_energy_data.assert_awaited_once()

        expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
        await hass.async_block_till_done()

        mock_unload_platforms.assert_awaited_once()
        expect(entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test
async def api_key_config_not_ready(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    solaredge_api: Mock = Depends(solaredge_api),
) -> None:
    """Test for setup failure with API key."""
    solaredge_api.get_details.side_effect = ClientError()
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_SITE_ID: SITE_ID, CONF_API_KEY: API_KEY},
    )
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def web_login_config_not_ready(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    solaredge_web_api: AsyncMock = Depends(solaredge_web_api),
) -> None:
    """Test for setup failure with web login."""
    solaredge_web_api.async_get_equipment.side_effect = ClientError()
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_SITE_ID: SITE_ID,
            CONF_USERNAME: USERNAME,
            CONF_PASSWORD: PASSWORD,
        },
    )
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)
