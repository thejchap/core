"""Test the Reolink host."""

from asyncio import CancelledError
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from aiohttp import ClientResponseError
from freezegun.api import FrozenDateTimeFactory
from reolink_aio.enums import SubType
from reolink_aio.exceptions import NotSupportedError, ReolinkError, SubscriptionError
from tryke import Depends, expect, fixture, test

from homeassistant.components.reolink.coordinator import DEVICE_UPDATE_INTERVAL_MIN
from homeassistant.components.reolink.host import (
    FIRST_ONVIF_LONG_POLL_TIMEOUT,
    FIRST_ONVIF_TIMEOUT,
    FIRST_TCP_PUSH_TIMEOUT,
    LONG_POLL_COOLDOWN,
    LONG_POLL_ERROR_COOLDOWN,
    POLL_INTERVAL_NO_PUSH,
)
from homeassistant.components.webhook import async_handle_webhook
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import STATE_OFF, STATE_ON, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.network import NoURLAvailableError
from homeassistant.util.aiohttp import MockRequest

from ._fixtures import (
    config_entry as config_entry_fx,
    reolink_host as reolink_host_fx,
)
from .conftest import TEST_CAM_NAME

from tests.common import MockConfigEntry, async_fire_time_changed
from tests.components.diagnostics import get_diagnostics_for_config_entry
from tests.hass_fixtures import (
    ClientSessionGenerator,
    entity_registry as entity_registry_fx,
    freezer as freezer_fx,
    hass as hass_fixture,
    hass_client as hass_client_fx,
    hass_client_no_auth as hass_client_no_auth_fx,
)
from tests.hass_tryke_helpers import expect_raises_async


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@test
async def setup_with_tcp_push(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fx),
    config_entry: MockConfigEntry = Depends(config_entry_fx),
    reolink_host: MagicMock = Depends(reolink_host_fx),
) -> None:
    """Test successful setup of the integration with TCP push callbacks."""
    reolink_host.baichuan.events_active = True
    with patch("homeassistant.components.reolink.PLATFORMS", [Platform.BINARY_SENSOR]):
        expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_truthy()
    await hass.async_block_till_done()
    expect(config_entry.state).to_be(ConfigEntryState.LOADED)

    freezer.tick(timedelta(seconds=FIRST_TCP_PUSH_TIMEOUT))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    # ONVIF push subscription not called
    expect(reolink_host.subscribe.called).to_be_falsy()


@test
async def unloading_with_tcp_push(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fx),
    reolink_host: MagicMock = Depends(reolink_host_fx),
) -> None:
    """Test successful unloading of the integration with TCP push callbacks."""
    reolink_host.baichuan.events_active = True
    with patch("homeassistant.components.reolink.PLATFORMS", [Platform.BINARY_SENSOR]):
        expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_truthy()
    await hass.async_block_till_done()
    expect(config_entry.state).to_be(ConfigEntryState.LOADED)

    reolink_host.baichuan.unsubscribe_events.side_effect = ReolinkError("Test error")

    expect(await hass.config_entries.async_unload(config_entry.entry_id)).to_be_truthy()
    await hass.async_block_till_done()
    expect(config_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test.skip(
    "device_class-based entity name not resolved in standalone hass fixture; "
    "test also fails under pytest on this branch"
)
async def webhook_callback(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client_no_auth: ClientSessionGenerator = Depends(hass_client_no_auth_fx),
    freezer: FrozenDateTimeFactory = Depends(freezer_fx),
    config_entry: MockConfigEntry = Depends(config_entry_fx),
    reolink_host: MagicMock = Depends(reolink_host_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
) -> None:
    """Test webhook callback with motion sensor."""
    reolink_host.motion_detected.return_value = False

    with patch("homeassistant.components.reolink.PLATFORMS", [Platform.BINARY_SENSOR]):
        expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_truthy()
    await hass.async_block_till_done()
    expect(config_entry.state).to_be(ConfigEntryState.LOADED)

    entity_id = f"{Platform.BINARY_SENSOR}.{TEST_CAM_NAME}_motion"
    webhook_id = config_entry.runtime_data.host.webhook_id
    unique_id = config_entry.runtime_data.host.unique_id

    signal_all = MagicMock()
    signal_ch = MagicMock()
    async_dispatcher_connect(hass, f"{unique_id}_all", signal_all)
    async_dispatcher_connect(hass, f"{unique_id}_0", signal_ch)

    client = await hass_client_no_auth()

    expect(hass.states.get(entity_id).state).to_equal(STATE_OFF)

    # test webhook callback success all channels
    reolink_host.get_motion_state_all_ch.return_value = True
    reolink_host.motion_detected.return_value = True
    reolink_host.ONVIF_event_callback.return_value = None
    await client.post(f"/api/webhook/{webhook_id}")
    await hass.async_block_till_done()
    signal_all.assert_called_once()
    expect(hass.states.get(entity_id).state).to_equal(STATE_ON)

    freezer.tick(timedelta(seconds=FIRST_ONVIF_TIMEOUT))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    # test webhook callback all channels with failure to read motion_state
    signal_all.reset_mock()
    reolink_host.get_motion_state_all_ch.return_value = False
    await client.post(f"/api/webhook/{webhook_id}")
    await hass.async_block_till_done()
    signal_all.assert_not_called()

    expect(hass.states.get(entity_id).state).to_equal(STATE_ON)

    # test webhook callback success single channel
    reolink_host.motion_detected.return_value = False
    reolink_host.ONVIF_event_callback.return_value = [0]
    await client.post(f"/api/webhook/{webhook_id}", data="test_data")
    await hass.async_block_till_done()
    signal_ch.assert_called_once()
    expect(hass.states.get(entity_id).state).to_equal(STATE_OFF)

    # test webhook callback single channel with error in event callback
    signal_ch.reset_mock()
    reolink_host.ONVIF_event_callback.side_effect = Exception("Test error")
    await client.post(f"/api/webhook/{webhook_id}", data="test_data")
    await hass.async_block_till_done()
    signal_ch.assert_not_called()

    # test failure to read date from webhook post
    request = MockRequest(
        method="POST",
        content=bytes("test", "utf-8"),
        mock_source="test",
    )
    request.read = AsyncMock()
    request.read.side_effect = ConnectionResetError("Test error")
    await async_handle_webhook(hass, webhook_id, request)
    signal_all.assert_not_called()

    request.read.side_effect = ClientResponseError("Test error", "Test")
    await async_handle_webhook(hass, webhook_id, request)
    signal_all.assert_not_called()

    request.read.side_effect = CancelledError("Test error")
    async with expect_raises_async(CancelledError):
        await async_handle_webhook(hass, webhook_id, request)
    signal_all.assert_not_called()


@test
async def no_mac(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fx),
    reolink_host: MagicMock = Depends(reolink_host_fx),
) -> None:
    """Test setup of host with no mac."""
    original = reolink_host.mac_address
    reolink_host.mac_address = None
    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_falsy()
    await hass.async_block_till_done()
    expect(config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)

    reolink_host.mac_address = original


@test
async def subscribe_error(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fx),
    reolink_host: MagicMock = Depends(reolink_host_fx),
) -> None:
    """Test error when subscribing to ONVIF does not block startup."""
    reolink_host.subscribe.side_effect = ReolinkError("Test Error")
    reolink_host.subscribed.return_value = False
    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_truthy()
    await hass.async_block_till_done()
    expect(config_entry.state).to_be(ConfigEntryState.LOADED)


@test
async def subscribe_unsuccesfull(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fx),
    reolink_host: MagicMock = Depends(reolink_host_fx),
) -> None:
    """Test that a unsuccessful ONVIF subscription does not block startup."""
    reolink_host.subscribed.return_value = False
    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_truthy()
    await hass.async_block_till_done()
    expect(config_entry.state).to_be(ConfigEntryState.LOADED)


@test
async def initial_ONVIF_not_supported(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fx),
    reolink_host: MagicMock = Depends(reolink_host_fx),
) -> None:
    """Test setup when initial ONVIF is not supported."""

    def test_supported(ch, key):
        """Test supported function."""
        if key == "initial_ONVIF_state":
            return False
        return True

    reolink_host.supported = test_supported

    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_truthy()
    await hass.async_block_till_done()
    expect(config_entry.state).to_be(ConfigEntryState.LOADED)


@test
async def ONVIF_not_supported(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fx),
    reolink_host: MagicMock = Depends(reolink_host_fx),
) -> None:
    """Test setup is not blocked when ONVIF API returns NotSupportedError."""

    def test_supported(ch, key):
        """Test supported function."""
        if key == "initial_ONVIF_state":
            return False
        return True

    reolink_host.supported = test_supported
    reolink_host.subscribed.return_value = False
    reolink_host.subscribe.side_effect = NotSupportedError("Test error")

    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_truthy()
    await hass.async_block_till_done()
    expect(config_entry.state).to_be(ConfigEntryState.LOADED)


@test
async def renew(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fx),
    config_entry: MockConfigEntry = Depends(config_entry_fx),
    reolink_host: MagicMock = Depends(reolink_host_fx),
) -> None:
    """Test renew of the ONVIF subscription."""
    reolink_host.renewtimer.return_value = 1

    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_truthy()
    await hass.async_block_till_done()
    expect(config_entry.state).to_be(ConfigEntryState.LOADED)

    freezer.tick(DEVICE_UPDATE_INTERVAL_MIN)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    reolink_host.renew.assert_called()

    reolink_host.renew.side_effect = SubscriptionError("Test error")

    freezer.tick(DEVICE_UPDATE_INTERVAL_MIN)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    reolink_host.subscribe.assert_called()

    reolink_host.subscribe.reset_mock()
    reolink_host.subscribe.side_effect = SubscriptionError("Test error")

    freezer.tick(DEVICE_UPDATE_INTERVAL_MIN)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    reolink_host.subscribe.assert_called()


@test
async def long_poll_renew_fail(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fx),
    config_entry: MockConfigEntry = Depends(config_entry_fx),
    reolink_host: MagicMock = Depends(reolink_host_fx),
) -> None:
    """Test ONVIF long polling errors while renewing."""
    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_truthy()
    await hass.async_block_till_done()
    expect(config_entry.state).to_be(ConfigEntryState.LOADED)

    reolink_host.subscribe.side_effect = NotSupportedError("Test error")

    freezer.tick(timedelta(seconds=FIRST_ONVIF_TIMEOUT))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    # ensure long polling continues
    reolink_host.pull_point_request.assert_called()


@test
async def register_webhook_errors(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fx),
    reolink_host: MagicMock = Depends(reolink_host_fx),
) -> None:
    """Test errors while registering the webhook."""
    with patch(
        "homeassistant.components.reolink.host.get_url",
        side_effect=NoURLAvailableError("Test error"),
    ):
        expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(False)
    await hass.async_block_till_done()
    expect(config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def long_poll_stop_when_push(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client_no_auth: ClientSessionGenerator = Depends(hass_client_no_auth_fx),
    freezer: FrozenDateTimeFactory = Depends(freezer_fx),
    config_entry: MockConfigEntry = Depends(config_entry_fx),
    reolink_host: MagicMock = Depends(reolink_host_fx),
) -> None:
    """Test ONVIF long polling stops when ONVIF push comes in."""
    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_truthy()
    await hass.async_block_till_done()
    expect(config_entry.state).to_be(ConfigEntryState.LOADED)

    # start ONVIF long polling because ONVIF push did not came in
    freezer.tick(timedelta(seconds=FIRST_ONVIF_TIMEOUT))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    # simulate ONVIF push callback
    client = await hass_client_no_auth()
    reolink_host.ONVIF_event_callback.return_value = None
    webhook_id = config_entry.runtime_data.host.webhook_id
    await client.post(f"/api/webhook/{webhook_id}")

    freezer.tick(DEVICE_UPDATE_INTERVAL_MIN)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    reolink_host.unsubscribe.assert_called_with(sub_type=SubType.long_poll)


@test
async def long_poll_errors(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fx),
    config_entry: MockConfigEntry = Depends(config_entry_fx),
    reolink_host: MagicMock = Depends(reolink_host_fx),
) -> None:
    """Test errors during ONVIF long polling."""
    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_truthy()
    await hass.async_block_till_done()
    expect(config_entry.state).to_be(ConfigEntryState.LOADED)

    reolink_host.pull_point_request.side_effect = ReolinkError("Test error")

    # start ONVIF long polling because ONVIF push did not came in
    freezer.tick(timedelta(seconds=FIRST_ONVIF_TIMEOUT))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    reolink_host.pull_point_request.assert_called_once()
    reolink_host.pull_point_request.side_effect = Exception("Test error")

    freezer.tick(timedelta(seconds=LONG_POLL_ERROR_COOLDOWN))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    freezer.tick(timedelta(seconds=LONG_POLL_COOLDOWN))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    reolink_host.unsubscribe.assert_called_with(sub_type=SubType.long_poll)


@test
async def fast_polling_errors(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fx),
    config_entry: MockConfigEntry = Depends(config_entry_fx),
    reolink_host: MagicMock = Depends(reolink_host_fx),
) -> None:
    """Test errors during ONVIF fast polling."""
    reolink_host.get_motion_state_all_ch.side_effect = ReolinkError("Test error")
    reolink_host.pull_point_request.side_effect = ReolinkError("Test error")

    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_truthy()
    await hass.async_block_till_done()
    expect(config_entry.state).to_be(ConfigEntryState.LOADED)

    # start ONVIF long polling because ONVIF push did not came in
    freezer.tick(timedelta(seconds=FIRST_ONVIF_TIMEOUT))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    # start ONVIF fast polling because ONVIF long polling did not came in
    freezer.tick(timedelta(seconds=FIRST_ONVIF_LONG_POLL_TIMEOUT))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    expect(reolink_host.get_motion_state_all_ch.call_count).to_equal(1)

    freezer.tick(timedelta(seconds=POLL_INTERVAL_NO_PUSH))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    # fast polling continues despite errors
    expect(reolink_host.get_motion_state_all_ch.call_count).to_equal(2)


@test
async def diagnostics_event_connection(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    hass_client_no_auth: ClientSessionGenerator = Depends(hass_client_no_auth_fx),
    freezer: FrozenDateTimeFactory = Depends(freezer_fx),
    reolink_host: MagicMock = Depends(reolink_host_fx),
    config_entry: MockConfigEntry = Depends(config_entry_fx),
) -> None:
    """Test Reolink diagnostics event connection return values."""
    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_truthy()
    await hass.async_block_till_done()
    expect(config_entry.state).to_be(ConfigEntryState.LOADED)

    diag = await get_diagnostics_for_config_entry(hass, hass_client, config_entry)
    expect(diag["event connection"]).to_equal("Fast polling")

    # start ONVIF long polling because ONVIF push did not came in
    freezer.tick(timedelta(seconds=FIRST_ONVIF_TIMEOUT))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    diag = await get_diagnostics_for_config_entry(hass, hass_client, config_entry)
    expect(diag["event connection"]).to_equal("ONVIF long polling")

    # simulate ONVIF push callback
    client = await hass_client_no_auth()
    reolink_host.ONVIF_event_callback.return_value = None
    webhook_id = config_entry.runtime_data.host.webhook_id
    await client.post(f"/api/webhook/{webhook_id}")

    diag = await get_diagnostics_for_config_entry(hass, hass_client, config_entry)
    expect(diag["event connection"]).to_equal("ONVIF push")

    # set TCP push as active
    reolink_host.baichuan.events_active = True
    diag = await get_diagnostics_for_config_entry(hass, hass_client, config_entry)
    expect(diag["event connection"]).to_equal("TCP push")
