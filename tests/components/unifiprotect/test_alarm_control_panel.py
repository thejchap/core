"""Test the UniFi Protect alarm control panel platform."""

from unittest.mock import AsyncMock, Mock

from tryke import Depends, expect, fixture, test
from uiprotect.data import NVR, NvrArmMode, NvrArmModeStatus, PublicBootstrap
from uiprotect.exceptions import GlobalAlarmManagerError
from uiprotect.websocket import WebsocketState

from homeassistant.components.alarm_control_panel import (
    DOMAIN as ALARM_DOMAIN,
    AlarmControlPanelState,
)
from homeassistant.components.unifiprotect.const import DEFAULT_ATTRIBUTION
from homeassistant.const import (
    ATTR_ATTRIBUTION,
    ATTR_ENTITY_ID,
    SERVICE_ALARM_ARM_AWAY,
    SERVICE_ALARM_DISARM,
    STATE_UNAVAILABLE,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er

from ._fixtures import (
    nvr as nvr_fixture,
    ufp as ufp_fixture,
)
from .utils import MockUFPFixture, assert_entity_counts, init_entry

from tests.hass_fixtures import (
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
)

ALARM_ENTITY_ID = "alarm_control_panel.unifiprotect_alarm_manager"


def _make_arm_mode(status: NvrArmModeStatus) -> Mock:
    """Create a NvrArmMode object for testing."""
    arm_mode = Mock(spec=NvrArmMode)
    arm_mode.status = status
    return arm_mode


def _make_public_bootstrap(arm_mode: Mock | None) -> Mock:
    """Create a PublicBootstrap with the given arm_mode."""
    pb = Mock(spec=PublicBootstrap)
    pb.arm_mode = arm_mode
    pb.arm_profiles = {}
    pb.relays = {}
    pb.sirens = {}
    return pb


@fixture
def _trigger_executor() -> int:
    """Force tryke to build a per-module HookExecutor for this file."""
    return 0


@test
async def alarm_panel_not_created_without_public_bootstrap(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp_fixture),
) -> None:
    """Alarm panel entity is NOT created when has_public_bootstrap is False."""
    ufp.api.has_public_bootstrap = False

    await init_entry(hass, ufp, [])
    assert_entity_counts(hass, Platform.ALARM_CONTROL_PANEL, 0, 0)


@test
async def alarm_panel_created_with_public_bootstrap(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    ufp: MockUFPFixture = Depends(ufp_fixture),
    nvr: NVR = Depends(nvr_fixture),
) -> None:
    """Alarm panel entity IS created when has_public_bootstrap is True."""
    arm_mode = _make_arm_mode(NvrArmModeStatus.DISABLED)
    pb = _make_public_bootstrap(arm_mode)
    ufp.api.has_public_bootstrap = True
    ufp.api.public_bootstrap = pb

    await init_entry(hass, ufp, [])
    assert_entity_counts(hass, Platform.ALARM_CONTROL_PANEL, 1, 1)

    entity = entity_registry.async_get(ALARM_ENTITY_ID)
    expect(entity).not_.to_be(None)
    expect(entity.unique_id).to_equal(f"{nvr.mac}_alarm")

    state = hass.states.get(ALARM_ENTITY_ID)
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(AlarmControlPanelState.DISARMED)
    expect(state.attributes[ATTR_ATTRIBUTION]).to_equal(DEFAULT_ATTRIBUTION)


@test.cases(
    test.case(
        "disabled",
        nvr_status=NvrArmModeStatus.DISABLED,
        expected_state=AlarmControlPanelState.DISARMED,
    ),
    test.case(
        "unknown",
        nvr_status=NvrArmModeStatus.UNKNOWN,
        expected_state=AlarmControlPanelState.DISARMED,
    ),
    test.case(
        "arming",
        nvr_status=NvrArmModeStatus.ARMING,
        expected_state=AlarmControlPanelState.ARMING,
    ),
    test.case(
        "armed",
        nvr_status=NvrArmModeStatus.ARMED,
        expected_state=AlarmControlPanelState.ARMED_AWAY,
    ),
    test.case(
        "breach",
        nvr_status=NvrArmModeStatus.BREACH,
        expected_state=AlarmControlPanelState.TRIGGERED,
    ),
)
async def alarm_panel_state_mapping(
    *,
    nvr_status: NvrArmModeStatus,
    expected_state: AlarmControlPanelState,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp_fixture),
) -> None:
    """Test that NvrArmModeStatus maps to correct AlarmControlPanelState."""
    arm_mode = _make_arm_mode(nvr_status)
    pb = _make_public_bootstrap(arm_mode)
    ufp.api.has_public_bootstrap = True
    ufp.api.public_bootstrap = pb

    await init_entry(hass, ufp, [])

    state = hass.states.get(ALARM_ENTITY_ID)
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(expected_state)


@test
async def alarm_panel_not_created_without_arm_mode(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp_fixture),
) -> None:
    """Alarm panel entity is NOT created on old firmware (arm_mode is None)."""
    pb = _make_public_bootstrap(arm_mode=None)
    ufp.api.has_public_bootstrap = True
    ufp.api.public_bootstrap = pb

    await init_entry(hass, ufp, [])
    assert_entity_counts(hass, Platform.ALARM_CONTROL_PANEL, 0, 0)


@test
async def alarm_panel_disarm(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp_fixture),
) -> None:
    """Test that disarm service calls disable_arm_alarm_public."""
    arm_mode = _make_arm_mode(NvrArmModeStatus.ARMED)
    pb = _make_public_bootstrap(arm_mode)
    ufp.api.has_public_bootstrap = True
    ufp.api.public_bootstrap = pb
    ufp.api.disable_arm_alarm_public = AsyncMock()

    await init_entry(hass, ufp, [])

    await hass.services.async_call(
        ALARM_DOMAIN,
        SERVICE_ALARM_DISARM,
        {ATTR_ENTITY_ID: ALARM_ENTITY_ID},
        blocking=True,
    )

    ufp.api.disable_arm_alarm_public.assert_called_once()


@test
async def alarm_panel_arm_away(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp_fixture),
) -> None:
    """Test that arm_away service calls enable_arm_alarm_public."""
    arm_mode = _make_arm_mode(NvrArmModeStatus.DISABLED)
    pb = _make_public_bootstrap(arm_mode)
    ufp.api.has_public_bootstrap = True
    ufp.api.public_bootstrap = pb
    ufp.api.enable_arm_alarm_public = AsyncMock()

    await init_entry(hass, ufp, [])

    await hass.services.async_call(
        ALARM_DOMAIN,
        SERVICE_ALARM_ARM_AWAY,
        {ATTR_ENTITY_ID: ALARM_ENTITY_ID},
        blocking=True,
    )

    ufp.api.enable_arm_alarm_public.assert_called_once()


@test
async def alarm_panel_disarm_global_manager_error(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp_fixture),
) -> None:
    """Test that GlobalAlarmManagerError on disarm raises HomeAssistantError."""
    arm_mode = _make_arm_mode(NvrArmModeStatus.ARMED)
    pb = _make_public_bootstrap(arm_mode)
    ufp.api.has_public_bootstrap = True
    ufp.api.public_bootstrap = pb
    ufp.api.disable_arm_alarm_public = AsyncMock(side_effect=GlobalAlarmManagerError())

    await init_entry(hass, ufp, [])

    raised: HomeAssistantError | None = None
    try:
        await hass.services.async_call(
            ALARM_DOMAIN,
            SERVICE_ALARM_DISARM,
            {ATTR_ENTITY_ID: ALARM_ENTITY_ID},
            blocking=True,
        )
    except HomeAssistantError as exc:
        raised = exc

    expect(raised is not None).to_be(True)
    expect(raised.translation_key).to_equal("global_alarm_manager")


@test
async def alarm_panel_arm_away_global_manager_error(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp_fixture),
) -> None:
    """Test that GlobalAlarmManagerError on arm raises HomeAssistantError."""
    arm_mode = _make_arm_mode(NvrArmModeStatus.DISABLED)
    pb = _make_public_bootstrap(arm_mode)
    ufp.api.has_public_bootstrap = True
    ufp.api.public_bootstrap = pb
    ufp.api.enable_arm_alarm_public = AsyncMock(side_effect=GlobalAlarmManagerError())

    await init_entry(hass, ufp, [])

    raised: HomeAssistantError | None = None
    try:
        await hass.services.async_call(
            ALARM_DOMAIN,
            SERVICE_ALARM_ARM_AWAY,
            {ATTR_ENTITY_ID: ALARM_ENTITY_ID},
            blocking=True,
        )
    except HomeAssistantError as exc:
        raised = exc

    expect(raised is not None).to_be(True)
    expect(raised.translation_key).to_equal("global_alarm_manager")


@test
async def alarm_panel_state_update_via_ws(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp_fixture),
    nvr: NVR = Depends(nvr_fixture),
) -> None:
    """Test that public devices WS update triggers state refresh."""
    arm_mode = _make_arm_mode(NvrArmModeStatus.DISABLED)
    pb = _make_public_bootstrap(arm_mode)
    ufp.api.has_public_bootstrap = True
    ufp.api.public_bootstrap = pb

    await init_entry(hass, ufp, [])

    state = hass.states.get(ALARM_ENTITY_ID)
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(AlarmControlPanelState.DISARMED)

    armed_arm_mode = _make_arm_mode(NvrArmModeStatus.ARMED)
    pb.arm_mode = armed_arm_mode

    mock_msg = Mock()
    mock_msg.changed_data = {}
    mock_msg.old_obj = nvr
    mock_msg.new_obj = nvr
    expect(ufp.devices_ws_subscription).not_.to_be(None)
    ufp.devices_ws_subscription(mock_msg)
    await hass.async_block_till_done()

    state = hass.states.get(ALARM_ENTITY_ID)
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(AlarmControlPanelState.ARMED_AWAY)


@test
async def alarm_panel_unavailable_when_arm_mode_disappears(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp_fixture),
    nvr: NVR = Depends(nvr_fixture),
) -> None:
    """Entity becomes unavailable when arm_mode disappears after a WS update."""
    arm_mode = _make_arm_mode(NvrArmModeStatus.ARMED)
    pb = _make_public_bootstrap(arm_mode)
    ufp.api.has_public_bootstrap = True
    ufp.api.public_bootstrap = pb

    await init_entry(hass, ufp, [])

    state = hass.states.get(ALARM_ENTITY_ID)
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(AlarmControlPanelState.ARMED_AWAY)

    pb.arm_mode = None

    mock_msg = Mock()
    mock_msg.changed_data = {}
    mock_msg.old_obj = nvr
    mock_msg.new_obj = nvr
    ufp.ws_msg(mock_msg)
    await hass.async_block_till_done()

    state = hass.states.get(ALARM_ENTITY_ID)
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(STATE_UNAVAILABLE)


@test
async def alarm_panel_unavailable_on_ws_disconnect(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp_fixture),
) -> None:
    """Entity becomes unavailable when the private WebSocket disconnects."""
    arm_mode = _make_arm_mode(NvrArmModeStatus.ARMED)
    pb = _make_public_bootstrap(arm_mode)
    ufp.api.has_public_bootstrap = True
    ufp.api.public_bootstrap = pb

    await init_entry(hass, ufp, [])

    state = hass.states.get(ALARM_ENTITY_ID)
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(AlarmControlPanelState.ARMED_AWAY)

    ufp.ws_state_subscription(WebsocketState.DISCONNECTED)
    await hass.async_block_till_done()

    state = hass.states.get(ALARM_ENTITY_ID)
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(STATE_UNAVAILABLE)

    ufp.ws_state_subscription(WebsocketState.CONNECTED)
    await hass.async_block_till_done()

    state = hass.states.get(ALARM_ENTITY_ID)
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(AlarmControlPanelState.ARMED_AWAY)
