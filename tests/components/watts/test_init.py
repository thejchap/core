"""Test the Watts Vision integration initialization."""

from datetime import timedelta
from unittest.mock import AsyncMock

from aiohttp import ClientError
from freezegun.api import FrozenDateTimeFactory
from tryke import Depends, expect, fixture, test
from visionpluspython.exceptions import (
    WattsVisionAuthError,
    WattsVisionConnectionError,
    WattsVisionDeviceError,
    WattsVisionError,
    WattsVisionTimeoutError,
)
from visionpluspython.models import create_device_from_data

from homeassistant.components.climate import (
    ATTR_TEMPERATURE,
    DOMAIN as CLIMATE_DOMAIN,
    SERVICE_SET_TEMPERATURE,
)
from homeassistant.components.watts.const import (
    DISCOVERY_INTERVAL_MINUTES,
    DOMAIN,
    FAST_POLLING_INTERVAL_SECONDS,
    OAUTH2_TOKEN,
    UPDATE_INTERVAL_SECONDS,
)
from homeassistant.config_entries import SOURCE_REAUTH, ConfigEntryState
from homeassistant.const import ATTR_ENTITY_ID, STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from . import setup_integration
from ._fixtures import (
    mock_config_entry as mock_config_entry_fx,
    mock_watts_client as mock_watts_client_fx,
    setup_credentials as setup_credentials_fx,
    skip_cloud as skip_cloud_fx,
)

from tests.common import MockConfigEntry, async_fire_time_changed
from tests.hass_fixtures import (
    aioclient_mock as aioclient_mock_fx,
    device_registry as device_registry_fx,
    freezer as freezer_fx,
    hass as hass_fx,
    mock_network,
)
from tests.test_util.aiohttp import AiohttpClientMocker


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    return 0


@test
async def setup_entry_success(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    _skip_cloud: None = Depends(skip_cloud_fx),
    _creds: None = Depends(setup_credentials_fx),
    mock_watts_client: AsyncMock = Depends(mock_watts_client_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test successful setup and unload of entry."""
    await setup_integration(hass, mock_config_entry)

    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)

    mock_watts_client.discover_devices.assert_called_once()

    unload_result = await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(unload_result).to_be(True)
    expect(mock_config_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test
async def setup_entry_auth_failed(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    _skip_cloud: None = Depends(skip_cloud_fx),
    _creds: None = Depends(setup_credentials_fx),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
) -> None:
    """Test setup with authentication failure."""
    config_entry = MockConfigEntry(
        domain="watts",
        unique_id="test-device-id",
        data={
            "device_id": "test-device-id",
            "auth_implementation": "watts",
            "token": {
                "access_token": "test-access-token",
                "refresh_token": "test-refresh-token",
                "expires_at": 0,
            },
        },
    )
    config_entry.add_to_hass(hass)

    aioclient_mock.post(OAUTH2_TOKEN, status=401)

    result = await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(result).to_be(False)
    expect(config_entry.state).to_be(ConfigEntryState.SETUP_ERROR)


@test
async def setup_entry_not_ready(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    _skip_cloud: None = Depends(skip_cloud_fx),
    _creds: None = Depends(setup_credentials_fx),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
) -> None:
    """Test setup when network is temporarily unavailable."""
    config_entry = MockConfigEntry(
        domain="watts",
        unique_id="test-device-id",
        data={
            "device_id": "test-device-id",
            "auth_implementation": "watts",
            "token": {
                "access_token": "test-access-token",
                "refresh_token": "test-refresh-token",
                "expires_at": 0,
            },
        },
    )
    config_entry.add_to_hass(hass)

    aioclient_mock.post(OAUTH2_TOKEN, exc=ClientError("Connection timeout"))

    result = await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(result).to_be(False)
    expect(config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def setup_entry_hub_coordinator_update_failed(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    _skip_cloud: None = Depends(skip_cloud_fx),
    _creds: None = Depends(setup_credentials_fx),
    mock_watts_client: AsyncMock = Depends(mock_watts_client_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test setup when hub coordinator update fails."""
    mock_watts_client.discover_devices.side_effect = ConnectionError("API error")

    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(result).to_be(False)
    expect(mock_config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def setup_entry_server_error_5xx(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    _skip_cloud: None = Depends(skip_cloud_fx),
    _creds: None = Depends(setup_credentials_fx),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
) -> None:
    """Test setup when server returns error."""
    config_entry = MockConfigEntry(
        domain="watts",
        unique_id="test-device-id",
        data={
            "device_id": "test-device-id",
            "auth_implementation": "watts",
            "token": {
                "access_token": "test-access-token",
                "refresh_token": "test-refresh-token",
                "expires_at": 0,
            },
        },
    )
    config_entry.add_to_hass(hass)

    aioclient_mock.post(OAUTH2_TOKEN, status=500)

    result = await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(result).to_be(False)
    expect(config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test.cases(
    test.case(
        "auth_error",
        exception=WattsVisionAuthError("Auth failed"),
        expected_state=ConfigEntryState.SETUP_ERROR,
    ),
    test.case(
        "connection_error",
        exception=WattsVisionConnectionError("Connection lost"),
        expected_state=ConfigEntryState.SETUP_RETRY,
    ),
    test.case(
        "timeout_error",
        exception=WattsVisionTimeoutError("Request timeout"),
        expected_state=ConfigEntryState.SETUP_RETRY,
    ),
    test.case(
        "device_error",
        exception=WattsVisionDeviceError("Device error"),
        expected_state=ConfigEntryState.SETUP_RETRY,
    ),
    test.case(
        "api_error",
        exception=WattsVisionError("API error"),
        expected_state=ConfigEntryState.SETUP_RETRY,
    ),
    test.case(
        "value_error",
        exception=ValueError("Value error"),
        expected_state=ConfigEntryState.SETUP_RETRY,
    ),
)
async def setup_entry_discover_devices_errors(
    exception: Exception,
    expected_state: ConfigEntryState,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    _skip_cloud: None = Depends(skip_cloud_fx),
    _creds: None = Depends(setup_credentials_fx),
    mock_watts_client: AsyncMock = Depends(mock_watts_client_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test setup errors during device discovery."""
    mock_watts_client.discover_devices.side_effect = exception

    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(result).to_be(False)
    expect(mock_config_entry.state).to_be(expected_state)


@test
async def dynamic_device_creation(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    _skip_cloud: None = Depends(skip_cloud_fx),
    _creds: None = Depends(setup_credentials_fx),
    mock_watts_client: AsyncMock = Depends(mock_watts_client_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    freezer: FrozenDateTimeFactory = Depends(freezer_fx),
) -> None:
    """Test new devices are created dynamically."""
    await setup_integration(hass, mock_config_entry)

    expect(
        device_registry.async_get_device(identifiers={(DOMAIN, "thermostat_123")})
    ).to_be_truthy()
    expect(
        device_registry.async_get_device(identifiers={(DOMAIN, "thermostat_456")})
    ).to_be_truthy()
    expect(
        device_registry.async_get_device(identifiers={(DOMAIN, "thermostat_789")})
    ).to_be(None)

    new_device_data = {
        "deviceId": "thermostat_789",
        "deviceName": "Kitchen Thermostat",
        "deviceType": "thermostat",
        "interface": "homeassistant.components.THERMOSTAT",
        "roomName": "Kitchen",
        "isOnline": True,
        "currentTemperature": 21.0,
        "setpoint": 20.0,
        "thermostatMode": "Comfort",
        "minAllowedTemperature": 5.0,
        "maxAllowedTemperature": 30.0,
        "temperatureUnit": "C",
        "availableThermostatModes": ["Program", "Eco", "Comfort", "Off"],
    }
    new_device = create_device_from_data(new_device_data)

    current_devices = list(mock_watts_client.discover_devices.return_value)
    mock_watts_client.discover_devices.return_value = [*current_devices, new_device]

    freezer.tick(timedelta(minutes=DISCOVERY_INTERVAL_MINUTES))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    new_device_entry = device_registry.async_get_device(
        identifiers={(DOMAIN, "thermostat_789")}
    )
    expect(new_device_entry).not_.to_be(None)
    expect(new_device_entry.name).to_equal("Kitchen Thermostat")

    state = hass.states.get("climate.kitchen_thermostat")
    expect(state).not_.to_be(None)


@test
async def stale_device_removal(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    _skip_cloud: None = Depends(skip_cloud_fx),
    _creds: None = Depends(setup_credentials_fx),
    mock_watts_client: AsyncMock = Depends(mock_watts_client_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    freezer: FrozenDateTimeFactory = Depends(freezer_fx),
) -> None:
    """Test stale devices are removed dynamically."""
    await setup_integration(hass, mock_config_entry)

    device_123 = device_registry.async_get_device(
        identifiers={(DOMAIN, "thermostat_123")}
    )
    device_456 = device_registry.async_get_device(
        identifiers={(DOMAIN, "thermostat_456")}
    )
    expect(device_123).not_.to_be(None)
    expect(device_456).not_.to_be(None)

    current_devices = list(mock_watts_client.discover_devices.return_value)

    mock_watts_client.discover_devices.return_value = [
        d for d in current_devices if d.device_id != "thermostat_456"
    ]

    freezer.tick(timedelta(minutes=DISCOVERY_INTERVAL_MINUTES))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    device_456_after_removal = device_registry.async_get_device(
        identifiers={(DOMAIN, "thermostat_456")}
    )
    expect(device_456_after_removal).to_be(None)


@test.cases(
    test.case(
        "auth_error",
        exception=WattsVisionAuthError("expired"),
        has_reauth_flow=True,
    ),
    test.case(
        "connection_error",
        exception=WattsVisionConnectionError("lost"),
        has_reauth_flow=False,
    ),
)
async def hub_coordinator_update_errors(
    exception: Exception,
    has_reauth_flow: bool,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    _skip_cloud: None = Depends(skip_cloud_fx),
    _creds: None = Depends(setup_credentials_fx),
    mock_watts_client: AsyncMock = Depends(mock_watts_client_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
    freezer: FrozenDateTimeFactory = Depends(freezer_fx),
) -> None:
    """Test hub coordinator handles errors during regular update."""
    await setup_integration(hass, mock_config_entry)

    state = hass.states.get("climate.living_room_thermostat")
    expect(state).not_.to_be(None)
    expect(state.state).not_.to_equal(STATE_UNAVAILABLE)

    mock_watts_client.get_devices_report.side_effect = exception

    freezer.tick(timedelta(seconds=UPDATE_INTERVAL_SECONDS))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get("climate.living_room_thermostat")
    expect(state).not_.to_be(None)
    expect(state.state).not_.to_equal(STATE_UNAVAILABLE)

    expect(
        any(mock_config_entry.async_get_active_flows(hass, {SOURCE_REAUTH}))
    ).to_be(has_reauth_flow)


@test
async def device_coordinator_refresh_error(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    _skip_cloud: None = Depends(skip_cloud_fx),
    _creds: None = Depends(setup_credentials_fx),
    mock_watts_client: AsyncMock = Depends(mock_watts_client_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
    freezer: FrozenDateTimeFactory = Depends(freezer_fx),
) -> None:
    """Test device coordinator handles refresh error."""
    await setup_integration(hass, mock_config_entry)

    state = hass.states.get("climate.living_room_thermostat")
    expect(state).not_.to_be(None)
    expect(state.state).not_.to_equal(STATE_UNAVAILABLE)

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_TEMPERATURE,
        {
            ATTR_ENTITY_ID: "climate.living_room_thermostat",
            ATTR_TEMPERATURE: 23.5,
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    mock_watts_client.get_device.side_effect = WattsVisionConnectionError("lost")

    freezer.tick(timedelta(seconds=FAST_POLLING_INTERVAL_SECONDS))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get("climate.living_room_thermostat")
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(STATE_UNAVAILABLE)
