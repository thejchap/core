"""Tests for the HDMI-CEC component."""

from datetime import timedelta
from typing import Any
from unittest.mock import ANY, MagicMock, PropertyMock, call

from tryke import Depends, expect, fixture, test

from homeassistant.components.hdmi_cec import (
    DOMAIN,
    EVENT_HDMI_CEC_UNAVAILABLE,
    SERVICE_POWER_ON,
    SERVICE_SELECT_DEVICE,
    SERVICE_SEND_COMMAND,
    SERVICE_STANDBY,
    SERVICE_UPDATE_DEVICES,
    SERVICE_VOLUME,
    WATCHDOG_INTERVAL,
    CecCommand,
    KeyPressCommand,
    KeyReleaseCommand,
    PhysicalAddress,
    parse_mapping,
)
from homeassistant.const import EVENT_HOMEASSISTANT_START, EVENT_HOMEASSISTANT_STOP
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util.dt import utcnow

from . import assert_key_press_release
from ._fixtures import (
    HDMINetworkCreator,
    create_hdmi_network,
    mock_cec_adapter,
    mock_hdmi_network,
    mock_tcp_adapter,
)

from tests.common import (
    MockEntity,
    MockEntityPlatform,
    async_capture_events,
    async_fire_time_changed,
)
from tests.hass_fixtures import hass as hass_fixture


@fixture
def _trigger_executor() -> int:
    return 0


@test.cases(
    test.case("empty", mapping={}, expected=[]),
    test.case(
        "string_addresses",
        mapping={
            "TV": "0.0.0.0",
            "Pi Zero": "1.0.0.0",
            "Fire TV Stick": "2.1.0.0",
            "Chromecast": "2.2.0.0",
            "Another Device": "2.3.0.0",
            "BlueRay player": "3.0.0.0",
        },
        expected=[
            ("TV", "0.0.0.0"),
            ("Pi Zero", "1.0.0.0"),
            ("Fire TV Stick", "2.1.0.0"),
            ("Chromecast", "2.2.0.0"),
            ("Another Device", "2.3.0.0"),
            ("BlueRay player", "3.0.0.0"),
        ],
    ),
    test.case(
        "nested_addresses",
        mapping={
            1: "Pi Zero",
            2: {
                1: "Fire TV Stick",
                2: "Chromecast",
                3: "Another Device",
            },
            3: "BlueRay player",
        },
        expected=[
            ("Pi Zero", [1, 0, 0, 0]),
            ("Fire TV Stick", [2, 1, 0, 0]),
            ("Chromecast", [2, 2, 0, 0]),
            ("Another Device", [2, 3, 0, 0]),
            ("BlueRay player", [3, 0, 0, 0]),
        ],
    ),
)
def parse_mapping_physical_address(
    mapping: dict[str, Any], expected: list[tuple[str, list[int]]]
) -> None:
    """Test the device config mapping function."""
    result = parse_mapping(mapping)
    result = [
        (r[0], str(r[1]) if isinstance(r[1], PhysicalAddress) else r[1]) for r in result
    ]
    expect(result).to_equal(expected)


# Test Setup


@test
async def setup_cec_adapter(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_cec_adapter: MagicMock = Depends(mock_cec_adapter),
    mock_hdmi_network: MagicMock = Depends(mock_hdmi_network),
) -> None:
    """Test the general setup of this component."""
    await async_setup_component(hass, DOMAIN, {DOMAIN: {}})

    mock_cec_adapter.assert_called_once_with(name="HA", activate_source=False)
    mock_hdmi_network.assert_called_once()
    call_args = mock_hdmi_network.call_args
    expect(call_args).to_equal(call(mock_cec_adapter.return_value, loop=ANY))
    expect(call_args.kwargs["loop"] in (None, hass.loop)).to_be(True)

    mock_hdmi_network_instance = mock_hdmi_network.return_value

    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    await hass.async_block_till_done()
    mock_hdmi_network_instance.start.assert_called_once_with()
    mock_hdmi_network_instance.set_new_device_callback.assert_called_once()
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STOP)
    await hass.async_block_till_done()
    mock_hdmi_network_instance.stop.assert_called_once_with()


@test.cases(
    test.case("short", osd_name="test"),
    test.case("long", osd_name="test_a_long_name"),
)
async def setup_set_osd_name(
    osd_name: str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_cec_adapter: MagicMock = Depends(mock_cec_adapter),
) -> None:
    """Test the setup of this component with the `osd_name` config setting."""
    await async_setup_component(hass, DOMAIN, {DOMAIN: {"osd_name": osd_name}})

    mock_cec_adapter.assert_called_once_with(name=osd_name[:12], activate_source=False)


@test
async def setup_tcp_adapter(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_tcp_adapter: MagicMock = Depends(mock_tcp_adapter),
    mock_hdmi_network: MagicMock = Depends(mock_hdmi_network),
    _mock_cec_adapter: MagicMock = Depends(mock_cec_adapter),
) -> None:
    """Test the setup of this component with the TcpAdapter (`host` config setting)."""
    host = "0.0.0.0"

    await async_setup_component(hass, DOMAIN, {DOMAIN: {"host": host}})

    mock_tcp_adapter.assert_called_once_with(host, name="HA", activate_source=False)
    mock_hdmi_network.assert_called_once()
    call_args = mock_hdmi_network.call_args
    expect(call_args).to_equal(call(mock_tcp_adapter.return_value, loop=ANY))
    expect(call_args.kwargs["loop"] in (None, hass.loop)).to_be(True)

    mock_hdmi_network_instance = mock_hdmi_network.return_value

    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    await hass.async_block_till_done()
    mock_hdmi_network_instance.start.assert_called_once_with()
    mock_hdmi_network_instance.set_new_device_callback.assert_called_once()
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STOP)
    await hass.async_block_till_done()
    mock_hdmi_network_instance.stop.assert_called_once_with()


# Test services


@test
async def service_power_on(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    create_hdmi_network: HDMINetworkCreator = Depends(create_hdmi_network),
) -> None:
    """Test the power on service call."""
    mock_hdmi_network_instance = await create_hdmi_network()

    await hass.services.async_call(
        DOMAIN,
        SERVICE_POWER_ON,
        {},
        blocking=True,
    )

    mock_hdmi_network_instance.power_on.assert_called_once_with()


@test
async def service_standby(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    create_hdmi_network: HDMINetworkCreator = Depends(create_hdmi_network),
) -> None:
    """Test the standby service call."""
    mock_hdmi_network_instance = await create_hdmi_network()

    await hass.services.async_call(
        DOMAIN,
        SERVICE_STANDBY,
        {},
        blocking=True,
    )

    mock_hdmi_network_instance.standby.assert_called_once_with()


@test
async def service_select_device_alias(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    create_hdmi_network: HDMINetworkCreator = Depends(create_hdmi_network),
) -> None:
    """Test the select device service call with a known alias."""
    mock_hdmi_network_instance = await create_hdmi_network(
        {"devices": {"Chromecast": "1.0.0.0"}}
    )

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SELECT_DEVICE,
        {"device": "Chromecast"},
        blocking=True,
    )

    mock_hdmi_network_instance.active_source.assert_called_once()
    physical_address = mock_hdmi_network_instance.active_source.call_args.args[0]
    expect(isinstance(physical_address, PhysicalAddress)).to_be(True)
    expect(str(physical_address)).to_equal("1.0.0.0")


class MockCecEntity(MockEntity):
    """Mock CEC entity."""

    @property
    def extra_state_attributes(self):
        """Set the physical address in the attributes."""
        return {"physical_address": self._values["physical_address"]}


@test
async def service_select_device_entity(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    create_hdmi_network: HDMINetworkCreator = Depends(create_hdmi_network),
) -> None:
    """Test the select device service call with an existing entity."""
    platform = MockEntityPlatform(hass)
    await platform.async_add_entities(
        [MockCecEntity(name="hdmi_3", physical_address="3.0.0.0")]
    )

    mock_hdmi_network_instance = await create_hdmi_network()

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SELECT_DEVICE,
        {"device": "test_domain.hdmi_3"},
        blocking=True,
    )

    mock_hdmi_network_instance.active_source.assert_called_once()
    physical_address = mock_hdmi_network_instance.active_source.call_args.args[0]
    expect(isinstance(physical_address, PhysicalAddress)).to_be(True)
    expect(str(physical_address)).to_equal("3.0.0.0")


@test
async def service_select_device_physical_address(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    create_hdmi_network: HDMINetworkCreator = Depends(create_hdmi_network),
) -> None:
    """Test the select device service call with a raw physical address."""
    mock_hdmi_network_instance = await create_hdmi_network()

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SELECT_DEVICE,
        {"device": "1.1.0.0"},
        blocking=True,
    )

    mock_hdmi_network_instance.active_source.assert_called_once()
    physical_address = mock_hdmi_network_instance.active_source.call_args.args[0]
    expect(isinstance(physical_address, PhysicalAddress)).to_be(True)
    expect(str(physical_address)).to_equal("1.1.0.0")


@test
async def service_update_devices(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    create_hdmi_network: HDMINetworkCreator = Depends(create_hdmi_network),
) -> None:
    """Test the update devices service call."""
    mock_hdmi_network_instance = await create_hdmi_network()

    await hass.services.async_call(
        DOMAIN,
        SERVICE_UPDATE_DEVICES,
        {},
        blocking=True,
    )

    mock_hdmi_network_instance.scan.assert_called_once_with()


@test.cases(
    test.case("up_3", count=3, call_count=3, direction="up", key=65),
    test.case("up_1", count=1, call_count=1, direction="up", key=65),
    test.case("up_0", count=0, call_count=0, direction="up", key=65),
    test.case(
        "up_empty_str",
        count="",
        call_count=1,
        direction="up",
        key=65,
        xfail="schema rejects empty string",
    ),
    test.case("down_3", count=3, call_count=3, direction="down", key=66),
    test.case("down_1", count=1, call_count=1, direction="down", key=66),
    test.case("down_0", count=0, call_count=0, direction="down", key=66),
    test.case(
        "down_empty_str",
        count="",
        call_count=1,
        direction="down",
        key=66,
        xfail="schema rejects empty string",
    ),
)
async def service_volume_x_times(
    count: int,
    call_count: int,
    direction: str,
    key: int,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    create_hdmi_network: HDMINetworkCreator = Depends(create_hdmi_network),
) -> None:
    """Test the volume service call with steps."""
    mock_hdmi_network_instance = await create_hdmi_network()

    await hass.services.async_call(
        DOMAIN,
        SERVICE_VOLUME,
        {direction: count},
        blocking=True,
    )

    expect(mock_hdmi_network_instance.send_command.call_count).to_equal(call_count * 2)
    for i in range(call_count):
        assert_key_press_release(
            mock_hdmi_network_instance.send_command, i, dst=5, key=key
        )


@test.cases(
    test.case("up", direction="up", key=65),
    test.case("down", direction="down", key=66),
)
async def service_volume_press(
    direction: str,
    key: int,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    create_hdmi_network: HDMINetworkCreator = Depends(create_hdmi_network),
) -> None:
    """Test the volume service call with press attribute."""
    mock_hdmi_network_instance = await create_hdmi_network()

    await hass.services.async_call(
        DOMAIN,
        SERVICE_VOLUME,
        {direction: "press"},
        blocking=True,
    )

    mock_hdmi_network_instance.send_command.assert_called_once()
    arg = mock_hdmi_network_instance.send_command.call_args.args[0]
    expect(isinstance(arg, KeyPressCommand)).to_be(True)
    expect(arg.key).to_equal(key)
    expect(arg.dst).to_equal(5)


@test.cases(
    test.case("up", direction="up", key=65),
    test.case("down", direction="down", key=66),
)
async def service_volume_release(
    direction: str,
    key: int,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    create_hdmi_network: HDMINetworkCreator = Depends(create_hdmi_network),
) -> None:
    """Test the volume service call with release attribute."""
    mock_hdmi_network_instance = await create_hdmi_network()

    await hass.services.async_call(
        DOMAIN,
        SERVICE_VOLUME,
        {direction: "release"},
        blocking=True,
    )

    mock_hdmi_network_instance.send_command.assert_called_once()
    arg = mock_hdmi_network_instance.send_command.call_args.args[0]
    expect(isinstance(arg, KeyReleaseCommand)).to_be(True)
    expect(arg.dst).to_equal(5)


@test.cases(
    test.case("toggle", attr="toggle", key=67),
    test.case("on", attr="on", key=101),
    test.case("off", attr="off", key=102),
    test.case(
        "empty",
        attr="",
        key=101,
        xfail="schema rejects empty string for mute",
    ),
)
async def service_volume_mute(
    attr: str,
    key: int,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    create_hdmi_network: HDMINetworkCreator = Depends(create_hdmi_network),
) -> None:
    """Test the volume service call with mute."""
    mock_hdmi_network_instance = await create_hdmi_network()

    await hass.services.async_call(
        DOMAIN,
        SERVICE_VOLUME,
        {"mute": attr},
        blocking=True,
    )

    expect(mock_hdmi_network_instance.send_command.call_count).to_equal(2)
    assert_key_press_release(mock_hdmi_network_instance.send_command, key=key, dst=5)


@test.cases(
    test.case("raw", data={"raw": "20:0D"}, expected="20:0d"),
    test.case(
        "cmd_str",
        data={"cmd": "36"},
        expected="ff:36",
        xfail="string is converted to hex value, not as expected",
    ),
    test.case("cmd_int", data={"cmd": 54}, expected="ff:36"),
    test.case(
        "cmd_str_src_dst",
        data={"cmd": "36", "src": "1", "dst": "0"},
        expected="10:36",
        xfail="string is converted to hex value, not as expected",
    ),
    test.case(
        "cmd_int_src_dst",
        data={"cmd": 54, "src": "1", "dst": "0"},
        expected="10:36",
    ),
    test.case(
        "att_raw",
        data={"cmd": "64", "src": "1", "dst": "0", "att": "4f:44"},
        expected="10:64:4f:44",
        xfail="att only accepts int or HEX value",
    ),
    test.case(
        "att_hex_str",
        data={"cmd": "0A", "src": "1", "dst": "0", "att": "1B"},
        expected="10:0a:1b",
        xfail="reduce on string fails",
    ),
    test.case(
        "att_int_str",
        data={"cmd": "0A", "src": "1", "dst": "0", "att": "01"},
        expected="10:0a:1b",
        xfail="reduce on int fails",
    ),
    test.case(
        "att_list",
        data={"cmd": "0A", "src": "1", "dst": "0", "att": ["1B", "44"]},
        expected="10:0a:1b:44",
        xfail="call schema does not allow list passthrough",
    ),
)
async def service_send_command(
    data: dict[str, Any],
    expected: str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    create_hdmi_network: HDMINetworkCreator = Depends(create_hdmi_network),
) -> None:
    """Test the send command service call."""
    mock_hdmi_network_instance = await create_hdmi_network()

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SEND_COMMAND,
        data,
        blocking=True,
    )

    mock_hdmi_network_instance.send_command.assert_called_once()
    command = mock_hdmi_network_instance.send_command.call_args.args[0]
    expect(isinstance(command, CecCommand)).to_be(True)
    expect(str(command)).to_equal(expected)


@test.cases(
    test.case("uninitialized", adapter_initialized_value=False, watchdog_actions=1),
    test.case("initialized", adapter_initialized_value=True, watchdog_actions=0),
)
async def watchdog(
    adapter_initialized_value: bool,
    watchdog_actions: int,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    create_hdmi_network: HDMINetworkCreator = Depends(create_hdmi_network),
    mock_cec_adapter: MagicMock = Depends(mock_cec_adapter),
) -> None:
    """Test the watchdog when adapter is down/up."""
    adapter_initialized = PropertyMock(return_value=adapter_initialized_value)
    events = async_capture_events(hass, EVENT_HDMI_CEC_UNAVAILABLE)

    mock_cec_adapter_instance = mock_cec_adapter.return_value
    type(mock_cec_adapter_instance).initialized = adapter_initialized

    mock_hdmi_network_instance = await create_hdmi_network()

    mock_hdmi_network_instance.set_initialized_callback.assert_called_once()
    callback = mock_hdmi_network_instance.set_initialized_callback.call_args.args[0]
    callback()

    async_fire_time_changed(hass, utcnow() + timedelta(seconds=WATCHDOG_INTERVAL))
    await hass.async_block_till_done()

    adapter_initialized.assert_called_once_with()
    expect(len(events)).to_equal(watchdog_actions)
    expect(mock_cec_adapter_instance.init.call_count).to_equal(watchdog_actions)
