"""Tests for the Aladdin Connect integration."""

import http
from unittest.mock import AsyncMock, patch

from aiohttp import ClientConnectionError, RequestInfo
from aiohttp.client_exceptions import ClientResponseError
from freezegun.api import FrozenDateTimeFactory
from tryke import Depends, expect, fixture, test

from homeassistant.components.aladdin_connect import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.config_entry_oauth2_flow import (
    ImplementationUnavailableError,
)

from . import init_integration
from ._fixtures import (
    mock_aladdin_connect_api,
    mock_config_entry,
    setup_credentials,
)

from tests.common import MockConfigEntry, async_fire_time_changed
from tests.hass_fixtures import (
    device_registry as device_registry_fx,
    entity_registry as entity_registry_fx,
    freezer as freezer_fx,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _credentials: None = Depends(setup_credentials),
    _aladdin: AsyncMock = Depends(mock_aladdin_connect_api),
) -> int:
    """Apply autouse-equivalent fixtures via this trigger."""
    return 0


@test
async def oauth_implementation_not_available(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test that unavailable OAuth implementation raises ConfigEntryNotReady."""
    config_entry.add_to_hass(hass)

    with patch(
        "homeassistant.helpers.config_entry_oauth2_flow.async_get_config_entry_implementation",
        side_effect=ImplementationUnavailableError,
    ):
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def setup_entry(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test a successful setup entry."""
    await init_integration(hass, config_entry)
    expect(config_entry.state).to_be(ConfigEntryState.LOADED)


@test
async def unload_entry(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test a successful unload entry."""
    await init_integration(hass, config_entry)
    expect(config_entry.state).to_be(ConfigEntryState.LOADED)

    await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()
    expect(config_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test.cases(
    test.case(
        "auth_failure",
        status=http.HTTPStatus.UNAUTHORIZED,
        expected_state=ConfigEntryState.SETUP_ERROR,
    ),
    test.case(
        "server_error",
        status=http.HTTPStatus.INTERNAL_SERVER_ERROR,
        expected_state=ConfigEntryState.SETUP_RETRY,
    ),
)
async def setup_entry_token_error(
    status: http.HTTPStatus,
    expected_state: ConfigEntryState,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test setup entry fails when token validation fails."""
    with patch(
        "homeassistant.helpers.config_entry_oauth2_flow.OAuth2Session.async_ensure_token_valid",
        side_effect=ClientResponseError(
            RequestInfo("", "POST", {}, ""), None, status=status
        ),
    ):
        await init_integration(hass, config_entry)

    expect(config_entry.state).to_be(expected_state)


@test
async def setup_entry_token_connection_error(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test setup entry retries when token validation has a connection error."""
    with patch(
        "homeassistant.helpers.config_entry_oauth2_flow.OAuth2Session.async_ensure_token_valid",
        side_effect=ClientConnectionError(),
    ):
        await init_integration(hass, config_entry)

    expect(config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test.cases(
    test.case(
        "auth_failure",
        status=http.HTTPStatus.UNAUTHORIZED,
        expected_state=ConfigEntryState.SETUP_ERROR,
    ),
    test.case(
        "server_error",
        status=http.HTTPStatus.INTERNAL_SERVER_ERROR,
        expected_state=ConfigEntryState.SETUP_RETRY,
    ),
)
async def setup_entry_api_error(
    status: http.HTTPStatus,
    expected_state: ConfigEntryState,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    aladdin_api: AsyncMock = Depends(mock_aladdin_connect_api),
) -> None:
    """Test setup entry fails when API call fails."""
    aladdin_api.get_doors.side_effect = ClientResponseError(
        RequestInfo("", "GET", {}, ""), None, status=status
    )
    await init_integration(hass, config_entry)
    expect(config_entry.state).to_be(expected_state)


@test
async def setup_entry_api_connection_error(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    aladdin_api: AsyncMock = Depends(mock_aladdin_connect_api),
) -> None:
    """Test setup entry retries when API has a connection error."""
    aladdin_api.get_doors.side_effect = ClientConnectionError()
    await init_integration(hass, config_entry)
    expect(config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def remove_stale_devices(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test stale devices are removed on setup."""
    config_entry.add_to_hass(hass)

    device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={(DOMAIN, "stale_device_id")},
    )
    device_entries = dr.async_entries_for_config_entry(
        device_registry, config_entry.entry_id
    )
    expect(len(device_entries)).to_equal(1)

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    device_entries = dr.async_entries_for_config_entry(
        device_registry, config_entry.entry_id
    )
    expect(len(device_entries)).to_equal(1)
    expect(device_entries[0].identifiers).to_equal({(DOMAIN, "test_device_id-1")})


@test
async def dynamic_devices(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    aladdin_api: AsyncMock = Depends(mock_aladdin_connect_api),
    freezer: FrozenDateTimeFactory = Depends(freezer_fx),
) -> None:
    """Test new devices are automatically discovered on coordinator refresh."""
    await init_integration(hass, config_entry)

    device_entries = dr.async_entries_for_config_entry(
        device_registry, config_entry.entry_id
    )
    expect(len(device_entries)).to_equal(1)
    expect(hass.states.get("cover.test_door") is not None).to_be(True)

    mock_door_2 = AsyncMock()
    mock_door_2.device_id = "test_device_id_2"
    mock_door_2.door_number = 1
    mock_door_2.name = "Test Door 2"
    mock_door_2.status = "open"
    mock_door_2.link_status = "connected"
    mock_door_2.battery_level = 80
    mock_door_2.unique_id = f"{mock_door_2.device_id}-{mock_door_2.door_number}"

    existing_door = aladdin_api.get_doors.return_value[0]
    aladdin_api.get_doors.return_value = [existing_door, mock_door_2]

    freezer.tick(15)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    device_entries = dr.async_entries_for_config_entry(
        device_registry, config_entry.entry_id
    )
    expect(len(device_entries)).to_equal(2)

    expect(hass.states.get("cover.test_door_2") is not None).to_be(True)
