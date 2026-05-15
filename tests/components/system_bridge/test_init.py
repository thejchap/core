"""Test the System Bridge integration."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.system_bridge.config_flow import SystemBridgeConfigFlow
from homeassistant.components.system_bridge.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_PORT, CONF_TOKEN
from homeassistant.core import HomeAssistant

from . import FIXTURE_USER_INPUT, FIXTURE_UUID

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test
async def migration_minor_1_to_2(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test migration."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=FIXTURE_UUID,
        data={
            CONF_API_KEY: FIXTURE_USER_INPUT[CONF_TOKEN],
            CONF_HOST: FIXTURE_USER_INPUT[CONF_HOST],
            CONF_PORT: FIXTURE_USER_INPUT[CONF_PORT],
        },
        version=SystemBridgeConfigFlow.VERSION,
        minor_version=1,
    )

    with patch(
        "homeassistant.components.system_bridge.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        expect(len(mock_setup_entry.mock_calls)).to_equal(1)

    # Check that the version has been updated and the api_key has been moved to token
    expect(config_entry.version).to_equal(SystemBridgeConfigFlow.VERSION)
    expect(config_entry.minor_version).to_equal(SystemBridgeConfigFlow.MINOR_VERSION)
    expect(dict(config_entry.data)).to_equal(
        {
            CONF_API_KEY: FIXTURE_USER_INPUT[CONF_TOKEN],
            CONF_HOST: FIXTURE_USER_INPUT[CONF_HOST],
            CONF_PORT: FIXTURE_USER_INPUT[CONF_PORT],
            CONF_TOKEN: FIXTURE_USER_INPUT[CONF_TOKEN],
        }
    )
    expect(config_entry.state is ConfigEntryState.LOADED).to_be(True)


@test
async def migration_minor_future_version(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test migration."""
    config_entry_data = {
        CONF_API_KEY: FIXTURE_USER_INPUT[CONF_TOKEN],
        CONF_HOST: FIXTURE_USER_INPUT[CONF_HOST],
        CONF_PORT: FIXTURE_USER_INPUT[CONF_PORT],
        CONF_TOKEN: FIXTURE_USER_INPUT[CONF_TOKEN],
    }
    config_entry_version = SystemBridgeConfigFlow.VERSION
    config_entry_minor_version = SystemBridgeConfigFlow.MINOR_VERSION + 1
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=FIXTURE_UUID,
        data=config_entry_data,
        version=config_entry_version,
        minor_version=config_entry_minor_version,
    )

    with patch(
        "homeassistant.components.system_bridge.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        expect(len(mock_setup_entry.mock_calls)).to_equal(1)

    expect(config_entry.version).to_equal(config_entry_version)
    expect(config_entry.minor_version).to_equal(config_entry_minor_version)
    expect(dict(config_entry.data)).to_equal(config_entry_data)
    expect(config_entry.state is ConfigEntryState.LOADED).to_be(True)


@test
async def setup_timeout(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test setup with timeout error."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=FIXTURE_UUID,
        data=FIXTURE_USER_INPUT,
        version=SystemBridgeConfigFlow.VERSION,
        minor_version=SystemBridgeConfigFlow.MINOR_VERSION,
    )

    with patch(
        "systembridgeconnector.version.Version.check_supported",
        side_effect=TimeoutError,
    ):
        config_entry.add_to_hass(hass)
        result = await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        expect(result).to_be(False)
        expect(config_entry.state is ConfigEntryState.SETUP_RETRY).to_be(True)


@test
async def coordinator_get_data_timeout(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test coordinator handling timeout during get_data."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=FIXTURE_UUID,
        data=FIXTURE_USER_INPUT,
        version=SystemBridgeConfigFlow.VERSION,
        minor_version=SystemBridgeConfigFlow.MINOR_VERSION,
    )

    with (
        patch(
            "systembridgeconnector.version.Version.check_supported",
            return_value=True,
        ),
        patch(
            "homeassistant.components.system_bridge.coordinator.SystemBridgeDataUpdateCoordinator.async_get_data",
            side_effect=TimeoutError,
        ),
    ):
        config_entry.add_to_hass(hass)
        result = await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        expect(result).to_be(False)
        expect(config_entry.state is ConfigEntryState.SETUP_RETRY).to_be(True)
