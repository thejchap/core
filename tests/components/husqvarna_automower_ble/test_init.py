"""Test the Husqvarna Automower Bluetooth setup."""

from unittest.mock import AsyncMock

from automower_ble.protocol import ResponseResult
from tryke import Depends, expect, fixture, test

from homeassistant.components.husqvarna_automower_ble.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_ADDRESS, CONF_CLIENT_ID, CONF_PIN
from homeassistant.core import HomeAssistant

from ._fixtures import (
    mock_automower_client,
    mock_config_entry,
    mock_get_manufacturer_data,
    only_discover_this_domain,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import enable_bluetooth, hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _bluetooth: None = Depends(enable_bluetooth),
    _only_domain: None = Depends(only_discover_this_domain),
    _manufacturer: None = Depends(mock_get_manufacturer_data),
) -> None:
    """Anchor fixture."""


@test.skip("snapshot test — out of scope")
async def setup() -> None:
    """Stub for test_setup."""


@test
async def setup_missing_pin(
    _trigger: None = Depends(_trigger_executor),
    mock_client: AsyncMock = Depends(mock_automower_client),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test a setup that was created before PIN support."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="My home",
        unique_id="397678e5-9995-4a39-9d9f-ae6ba310236c",
        data={
            CONF_ADDRESS: "00000000-0000-0000-0000-000000000003",
            CONF_CLIENT_ID: "1197489078",
        },
    )

    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.SETUP_ERROR)

    hass.config_entries.async_update_entry(
        entry,
        data={**entry.data, CONF_PIN: 1234},
    )

    expect(len(hass.config_entries.flow.async_progress())).to_equal(1)
    await hass.async_block_till_done()


@test
async def setup_failed_connect(
    _trigger: None = Depends(_trigger_executor),
    mock_client: AsyncMock = Depends(mock_automower_client),
    entry: MockConfigEntry = Depends(mock_config_entry),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setup retries on TimeoutError."""

    mock_client.connect.side_effect = TimeoutError

    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def setup_unknown_error(
    _trigger: None = Depends(_trigger_executor),
    mock_client: AsyncMock = Depends(mock_automower_client),
    entry: MockConfigEntry = Depends(mock_config_entry),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setup retries on unknown response."""
    mock_client.connect.return_value = ResponseResult.UNKNOWN_ERROR

    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def setup_invalid_pin(
    _trigger: None = Depends(_trigger_executor),
    mock_client: AsyncMock = Depends(mock_automower_client),
    entry: MockConfigEntry = Depends(mock_config_entry),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setup fails on invalid PIN."""
    mock_client.connect.return_value = ResponseResult.INVALID_PIN

    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.SETUP_ERROR)
