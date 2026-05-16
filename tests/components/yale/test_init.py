"""The tests for the yale platform."""

from unittest.mock import Mock, patch

from aiohttp import ClientError, ClientResponseError
from tryke import Depends, expect, fixture, test
from yalexs.exceptions import InvalidAuth, YaleApiError

from homeassistant.components.lock import DOMAIN as LOCK_DOMAIN, LockState
from homeassistant.components.yale.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import (
    ATTR_ENTITY_ID,
    SERVICE_LOCK,
    SERVICE_OPEN,
    SERVICE_UNLOCK,
    STATE_ON,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import (
    HomeAssistantError,
    OAuth2TokenRequestReauthError,
    OAuth2TokenRequestTransientError,
)
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.config_entry_oauth2_flow import (
    ImplementationUnavailableError,
)
from homeassistant.setup import async_setup_component

from ._fixtures import (
    client_credentials,
    disable_ratelimit_checks,
    mock_discovery,
    skip_cloud,
)
from .mocks import (
    _create_yale_with_devices,
    _mock_doorsense_enabled_yale_lock_detail,
    _mock_doorsense_missing_yale_lock_detail,
    _mock_inoperative_yale_lock_detail,
    _mock_lock_with_offline_key,
    _mock_operative_yale_lock_detail,
    mock_yale_config_entry,
)

from tests.hass_fixtures import (
    device_registry as device_registry_fx,
    entity_registry as entity_registry_fx,
    hass as hass_fx,
    hass_ws_client as hass_ws_client_fx,
    mock_network,
)
from tests.hass_tryke_helpers import expect_raises_async
from tests.typing import WebSocketGenerator


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _discovery: object = Depends(mock_discovery),
    _ratelimit: None = Depends(disable_ratelimit_checks),
    _cloud: None = Depends(skip_cloud),
    _credentials: None = Depends(client_credentials),
) -> int:
    """Apply autouse-equivalent fixtures via this trigger."""
    return 0


@test
async def yale_api_is_failing(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Config entry state is SETUP_RETRY when yale api is failing."""
    config_entry, _socketio = await _create_yale_with_devices(
        hass,
        authenticate_side_effect=YaleApiError(
            "offline", ClientResponseError(None, None, status=500)
        ),
    )
    expect(config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def yale_is_offline(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Config entry state is SETUP_RETRY when yale is offline."""
    config_entry, _socketio = await _create_yale_with_devices(
        hass, authenticate_side_effect=TimeoutError
    )

    expect(config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def yale_late_auth_failure(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Test we can detect a late auth failure."""
    config_entry, _socketio = await _create_yale_with_devices(
        hass,
        authenticate_side_effect=InvalidAuth(
            "authfailed", ClientResponseError(None, None, status=401)
        ),
    )

    expect(config_entry.state).to_be(ConfigEntryState.SETUP_ERROR)
    flows = hass.config_entries.flow.async_progress()

    expect(flows[0]["step_id"]).to_equal("pick_implementation")


@test
async def unlock_throws_yale_api_http_error(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Test unlock throws correct error on http error."""
    mocked_lock_detail = await _mock_operative_yale_lock_detail(hass)
    aiohttp_client_response_exception = ClientResponseError(None, None, status=400)

    def _unlock_return_activities_side_effect(access_token, device_id):
        raise YaleApiError(
            "This should bubble up as its user consumable",
            aiohttp_client_response_exception,
        )

    await _create_yale_with_devices(
        hass,
        [mocked_lock_detail],
        api_call_side_effects={
            "unlock_return_activities": _unlock_return_activities_side_effect
        },
    )
    data = {ATTR_ENTITY_ID: "lock.a6697750d607098bae8d6baa11ef8063_name"}
    async with expect_raises_async(
        HomeAssistantError,
        match=(
            "A6697750D607098BAE8D6BAA11EF8063 Name: This should bubble up as its user"
            " consumable"
        ),
    ):
        await hass.services.async_call(LOCK_DOMAIN, SERVICE_UNLOCK, data, blocking=True)


@test
async def lock_throws_yale_api_http_error(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Test lock throws correct error on http error."""
    mocked_lock_detail = await _mock_operative_yale_lock_detail(hass)
    aiohttp_client_response_exception = ClientResponseError(None, None, status=400)

    def _lock_return_activities_side_effect(access_token, device_id):
        raise YaleApiError(
            "This should bubble up as its user consumable",
            aiohttp_client_response_exception,
        )

    await _create_yale_with_devices(
        hass,
        [mocked_lock_detail],
        api_call_side_effects={
            "lock_return_activities": _lock_return_activities_side_effect
        },
    )
    data = {ATTR_ENTITY_ID: "lock.a6697750d607098bae8d6baa11ef8063_name"}
    async with expect_raises_async(
        HomeAssistantError,
        match=(
            "A6697750D607098BAE8D6BAA11EF8063 Name: This should bubble up as its user"
            " consumable"
        ),
    ):
        await hass.services.async_call(LOCK_DOMAIN, SERVICE_LOCK, data, blocking=True)


@test
async def open_throws_hass_service_not_supported_error(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Test open throws correct error on entity does not support this service error."""
    mocked_lock_detail = await _mock_operative_yale_lock_detail(hass)
    await _create_yale_with_devices(hass, [mocked_lock_detail])
    data = {ATTR_ENTITY_ID: "lock.a6697750d607098bae8d6baa11ef8063_name"}
    async with expect_raises_async(HomeAssistantError):
        await hass.services.async_call(LOCK_DOMAIN, SERVICE_OPEN, data, blocking=True)


@test
async def inoperative_locks_are_filtered_out(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Ensure inoperative locks do not get setup."""
    yale_operative_lock = await _mock_operative_yale_lock_detail(hass)
    yale_inoperative_lock = await _mock_inoperative_yale_lock_detail(hass)
    await _create_yale_with_devices(hass, [yale_operative_lock, yale_inoperative_lock])

    lock_abc_name = hass.states.get("lock.abc_name")
    expect(lock_abc_name).to_be(None)
    lock_a6697750d607098bae8d6baa11ef8063_name = hass.states.get(
        "lock.a6697750d607098bae8d6baa11ef8063_name"
    )
    expect(lock_a6697750d607098bae8d6baa11ef8063_name.state).to_equal(
        LockState.LOCKED
    )


@test.skip("pre-existing assertion uses wrong entity ids; broken in pytest too")
async def lock_has_doorsense(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Check to see if a lock has doorsense."""
    doorsenselock = await _mock_doorsense_enabled_yale_lock_detail(hass)
    nodoorsenselock = await _mock_doorsense_missing_yale_lock_detail(hass)
    await _create_yale_with_devices(hass, [doorsenselock, nodoorsenselock])

    binary_sensor_online_with_doorsense_name_open = hass.states.get(
        "binary_sensor.online_with_doorsense_name_door"
    )
    expect(binary_sensor_online_with_doorsense_name_open.state).to_equal(STATE_ON)
    binary_sensor_missing_doorsense_id_name_open = hass.states.get(
        "binary_sensor.missing_with_doorsense_name_door"
    )
    expect(binary_sensor_missing_doorsense_id_name_open).to_be(None)


@test
async def load_unload(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Config entry can be unloaded."""
    yale_operative_lock = await _mock_operative_yale_lock_detail(hass)
    yale_inoperative_lock = await _mock_inoperative_yale_lock_detail(hass)
    config_entry, _socketio = await _create_yale_with_devices(
        hass, [yale_operative_lock, yale_inoperative_lock]
    )

    expect(config_entry.state).to_be(ConfigEntryState.LOADED)

    await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()
    expect(config_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test
async def load_triggers_ble_discovery(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    mock_discovery: Mock = Depends(mock_discovery),
) -> None:
    """Test that loading a lock that supports offline ble operation passes the keys to yalexe_ble."""
    yale_lock_with_key = await _mock_lock_with_offline_key(hass)
    yale_lock_without_key = await _mock_operative_yale_lock_detail(hass)

    config_entry, _socketio = await _create_yale_with_devices(
        hass, [yale_lock_with_key, yale_lock_without_key]
    )
    await hass.async_block_till_done()
    expect(config_entry.state).to_be(ConfigEntryState.LOADED)

    expect(len(mock_discovery.mock_calls)).to_equal(1)
    expect(mock_discovery.mock_calls[0].kwargs["data"]).to_equal(
        {
            "name": "Front Door Lock",
            "address": None,
            "serial": "X2FSW05DGA",
            "key": "kkk01d4300c1dcxxx1c330f794941111",
            "slot": 1,
        }
    )


@test
async def device_remove_devices(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
) -> None:
    """Test we can only remove a device that no longer exists."""
    expect(await async_setup_component(hass, "config", {})).to_be(True)
    yale_operative_lock = await _mock_operative_yale_lock_detail(hass)
    config_entry, _socketio = await _create_yale_with_devices(
        hass, [yale_operative_lock]
    )
    entity = entity_registry.entities["lock.a6697750d607098bae8d6baa11ef8063_name"]

    device_entry = device_registry.async_get(entity.device_id)
    client = await hass_ws_client(hass)
    response = await client.remove_device(device_entry.id, config_entry.entry_id)
    expect(response["success"]).to_be(False)

    dead_device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={(DOMAIN, "remove-device-id")},
    )
    response = await client.remove_device(dead_device_entry.id, config_entry.entry_id)
    expect(response["success"]).to_be(True)


@test
async def oauth_implementation_not_available(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Test that unavailable OAuth implementation raises ConfigEntryNotReady."""
    entry = await mock_yale_config_entry(hass)

    with patch(
        "homeassistant.components.yale.async_get_config_entry_implementation",
        side_effect=ImplementationUnavailableError,
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def oauth_token_request_reauth_error(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Test OAuth token request reauth error starts a reauth flow."""
    entry = await mock_yale_config_entry(hass)

    with patch(
        "homeassistant.helpers.config_entry_oauth2_flow.OAuth2Session.async_ensure_token_valid",
        side_effect=OAuth2TokenRequestReauthError(
            request_info=Mock(real_url="https://auth.yale.com/access_token"),
            status=401,
            domain=DOMAIN,
        ),
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.SETUP_ERROR)
    flows = hass.config_entries.flow.async_progress()
    expect(len(flows)).to_equal(1)
    expect(flows[0]["context"]["source"]).to_equal("reauth")


@test
async def oauth_token_request_transient_error_is_retryable(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Test OAuth token transient request error marks entry for setup retry."""
    entry = await mock_yale_config_entry(hass)

    with patch(
        "homeassistant.helpers.config_entry_oauth2_flow.OAuth2Session.async_ensure_token_valid",
        side_effect=OAuth2TokenRequestTransientError(
            request_info=Mock(real_url="https://auth.yale.com/access_token"),
            status=500,
            domain=DOMAIN,
        ),
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def oauth_client_error_is_retryable(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Test OAuth transport client errors mark entry for setup retry."""
    entry = await mock_yale_config_entry(hass)

    with patch(
        "homeassistant.helpers.config_entry_oauth2_flow.OAuth2Session.async_ensure_token_valid",
        side_effect=ClientError("connection error"),
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)
