"""Test the Aquacell init module."""

from datetime import datetime
from unittest.mock import AsyncMock, patch

from aioaquacell import AquacellApiException, AuthenticationFailed
from tryke import Depends, expect, fixture, test

from homeassistant.components.aquacell.const import (
    CONF_REFRESH_TOKEN,
    CONF_REFRESH_TOKEN_CREATION_TIME,
    DOMAIN,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import setup_integration
from ._fixtures import (
    mock_aquacell_api,
    mock_config_entry,
    mock_config_entry_expired,
    mock_config_entry_without_brand,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Force tryke to fully resolve hass."""
    return hass


@test
async def load_unload_entry(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _api: AsyncMock = Depends(mock_aquacell_api),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test load and unload entry."""
    await setup_integration(hass, mock_config_entry)
    entry = hass.config_entries.async_entries(DOMAIN)[0]

    expect(entry.state).to_be(ConfigEntryState.LOADED)

    await hass.config_entries.async_remove(entry.entry_id)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test
async def load_withoutbrand(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _api: AsyncMock = Depends(mock_aquacell_api),
    mock_config_entry_without_brand: MockConfigEntry = Depends(
        mock_config_entry_without_brand
    ),
) -> None:
    """Test load entry without brand."""
    await setup_integration(hass, mock_config_entry_without_brand)

    expect(mock_config_entry_without_brand.state).to_be(ConfigEntryState.LOADED)


@test
async def coordinator_update_valid_refresh_token(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_aquacell_api: AsyncMock = Depends(mock_aquacell_api),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test load with valid refresh token."""
    await setup_integration(hass, mock_config_entry)
    entry = hass.config_entries.async_entries(DOMAIN)[0]

    expect(entry.state).to_be(ConfigEntryState.LOADED)

    expect(len(mock_aquacell_api.authenticate.mock_calls)).to_equal(0)
    expect(len(mock_aquacell_api.authenticate_refresh.mock_calls)).to_equal(1)
    expect(len(mock_aquacell_api.get_all_softeners.mock_calls)).to_equal(1)


@test
async def coordinator_update_expired_refresh_token(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_aquacell_api: AsyncMock = Depends(mock_aquacell_api),
    mock_config_entry_expired: MockConfigEntry = Depends(mock_config_entry_expired),
) -> None:
    """Test load with expired refresh token."""
    mock_aquacell_api.authenticate.return_value = "new-refresh-token"

    now = datetime.now()
    with patch(
        "homeassistant.components.aquacell.coordinator.datetime"
    ) as datetime_mock:
        datetime_mock.now.return_value = now
        await setup_integration(hass, mock_config_entry_expired)

    entry = hass.config_entries.async_entries(DOMAIN)[0]

    expect(entry.state).to_be(ConfigEntryState.LOADED)

    expect(len(mock_aquacell_api.authenticate.mock_calls)).to_equal(1)
    expect(len(mock_aquacell_api.authenticate_refresh.mock_calls)).to_equal(0)
    expect(len(mock_aquacell_api.get_all_softeners.mock_calls)).to_equal(1)

    expect(entry.data[CONF_REFRESH_TOKEN]).to_equal("new-refresh-token")
    expect(entry.data[CONF_REFRESH_TOKEN_CREATION_TIME]).to_equal(now.timestamp())


@test.cases(
    test.case(
        "auth_failed",
        exception=AuthenticationFailed,
        expected_state=ConfigEntryState.SETUP_ERROR,
    ),
    test.case(
        "api_exception",
        exception=AquacellApiException,
        expected_state=ConfigEntryState.SETUP_RETRY,
    ),
)
async def load_exceptions(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_aquacell_api: AsyncMock = Depends(mock_aquacell_api),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    *,
    exception: Exception,
    expected_state: ConfigEntryState,
) -> None:
    """Test load with exceptions."""
    mock_aquacell_api.authenticate_refresh.side_effect = exception
    await setup_integration(hass, mock_config_entry)
    entry = hass.config_entries.async_entries(DOMAIN)[0]

    expect(entry.state).to_be(expected_state)
