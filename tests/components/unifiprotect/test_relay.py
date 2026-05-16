"""Tests for the UniFi Protect relay (Public API) switch entities."""

from unittest.mock import AsyncMock, Mock

from tryke import Depends, expect, fixture, test
from uiprotect.data import (
    ModelType,
    PublicBootstrap,
    PublicRelayOutput,
    Relay,
    RelayOutputState,
)
from uiprotect.exceptions import ClientError, NotAuthorized
from uiprotect.websocket import WebsocketState

from homeassistant.const import (
    ATTR_ENTITY_ID,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er, translation as translation_helper

from ._fixtures import ufp as ufp_fixture
from .utils import MockUFPFixture, init_entry

from tests.hass_fixtures import (
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
)
from tests.hass_tryke_helpers import expect_raises_async

RELAY_ID = "relay-id-1"
RELAY_MAC = "AA:BB:CC:DD:EE:01"
RELAY_NAME = "Garage Relay"
OUTPUT_ID = 1
OUTPUT_NAME = "output1"

SWITCH_ENTITY_ID = "switch.garage_relay_output_output1"


@fixture
def _trigger_executor() -> int:
    return 0


def _make_output(
    output_id: int = OUTPUT_ID,
    name: str | None = OUTPUT_NAME,
    state: RelayOutputState | None = RelayOutputState.OFF,
) -> Mock:
    """Build a mock :class:`PublicRelayOutput`."""
    output = Mock(spec=PublicRelayOutput)
    output.id = output_id
    output.name = name
    output.state = state
    return output


def _make_relay(
    *,
    outputs: list[Mock] | None = None,
) -> Mock:
    """Build a mock :class:`Relay` whose ``activate_output`` is awaitable."""
    relay = Mock(spec=Relay)
    relay.id = RELAY_ID
    relay.mac = RELAY_MAC
    relay.name = RELAY_NAME
    relay.model = ModelType.RELAY
    relay.outputs = outputs if outputs is not None else [_make_output()]

    def get_output(output_id: int) -> Mock | None:
        return next((o for o in relay.outputs if o.id == output_id), None)

    relay.get_output = get_output
    relay.activate_output = AsyncMock()
    return relay


def _make_public_bootstrap(relay: Mock | None) -> Mock:
    """Build a public bootstrap mock holding the given relay."""
    pb = Mock(spec=PublicBootstrap)
    pb.relays = {relay.id: relay} if relay is not None else {}
    pb.arm_mode = None
    pb.arm_profiles = {}
    pb.sirens = {}
    return pb


async def _setup_with_relay(
    hass: HomeAssistant, ufp: MockUFPFixture, relay: Mock
) -> None:
    """Pre-load translations then set up the entry."""
    ufp.api.has_public_bootstrap = True
    ufp.api.public_bootstrap = _make_public_bootstrap(relay)
    # Pre-load unifiprotect translations so entity names resolve to slugs
    # like "switch.garage_relay_output_output1" instead of "switch.garage_relay".
    await translation_helper.async_load_integrations(hass, {"unifiprotect"})
    await init_entry(hass, ufp, [])


@fixture
def ufp_with_relay_fixture(
    ufp: MockUFPFixture = Depends(ufp_fixture),
) -> tuple[MockUFPFixture, Mock]:
    """Configure ufp fixture with a single relay accessible via public API."""
    relay = _make_relay()
    ufp.api.has_public_bootstrap = True
    ufp.api.public_bootstrap = _make_public_bootstrap(relay)
    return ufp, relay


# ---------------------------------------------------------------------------
# Switch
# ---------------------------------------------------------------------------


@test
async def relay_switch_not_created_without_public_bootstrap(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp_fixture),
) -> None:
    """No relay output switch is created when public bootstrap is unavailable."""
    ufp.api.has_public_bootstrap = False
    await translation_helper.async_load_integrations(hass, {"unifiprotect"})
    await init_entry(hass, ufp, [])

    expect(hass.states.get(SWITCH_ENTITY_ID)).to_be_none()


@test
async def relay_switch_created_with_state(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    ufp_with_relay: tuple[MockUFPFixture, Mock] = Depends(ufp_with_relay_fixture),
) -> None:
    """Relay output switch is created and reflects the cached state."""
    ufp, relay = ufp_with_relay
    relay.outputs[0].state = RelayOutputState.ON

    await _setup_with_relay(hass, ufp, relay)

    entry = entity_registry.async_get(SWITCH_ENTITY_ID)
    expect(entry).not_.to_be_none()
    expect(entry.unique_id).to_equal(f"{RELAY_MAC}_relay_output_{OUTPUT_ID}")

    state = hass.states.get(SWITCH_ENTITY_ID)
    expect(state).not_.to_be_none()
    expect(state.state).to_equal(STATE_ON)


@test
async def relay_switch_off_otp_is_off(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp_with_relay: tuple[MockUFPFixture, Mock] = Depends(ufp_with_relay_fixture),
) -> None:
    """OFF_OTP (over-temperature protection) is treated as ``off``."""
    ufp, relay = ufp_with_relay
    relay.outputs[0].state = RelayOutputState.OFF_OTP

    await _setup_with_relay(hass, ufp, relay)

    state = hass.states.get(SWITCH_ENTITY_ID)
    expect(state).not_.to_be_none()
    expect(state.state).to_equal(STATE_OFF)


@test
async def relay_switch_unknown_state_is_unknown(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp_with_relay: tuple[MockUFPFixture, Mock] = Depends(ufp_with_relay_fixture),
) -> None:
    """Unknown relay state should leave the switch state as ``unknown``."""
    ufp, relay = ufp_with_relay
    relay.outputs[0].state = RelayOutputState.UNKNOWN

    await _setup_with_relay(hass, ufp, relay)

    state = hass.states.get(SWITCH_ENTITY_ID)
    expect(state).not_.to_be_none()
    expect(state.state).to_equal(STATE_UNKNOWN)


@test
async def relay_switch_turn_on_off(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp_with_relay: tuple[MockUFPFixture, Mock] = Depends(ufp_with_relay_fixture),
) -> None:
    """Calling ``turn_on``/``turn_off`` invokes the public-API helper."""
    ufp, relay = ufp_with_relay
    await _setup_with_relay(hass, ufp, relay)

    await hass.services.async_call(
        Platform.SWITCH,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: SWITCH_ENTITY_ID},
        blocking=True,
    )
    relay.activate_output.assert_awaited_once_with(OUTPUT_ID, state="on")
    relay.activate_output.reset_mock()

    await hass.services.async_call(
        Platform.SWITCH,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: SWITCH_ENTITY_ID},
        blocking=True,
    )
    relay.activate_output.assert_awaited_once_with(OUTPUT_ID, state="off")


@test
async def relay_switch_state_updates_from_public_ws(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp_with_relay: tuple[MockUFPFixture, Mock] = Depends(ufp_with_relay_fixture),
) -> None:
    """A public devices WS update for the relay refreshes the switch state."""
    ufp, relay = ufp_with_relay
    relay.outputs[0].state = RelayOutputState.OFF
    await _setup_with_relay(hass, ufp, relay)

    state = hass.states.get(SWITCH_ENTITY_ID)
    expect(state).not_.to_be_none()
    expect(state.state).to_equal(STATE_OFF)

    relay.outputs[0].state = RelayOutputState.ON

    mock_msg = Mock()
    mock_msg.changed_data = {}
    mock_msg.old_obj = relay
    mock_msg.new_obj = relay
    expect(ufp.devices_ws_subscription).not_.to_be_none()
    ufp.devices_ws_subscription(mock_msg)
    await hass.async_block_till_done()

    state = hass.states.get(SWITCH_ENTITY_ID)
    expect(state).not_.to_be_none()
    expect(state.state).to_equal(STATE_ON)


@test
async def relay_switch_creates_one_entity_per_output(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    ufp: MockUFPFixture = Depends(ufp_fixture),
) -> None:
    """Multiple outputs on a single relay yield multiple switch entities."""
    relay = _make_relay(
        outputs=[
            _make_output(output_id=1, name="output1"),
            _make_output(output_id=2, name="output2"),
        ],
    )
    await _setup_with_relay(hass, ufp, relay)

    expect(
        entity_registry.async_get("switch.garage_relay_output_output1")
    ).not_.to_be_none()
    expect(
        entity_registry.async_get("switch.garage_relay_output_output2")
    ).not_.to_be_none()


@test
async def relay_switch_command_error_raises(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp_with_relay: tuple[MockUFPFixture, Mock] = Depends(ufp_with_relay_fixture),
) -> None:
    """``activate_output`` errors are surfaced as :class:`HomeAssistantError`."""
    ufp, relay = ufp_with_relay
    await _setup_with_relay(hass, ufp, relay)

    relay.activate_output.side_effect = NotAuthorized("denied")

    async with expect_raises_async(HomeAssistantError):
        await hass.services.async_call(
            Platform.SWITCH,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: SWITCH_ENTITY_ID},
            blocking=True,
        )


@test
async def relay_switch_client_error_raises(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp_with_relay: tuple[MockUFPFixture, Mock] = Depends(ufp_with_relay_fixture),
) -> None:
    """``ClientError`` from ``activate_output`` is wrapped as HomeAssistantError."""
    ufp, relay = ufp_with_relay
    await _setup_with_relay(hass, ufp, relay)

    relay.activate_output.side_effect = ClientError("timeout")

    async with expect_raises_async(HomeAssistantError):
        await hass.services.async_call(
            Platform.SWITCH,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: SWITCH_ENTITY_ID},
            blocking=True,
        )


@test
async def relay_switch_command_when_relay_gone(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp_with_relay: tuple[MockUFPFixture, Mock] = Depends(ufp_with_relay_fixture),
) -> None:
    """Command raises HomeAssistantError when the relay is no longer in bootstrap."""
    ufp, relay = ufp_with_relay
    await _setup_with_relay(hass, ufp, relay)

    ufp.api.public_bootstrap.relays = {}

    async with expect_raises_async(HomeAssistantError):
        await hass.services.async_call(
            Platform.SWITCH,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: SWITCH_ENTITY_ID},
            blocking=True,
        )


@test
async def relay_switch_command_when_bootstrap_unavailable(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp_with_relay: tuple[MockUFPFixture, Mock] = Depends(ufp_with_relay_fixture),
) -> None:
    """Command raises HomeAssistantError when has_public_bootstrap is False."""
    ufp, relay = ufp_with_relay
    await _setup_with_relay(hass, ufp, relay)

    ufp.api.has_public_bootstrap = False

    async with expect_raises_async(HomeAssistantError):
        await hass.services.async_call(
            Platform.SWITCH,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: SWITCH_ENTITY_ID},
            blocking=True,
        )


@test
async def relay_switch_ws_update_no_state_change(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp_with_relay: tuple[MockUFPFixture, Mock] = Depends(ufp_with_relay_fixture),
) -> None:
    """WS update with the same state does not trigger an unnecessary state write."""
    ufp, relay = ufp_with_relay
    relay.outputs[0].state = RelayOutputState.ON
    await _setup_with_relay(hass, ufp, relay)

    state_obj = hass.states.get(SWITCH_ENTITY_ID)
    expect(state_obj).not_.to_be_none()
    expect(state_obj.state).to_equal(STATE_ON)

    mock_msg = Mock()
    mock_msg.changed_data = {}
    mock_msg.old_obj = relay
    mock_msg.new_obj = relay
    expect(ufp.devices_ws_subscription).not_.to_be_none()
    ufp.devices_ws_subscription(mock_msg)
    await hass.async_block_till_done()

    state_obj = hass.states.get(SWITCH_ENTITY_ID)
    expect(state_obj).not_.to_be_none()
    expect(state_obj.state).to_equal(STATE_ON)


@test
async def relay_switch_becomes_unavailable_when_relay_removed(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp_with_relay: tuple[MockUFPFixture, Mock] = Depends(ufp_with_relay_fixture),
) -> None:
    """Entity becomes unavailable when the relay disappears from the bootstrap."""
    ufp, relay = ufp_with_relay
    relay.outputs[0].state = RelayOutputState.OFF
    await _setup_with_relay(hass, ufp, relay)

    ufp.api.public_bootstrap.relays = {}

    relay2 = _make_relay()
    relay2.id = relay.id
    relay2.mac = relay.mac

    mock_msg = Mock()
    mock_msg.changed_data = {}
    mock_msg.old_obj = relay2
    mock_msg.new_obj = relay2
    expect(ufp.devices_ws_subscription).not_.to_be_none()
    ufp.devices_ws_subscription(mock_msg)
    await hass.async_block_till_done()

    state = hass.states.get(SWITCH_ENTITY_ID)
    expect(state).not_.to_be_none()
    expect(state.state).to_equal(STATE_UNAVAILABLE)


@test
async def relay_switch_availability_follows_websocket_state(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp_with_relay: tuple[MockUFPFixture, Mock] = Depends(ufp_with_relay_fixture),
) -> None:
    """Relay switch becomes unavailable on WS disconnect and recovers on reconnect."""
    ufp, relay = ufp_with_relay
    relay.outputs[0].state = RelayOutputState.ON
    await _setup_with_relay(hass, ufp, relay)

    state_obj = hass.states.get(SWITCH_ENTITY_ID)
    expect(state_obj).not_.to_be_none()
    expect(state_obj.state).to_equal(STATE_ON)

    expect(ufp.ws_state_subscription).not_.to_be_none()
    ufp.ws_state_subscription(WebsocketState.DISCONNECTED)
    await hass.async_block_till_done()

    state = hass.states.get(SWITCH_ENTITY_ID)
    expect(state).not_.to_be_none()
    expect(state.state).to_equal(STATE_UNAVAILABLE)

    ufp.ws_state_subscription(WebsocketState.CONNECTED)
    await hass.async_block_till_done()

    state = hass.states.get(SWITCH_ENTITY_ID)
    expect(state).not_.to_be_none()
    expect(state.state).to_equal(STATE_ON)


@test
async def relay_public_ws_message_with_none_new_obj(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp_with_relay: tuple[MockUFPFixture, Mock] = Depends(ufp_with_relay_fixture),
) -> None:
    """Public WS message with new_obj=None is silently ignored."""
    ufp, relay = ufp_with_relay
    await _setup_with_relay(hass, ufp, relay)

    state_before = hass.states.get(SWITCH_ENTITY_ID)
    expect(state_before).not_.to_be_none()

    mock_msg = Mock()
    mock_msg.new_obj = None

    expect(ufp.devices_ws_subscription).not_.to_be_none()
    ufp.devices_ws_subscription(mock_msg)
    await hass.async_block_till_done()

    expect(hass.states.get(SWITCH_ENTITY_ID)).to_equal(state_before)


@test
async def relay_switch_output_removed_from_relay_update(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp_with_relay: tuple[MockUFPFixture, Mock] = Depends(ufp_with_relay_fixture),
) -> None:
    """WS update where the output is no longer present marks the entity unavailable."""
    ufp, relay = ufp_with_relay
    relay.outputs[0].state = RelayOutputState.ON
    await _setup_with_relay(hass, ufp, relay)

    state_obj = hass.states.get(SWITCH_ENTITY_ID)
    expect(state_obj).not_.to_be_none()
    expect(state_obj.state).to_equal(STATE_ON)

    relay_no_outputs = _make_relay(outputs=[])
    relay_no_outputs.id = relay.id
    relay_no_outputs.mac = relay.mac

    mock_msg = Mock()
    mock_msg.changed_data = {}
    mock_msg.old_obj = relay_no_outputs
    mock_msg.new_obj = relay_no_outputs

    expect(ufp.devices_ws_subscription).not_.to_be_none()
    ufp.devices_ws_subscription(mock_msg)
    await hass.async_block_till_done()

    state = hass.states.get(SWITCH_ENTITY_ID)
    expect(state).not_.to_be_none()
    expect(state.state).to_equal(STATE_UNAVAILABLE)


@test
async def relay_switch_command_when_output_gone(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp_with_relay: tuple[MockUFPFixture, Mock] = Depends(ufp_with_relay_fixture),
) -> None:
    """Command raises HomeAssistantError when the relay output channel is no longer present."""
    ufp, relay = ufp_with_relay
    await _setup_with_relay(hass, ufp, relay)

    relay.outputs = []

    async with expect_raises_async(HomeAssistantError):
        await hass.services.async_call(
            Platform.SWITCH,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: SWITCH_ENTITY_ID},
            blocking=True,
        )
