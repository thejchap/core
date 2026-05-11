"""Test the laundrify init file."""

from unittest.mock import AsyncMock

from laundrify_aio import exceptions
from tryke import Depends, expect, fixture, test

from homeassistant.components.laundrify.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_ACCESS_TOKEN
from homeassistant.core import HomeAssistant

from ._fixtures import laundrify_api_mock, laundrify_config_entry
from .const import VALID_ACCESS_TOKEN

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def setup_entry_api_unauthorized(
    hass: HomeAssistant = Depends(hass_fixture),
    laundrify_api_mock: AsyncMock = Depends(laundrify_api_mock),
    laundrify_config_entry: MockConfigEntry = Depends(laundrify_config_entry),
) -> None:
    """Test that ConfigEntryAuthFailed is thrown when authentication fails."""
    laundrify_api_mock.validate_token.side_effect = exceptions.UnauthorizedException
    await hass.config_entries.async_reload(laundrify_config_entry.entry_id)

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(laundrify_config_entry.state).to_be(ConfigEntryState.SETUP_ERROR)
    expect(hass.data.get(DOMAIN)).to_be(None)


@test
async def setup_entry_api_cannot_connect(
    hass: HomeAssistant = Depends(hass_fixture),
    laundrify_api_mock: AsyncMock = Depends(laundrify_api_mock),
    laundrify_config_entry: MockConfigEntry = Depends(laundrify_config_entry),
) -> None:
    """Test that ApiConnectionException is thrown when connection fails."""
    laundrify_api_mock.validate_token.side_effect = exceptions.ApiConnectionException
    await hass.config_entries.async_reload(laundrify_config_entry.entry_id)

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(laundrify_config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)
    expect(hass.data.get(DOMAIN)).to_be(None)


@test
async def setup_entry_successful(
    hass: HomeAssistant = Depends(hass_fixture),
    laundrify_config_entry: MockConfigEntry = Depends(laundrify_config_entry),
) -> None:
    """Test entry can be setup successfully."""
    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(laundrify_config_entry.state).to_be(ConfigEntryState.LOADED)


@test
async def setup_entry_unload(
    hass: HomeAssistant = Depends(hass_fixture),
    laundrify_config_entry: MockConfigEntry = Depends(laundrify_config_entry),
) -> None:
    """Test unloading the laundrify entry."""
    await hass.config_entries.async_unload(laundrify_config_entry.entry_id)

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(laundrify_config_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test
async def migrate_entry_minor_version_1_2(
    hass: HomeAssistant = Depends(hass_fixture),
    laundrify_api_mock: AsyncMock = Depends(laundrify_api_mock),
) -> None:
    """Test migrating a 1.1 config entry to 1.2."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_ACCESS_TOKEN: VALID_ACCESS_TOKEN},
        version=1,
        minor_version=1,
        unique_id=123456,
    )
    entry.add_to_hass(hass)
    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
    expect(entry.version).to_equal(1)
    expect(entry.minor_version).to_equal(2)
    expect(entry.unique_id).to_equal("123456")
