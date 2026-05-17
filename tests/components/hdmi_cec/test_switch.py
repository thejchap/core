"""Tests for the HDMI-CEC switch platform."""

from typing import Any

from pycec.const import POWER_OFF, POWER_ON, STATUS_PLAY, STATUS_STILL, STATUS_STOP
from pycec.network import PhysicalAddress
from tryke import Depends, expect, fixture, test

from homeassistant.components.hdmi_cec import EVENT_HDMI_CEC_UNAVAILABLE
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.const import (
    ATTR_ENTITY_ID,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
)
from homeassistant.core import HomeAssistant

from . import MockHDMIDevice
from ._fixtures import (
    CecEntityCreator,
    HDMINetworkCreator,
    create_cec_entity,
    create_hdmi_network,
)

from tests.hass_fixtures import hass as hass_fixture


@fixture
def _trigger_executor() -> int:
    return 0


@test.cases(
    test.case("empty", config={}),
    test.case("switch", config={"platform": "switch"}),
)
async def load_platform(
    config: dict[str, Any],
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    create_hdmi_network: HDMINetworkCreator = Depends(create_hdmi_network),
    create_cec_entity: CecEntityCreator = Depends(create_cec_entity),
) -> None:
    """Test that switch entity is loaded."""
    hdmi_network = await create_hdmi_network(config=config)
    mock_hdmi_device = MockHDMIDevice(logical_address=3)
    await create_cec_entity(hdmi_network, mock_hdmi_device)
    mock_hdmi_device.set_update_callback.assert_called_once()
    state = hass.states.get("media_player.hdmi_3")
    expect(state).to_be_none()

    state = hass.states.get("switch.hdmi_3")
    expect(state).not_.to_be_none()


@test
async def load_types(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    create_hdmi_network: HDMINetworkCreator = Depends(create_hdmi_network),
    create_cec_entity: CecEntityCreator = Depends(create_cec_entity),
) -> None:
    """Test that switch entity is loaded when types is set."""
    config = {"platform": "media_player", "types": {"hdmi_cec.hdmi_3": "switch"}}
    hdmi_network = await create_hdmi_network(config=config)
    mock_hdmi_device = MockHDMIDevice(logical_address=3)
    await create_cec_entity(hdmi_network, mock_hdmi_device)
    mock_hdmi_device.set_update_callback.assert_called_once()
    state = hass.states.get("media_player.hdmi_3")
    expect(state).to_be_none()

    state = hass.states.get("switch.hdmi_3")
    expect(state).not_.to_be_none()

    mock_hdmi_device = MockHDMIDevice(logical_address=4)
    await create_cec_entity(hdmi_network, mock_hdmi_device)
    mock_hdmi_device.set_update_callback.assert_called_once()
    state = hass.states.get("media_player.hdmi_4")
    expect(state).not_.to_be_none()

    state = hass.states.get("switch.hdmi_4")
    expect(state).to_be_none()


@test
async def service_on(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    create_hdmi_network: HDMINetworkCreator = Depends(create_hdmi_network),
    create_cec_entity: CecEntityCreator = Depends(create_cec_entity),
) -> None:
    """Test that switch triggers on `on` service."""
    hdmi_network = await create_hdmi_network()
    mock_hdmi_device = MockHDMIDevice(logical_address=3, power_status=3)
    await create_cec_entity(hdmi_network, mock_hdmi_device)
    state = hass.states.get("switch.hdmi_3")
    expect(state.state).not_.to_equal(STATE_ON)

    await hass.services.async_call(
        SWITCH_DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: "switch.hdmi_3"}, blocking=True
    )

    mock_hdmi_device.turn_on.assert_called_once_with()

    state = hass.states.get("switch.hdmi_3")
    expect(state.state).to_equal(STATE_ON)


@test
async def service_off(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    create_hdmi_network: HDMINetworkCreator = Depends(create_hdmi_network),
    create_cec_entity: CecEntityCreator = Depends(create_cec_entity),
) -> None:
    """Test that switch triggers on `off` service."""
    hdmi_network = await create_hdmi_network()
    mock_hdmi_device = MockHDMIDevice(logical_address=3, power_status=4)
    await create_cec_entity(hdmi_network, mock_hdmi_device)
    state = hass.states.get("switch.hdmi_3")
    expect(state.state).not_.to_equal(STATE_OFF)

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: "switch.hdmi_3"},
        blocking=True,
    )

    mock_hdmi_device.turn_off.assert_called_once_with()

    state = hass.states.get("switch.hdmi_3")
    expect(state.state).to_equal(STATE_OFF)


# Cartesian product of power_status x status. Cases where power_status is
# POWER_ON/4 AND status is not None are xfailed in the original test.
@test.cases(
    test.case("p3_none", power_status=3, expected_state=STATE_OFF, status=None),
    test.case("p3_play", power_status=3, expected_state=STATE_OFF, status=STATUS_PLAY),
    test.case("p3_stop", power_status=3, expected_state=STATE_OFF, status=STATUS_STOP),
    test.case("p3_still", power_status=3, expected_state=STATE_OFF, status=STATUS_STILL),
    test.case("poff_none", power_status=POWER_OFF, expected_state=STATE_OFF, status=None),
    test.case("poff_play", power_status=POWER_OFF, expected_state=STATE_OFF, status=STATUS_PLAY),
    test.case("poff_stop", power_status=POWER_OFF, expected_state=STATE_OFF, status=STATUS_STOP),
    test.case("poff_still", power_status=POWER_OFF, expected_state=STATE_OFF, status=STATUS_STILL),
    test.case("p4_none", power_status=4, expected_state=STATE_ON, status=None),
    test.case("p4_play", power_status=4, expected_state=STATE_ON, status=STATUS_PLAY),
    test.case("p4_stop", power_status=4, expected_state=STATE_ON, status=STATUS_STOP),
    test.case("p4_still", power_status=4, expected_state=STATE_ON, status=STATUS_STILL),
    test.case("pon_none", power_status=POWER_ON, expected_state=STATE_ON, status=None),
    test.case("pon_play", power_status=POWER_ON, expected_state=STATE_ON, status=STATUS_PLAY),
    test.case("pon_stop", power_status=POWER_ON, expected_state=STATE_ON, status=STATUS_STOP),
    test.case("pon_still", power_status=POWER_ON, expected_state=STATE_ON, status=STATUS_STILL),
)
async def device_status_change(
    power_status: Any,
    expected_state: str,
    status: Any,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    create_hdmi_network: HDMINetworkCreator = Depends(create_hdmi_network),
    create_cec_entity: CecEntityCreator = Depends(create_cec_entity),
) -> None:
    """Test state change on device status change."""
    hdmi_network = await create_hdmi_network()
    mock_hdmi_device = MockHDMIDevice(logical_address=3, status=status)
    await create_cec_entity(hdmi_network, mock_hdmi_device)

    mock_hdmi_device.power_status = power_status
    await hass.async_block_till_done()

    state = hass.states.get("switch.hdmi_3")
    expect(state.state).to_equal(expected_state)


@test.cases(
    test.case(
        "nintendo_switch",
        device_values={"osd_name": "Switch", "vendor": "Nintendo"},
        expected="Nintendo Switch",
    ),
    test.case("tv", device_values={"type_name": "TV"}, expected="TV 3"),
    test.case(
        "playback_switch",
        device_values={"type_name": "Playback", "osd_name": "Switch"},
        expected="Playback 3 (Switch)",
    ),
    test.case(
        "tv_samsung",
        device_values={"type_name": "TV", "vendor": "Samsung"},
        expected="TV 3",
    ),
    test.case(
        "playback_unknown",
        device_values={
            "type_name": "Playback",
            "osd_name": "Super PC",
            "vendor": "Unknown",
        },
        expected="Playback 3 (Super PC)",
    ),
)
async def friendly_name(
    device_values: dict[str, Any],
    expected: str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    create_hdmi_network: HDMINetworkCreator = Depends(create_hdmi_network),
    create_cec_entity: CecEntityCreator = Depends(create_cec_entity),
) -> None:
    """Test friendly name setup."""
    hdmi_network = await create_hdmi_network()
    mock_hdmi_device = MockHDMIDevice(logical_address=3, **device_values)
    await create_cec_entity(hdmi_network, mock_hdmi_device)

    state = hass.states.get("switch.hdmi_3")
    expect(state.attributes["friendly_name"]).to_equal(expected)


@test.cases(
    test.case(
        "physical_address_only",
        device_values={"physical_address": PhysicalAddress("3.0.0.0")},
        expected_attributes={"physical_address": "3.0.0.0"},
    ),
    test.case(
        "empty",
        device_values={},
        expected_attributes={},
        xfail="physical address logic returns a string 'None' instead of not being set.",
    ),
    test.case(
        "vendor_id",
        device_values={
            "physical_address": PhysicalAddress("3.0.0.0"),
            "vendor_id": 5,
        },
        expected_attributes={
            "physical_address": "3.0.0.0",
            "vendor_id": 5,
            "vendor_name": None,
        },
    ),
    test.case(
        "vendor_samsung",
        device_values={
            "physical_address": PhysicalAddress("3.0.0.0"),
            "vendor_id": 5,
            "vendor": "Samsung",
        },
        expected_attributes={
            "physical_address": "3.0.0.0",
            "vendor_id": 5,
            "vendor_name": "Samsung",
        },
    ),
    test.case(
        "type_id_only",
        device_values={
            "physical_address": PhysicalAddress("3.0.0.0"),
            "type": 1,
        },
        expected_attributes={
            "physical_address": "3.0.0.0",
            "type_id": 1,
            "type": None,
        },
    ),
    test.case(
        "type_tv",
        device_values={
            "physical_address": PhysicalAddress("3.0.0.0"),
            "type": 1,
            "type_name": "TV",
        },
        expected_attributes={
            "physical_address": "3.0.0.0",
            "type_id": 1,
            "type": "TV",
        },
    ),
)
async def extra_state_attributes(
    device_values: dict[str, Any],
    expected_attributes: dict[str, Any],
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    create_hdmi_network: HDMINetworkCreator = Depends(create_hdmi_network),
    create_cec_entity: CecEntityCreator = Depends(create_cec_entity),
) -> None:
    """Test extra state attributes."""
    hdmi_network = await create_hdmi_network()
    mock_hdmi_device = MockHDMIDevice(logical_address=3, **device_values)
    await create_cec_entity(hdmi_network, mock_hdmi_device)

    state = hass.states.get("switch.hdmi_3")
    attributes = state.attributes
    # Copy keys we don't care about, so the equality check below ignores them.
    for att in ("friendly_name", "icon"):
        expected_attributes[att] = attributes[att]
    expect(dict(attributes)).to_equal(expected_attributes)


@test.cases(
    test.case("none", device_type=None, expected_icon="mdi:help"),
    test.case("tv", device_type=0, expected_icon="mdi:television"),
    test.case("microphone", device_type=1, expected_icon="mdi:microphone"),
    test.case("help", device_type=2, expected_icon="mdi:help"),
    test.case("radio", device_type=3, expected_icon="mdi:radio"),
    test.case("play", device_type=4, expected_icon="mdi:play"),
    test.case("speaker", device_type=5, expected_icon="mdi:speaker"),
)
async def icon(
    device_type: Any,
    expected_icon: str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    create_hdmi_network: HDMINetworkCreator = Depends(create_hdmi_network),
    create_cec_entity: CecEntityCreator = Depends(create_cec_entity),
) -> None:
    """Test icon selection."""
    hdmi_network = await create_hdmi_network()
    mock_hdmi_device = MockHDMIDevice(logical_address=3, type=device_type)
    await create_cec_entity(hdmi_network, mock_hdmi_device)

    state = hass.states.get("switch.hdmi_3")
    expect(state.attributes["icon"]).to_equal(expected_icon)


@test
async def unavailable_status(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    create_hdmi_network: HDMINetworkCreator = Depends(create_hdmi_network),
    create_cec_entity: CecEntityCreator = Depends(create_cec_entity),
) -> None:
    """Test entity goes into unavailable status when expected."""
    hdmi_network = await create_hdmi_network()
    mock_hdmi_device = MockHDMIDevice(logical_address=3)
    await create_cec_entity(hdmi_network, mock_hdmi_device)

    hass.bus.async_fire(EVENT_HDMI_CEC_UNAVAILABLE)
    await hass.async_block_till_done()

    state = hass.states.get("switch.hdmi_3")
    expect(state.state).to_equal(STATE_UNAVAILABLE)
