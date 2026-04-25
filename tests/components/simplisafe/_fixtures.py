"""Tryke fixtures for the SimpliSafe integration."""

from unittest.mock import AsyncMock, Mock, patch

from simplipy.system.v3 import SystemV3
from tryke import Depends, fixture

from homeassistant.components.simplisafe.const import DOMAIN
from homeassistant.const import CONF_CODE, CONF_TOKEN, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util.json import JsonObjectType

from .common import REFRESH_TOKEN, USER_ID, USERNAME

from tests.common import MockConfigEntry, load_json_object_fixture
from tests.hass_fixtures import hass as hass_fixture

SYSTEM_ID = 12345


@fixture
def data_latest_event() -> JsonObjectType:
    """Define latest event data."""
    return load_json_object_fixture("latest_event_data.json", "simplisafe")


@fixture
def data_sensor() -> JsonObjectType:
    """Define sensor data."""
    return load_json_object_fixture("sensor_data.json", "simplisafe")


@fixture
def data_settings() -> JsonObjectType:
    """Define settings data."""
    return load_json_object_fixture("settings_data.json", "simplisafe")


@fixture
def data_subscription() -> JsonObjectType:
    """Define subscription data."""
    data = load_json_object_fixture("subscription_data.json", "simplisafe")
    return {SYSTEM_ID: data}  # type: ignore[return-value]


@fixture
def system_v3(
    latest_event: JsonObjectType = Depends(data_latest_event),
    sensor: JsonObjectType = Depends(data_sensor),
    settings: JsonObjectType = Depends(data_settings),
    subscription: JsonObjectType = Depends(data_subscription),
) -> SystemV3:
    """Define a simplisafe-python V3 System object."""
    system = SystemV3(Mock(subscription_data=subscription), SYSTEM_ID)
    system.async_get_latest_event = AsyncMock(return_value=latest_event)
    system.sensor_data = sensor
    system.settings_data = settings
    system.generate_device_objects()
    system.async_update = AsyncMock(return_value=None)
    return system


@fixture
def websocket() -> Mock:
    """Define a simplisafe-python websocket object."""
    return Mock(
        async_connect=AsyncMock(),
        async_disconnect=AsyncMock(),
        async_listen=AsyncMock(),
    )


@fixture
def api(
    subscription: JsonObjectType = Depends(data_subscription),
    system: SystemV3 = Depends(system_v3),
    ws: Mock = Depends(websocket),
) -> Mock:
    """Define a simplisafe-python API object."""
    return Mock(
        async_get_systems=AsyncMock(return_value={SYSTEM_ID: system}),
        refresh_token=REFRESH_TOKEN,
        subscription_data=subscription,
        user_id=USER_ID,
        websocket=ws,
    )


@fixture
def config() -> dict[str, str]:
    """Define config entry data config."""
    return {
        CONF_TOKEN: REFRESH_TOKEN,
        CONF_USERNAME: USERNAME,
    }


@fixture
def config_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    cfg: dict[str, str] = Depends(config),
) -> MockConfigEntry:
    """Define a config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id=USER_ID, data=cfg, options={CONF_CODE: "1234"}
    )
    entry.add_to_hass(hass)
    return entry


@fixture
def config_entry_other_id(
    hass: HomeAssistant = Depends(hass_fixture),
    cfg: dict[str, str] = Depends(config),
) -> MockConfigEntry:
    """Define a config entry with a different unique id."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="some_other_id",
        data=cfg,
        options={CONF_CODE: "1234"},
    )
    entry.add_to_hass(hass)
    return entry


@fixture
def patch_simplisafe_api(
    api_mock: Mock = Depends(api),
    ws: Mock = Depends(websocket),
):
    """Patch the SimpliSafe API creation methods."""
    with (
        patch(
            "homeassistant.components.simplisafe.config_flow.API.async_from_auth",
            return_value=api_mock,
        ),
        patch(
            "homeassistant.components.simplisafe.API.async_from_auth",
            return_value=api_mock,
        ),
        patch(
            "homeassistant.components.simplisafe.API.async_from_refresh_token",
            return_value=api_mock,
        ),
        patch(
            "homeassistant.components.simplisafe.SimpliSafe._async_start_websocket_if_needed",
        ),
    ):
        api_mock.websocket = ws
        yield


@fixture
async def setup_simplisafe(
    hass: HomeAssistant = Depends(hass_fixture),
    _api: Mock = Depends(api),
    cfg: dict[str, str] = Depends(config),
    _patched: None = Depends(patch_simplisafe_api),
) -> None:
    """Define a fixture to set up SimpliSafe for config flow tests."""
    assert await async_setup_component(hass, DOMAIN, cfg)
    await hass.async_block_till_done()
