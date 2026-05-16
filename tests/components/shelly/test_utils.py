"""Tests for Shelly utils."""

from collections.abc import Generator
from contextlib import contextmanager
from typing import Any
from unittest.mock import AsyncMock, Mock

from aiohttp.web import Request
from aioshelly.const import (
    MODEL_1,
    MODEL_1L,
    MODEL_BUTTON1,
    MODEL_BUTTON1_V2,
    MODEL_DIMMER_2,
    MODEL_I3,
    MODEL_MOTION,
    MODEL_PLUS_2PM_V2,
    MODEL_WALL_DISPLAY,
)
from aioshelly.rpc_device import WsServer
from tryke import Depends, expect, fixture, test

from homeassistant.components.shelly.const import (
    GEN1_RELEASE_URL,
    GEN2_BETA_RELEASE_URL,
    GEN2_RELEASE_URL,
    WALL_DISPLAY_RELEASE_URL,
)
from homeassistant.components.shelly.utils import (
    ShellyReceiver,
    get_block_device_sleep_period,
    get_block_input_triggers,
    get_block_number_of_channels,
    get_host,
    get_release_url,
    get_rpc_channel_name,
    get_rpc_input_triggers,
    get_rpc_sub_device_name,
    is_block_momentary_input,
    mac_address_from_name,
)

from tests.components.shelly._fixtures import (
    mock_block_device as mock_block_device_fixture,
    mock_rpc_device as mock_rpc_device_fixture,
)

DEVICE_BLOCK_ID = 4

_MISSING = object()


@contextmanager
def _patches() -> Generator[Any]:
    """Mimic pytest's monkeypatch for setattr/setitem/delitem."""

    undo: list[Any] = []

    class _Patcher:
        def setattr(self, target: Any, name: str, value: Any) -> None:
            original = getattr(target, name, _MISSING)
            undo.append(("attr", target, name, original))
            setattr(target, name, value)

        def setitem(self, mapping: Any, key: Any, value: Any) -> None:
            original = mapping.get(key, _MISSING)
            undo.append(("item", mapping, key, original))
            mapping[key] = value

        def delitem(self, mapping: Any, key: Any) -> None:
            original = mapping.get(key, _MISSING)
            undo.append(("item", mapping, key, original))
            del mapping[key]

    try:
        yield _Patcher()
    finally:
        for kind, obj, key, original in reversed(undo):
            if kind == "attr":
                if original is _MISSING:
                    try:
                        delattr(obj, key)
                    except AttributeError:
                        pass
                else:
                    setattr(obj, key, original)
            else:
                if original is _MISSING:
                    obj.pop(key, None)
                else:
                    obj[key] = original


@fixture
def _trigger_executor() -> int:
    """Anchor fixture so async Depends() fixtures resolve under tryke."""
    return 0


@test
async def block_get_block_number_of_channels(
    _t: int = Depends(_trigger_executor),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
) -> None:
    """Test block get block number of channels."""
    with _patches() as monkeypatch:
        monkeypatch.setattr(mock_block_device.blocks[DEVICE_BLOCK_ID], "type", "emeter")
        monkeypatch.setitem(mock_block_device.shelly, "num_emeters", 3)

        expect(
            get_block_number_of_channels(
                mock_block_device,
                mock_block_device.blocks[DEVICE_BLOCK_ID],
            )
        ).to_be(3)

        monkeypatch.setitem(mock_block_device.shelly, "num_inputs", 4)
        monkeypatch.setattr(mock_block_device.blocks[DEVICE_BLOCK_ID], "type", "input")
        expect(
            get_block_number_of_channels(
                mock_block_device,
                mock_block_device.blocks[DEVICE_BLOCK_ID],
            )
        ).to_be(4)

        monkeypatch.setitem(
            mock_block_device.settings["device"], "type", MODEL_DIMMER_2
        )
        expect(
            get_block_number_of_channels(
                mock_block_device,
                mock_block_device.blocks[DEVICE_BLOCK_ID],
            )
        ).to_be(2)


@test
async def is_block_momentary_input_test(
    _t: int = Depends(_trigger_executor),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
) -> None:
    """Test is block momentary input."""
    with _patches() as monkeypatch:
        monkeypatch.setattr(mock_block_device.blocks[DEVICE_BLOCK_ID], "type", "relay")

        monkeypatch.setitem(mock_block_device.settings, "mode", "roller")
        monkeypatch.setitem(
            mock_block_device.settings, "rollers", [{"button_type": "detached"}]
        )
        expect(
            is_block_momentary_input(
                mock_block_device.settings,
                mock_block_device.blocks[DEVICE_BLOCK_ID],
            )
        ).to_be(False)
        expect(
            is_block_momentary_input(
                mock_block_device.settings,
                mock_block_device.blocks[DEVICE_BLOCK_ID],
                True,
            )
        ).to_be(True)

        monkeypatch.setitem(mock_block_device.settings, "mode", "relay")
        monkeypatch.setitem(mock_block_device.settings["device"], "type", MODEL_1L)
        expect(
            is_block_momentary_input(
                mock_block_device.settings,
                mock_block_device.blocks[DEVICE_BLOCK_ID],
                True,
            )
        ).to_be(False)

        monkeypatch.delitem(mock_block_device.settings, "inputs")
        monkeypatch.delitem(mock_block_device.settings, "relays")
        monkeypatch.delitem(mock_block_device.settings, "rollers")
        expect(
            is_block_momentary_input(
                mock_block_device.settings,
                mock_block_device.blocks[DEVICE_BLOCK_ID],
            )
        ).to_be(False)

        monkeypatch.setitem(
            mock_block_device.settings["device"], "type", MODEL_BUTTON1_V2
        )

        expect(
            is_block_momentary_input(
                mock_block_device.settings,
                mock_block_device.blocks[DEVICE_BLOCK_ID],
            )
        ).to_be(True)


@test.cases(
    test.case("empty", settings={}, sleep_period=0),
    test.case(
        "minutes",
        settings={"sleep_mode": {"period": 1000, "unit": "m"}},
        sleep_period=1000 * 60,
    ),
    test.case(
        "hours",
        settings={"sleep_mode": {"period": 5, "unit": "h"}},
        sleep_period=5 * 3600,
    ),
)
async def get_block_device_sleep_period_test(
    settings: dict[str, Any], sleep_period: int
) -> None:
    """Test get block device sleep period."""
    expect(get_block_device_sleep_period(settings)).to_equal(sleep_period)


@test
async def get_block_input_triggers_test(
    _t: int = Depends(_trigger_executor),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
) -> None:
    """Test get block input triggers."""
    with _patches() as monkeypatch:
        monkeypatch.setattr(
            mock_block_device.blocks[DEVICE_BLOCK_ID],
            "sensor_ids",
            {"inputEvent": "S", "inputEventCnt": 0},
        )
        monkeypatch.setitem(
            mock_block_device.settings, "rollers", [{"button_type": "detached"}]
        )
        expect(
            set(
                get_block_input_triggers(
                    mock_block_device, mock_block_device.blocks[DEVICE_BLOCK_ID]
                )
            )
        ).to_equal({("long", "button"), ("single", "button")})

        monkeypatch.setitem(mock_block_device.settings["device"], "type", MODEL_BUTTON1)
        expect(
            set(
                get_block_input_triggers(
                    mock_block_device, mock_block_device.blocks[DEVICE_BLOCK_ID]
                )
            )
        ).to_equal(
            {
                ("long", "button"),
                ("double", "button"),
                ("single", "button"),
                ("triple", "button"),
            }
        )

        monkeypatch.setitem(mock_block_device.settings["device"], "type", MODEL_I3)
        expect(
            set(
                get_block_input_triggers(
                    mock_block_device, mock_block_device.blocks[DEVICE_BLOCK_ID]
                )
            )
        ).to_equal(
            {
                ("long_single", "button"),
                ("single_long", "button"),
                ("triple", "button"),
                ("long", "button"),
                ("single", "button"),
                ("double", "button"),
            }
        )


@test
async def get_rpc_channel_name_test(
    _t: int = Depends(_trigger_executor),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test get RPC channel name."""
    expect(get_rpc_channel_name(mock_rpc_device, "input:0")).to_equal("Test input 0")
    expect(get_rpc_channel_name(mock_rpc_device, "input:3")).to_equal("Input 3")


@test.cases(
    test.case("cover", component="cover", expected=None),
    test.case("light", component="light", expected=None),
    test.case("rgb", component="rgb", expected=None),
    test.case("rgbw", component="rgbw", expected=None),
    test.case("switch", component="switch", expected=None),
    test.case("thermostat", component="thermostat", expected=None),
)
async def get_rpc_channel_name_multiple_components(
    component: str,
    expected: str | None,
    _t: int = Depends(_trigger_executor),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test get RPC channel name when there is more components of the same type."""
    with _patches() as monkeypatch:
        config = {
            f"{component}:0": {"name": None},
            f"{component}:1": {"name": None},
        }
        monkeypatch.setattr(mock_rpc_device, "config", config)

        expect(get_rpc_channel_name(mock_rpc_device, f"{component}:0")).to_be(expected)
        expect(get_rpc_channel_name(mock_rpc_device, f"{component}:1")).to_be(expected)


@test
async def get_rpc_input_triggers_test(
    _t: int = Depends(_trigger_executor),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test get RPC input triggers."""
    with _patches() as monkeypatch:
        monkeypatch.setattr(mock_rpc_device, "config", {"input:0": {"type": "button"}})
        expect(set(get_rpc_input_triggers(mock_rpc_device))).to_equal(
            {
                ("btn_down", "button1"),
                ("btn_up", "button1"),
                ("single_push", "button1"),
                ("double_push", "button1"),
                ("triple_push", "button1"),
                ("long_push", "button1"),
            }
        )

        monkeypatch.setattr(mock_rpc_device, "config", {"input:0": {"type": "switch"}})
        expect(bool(get_rpc_input_triggers(mock_rpc_device))).to_be(False)


@test.cases(
    test.case("motion_gen1", gen=1, model=MODEL_MOTION, beta=False, expected=None),
    test.case("model_1_stable", gen=1, model=MODEL_1, beta=False, expected=GEN1_RELEASE_URL),
    test.case("model_1_beta", gen=1, model=MODEL_1, beta=True, expected=None),
    test.case(
        "wall_display",
        gen=2,
        model=MODEL_WALL_DISPLAY,
        beta=False,
        expected=WALL_DISPLAY_RELEASE_URL,
    ),
    test.case(
        "plus_2pm_v2_stable",
        gen=2,
        model=MODEL_PLUS_2PM_V2,
        beta=False,
        expected=GEN2_RELEASE_URL,
    ),
    test.case(
        "plus_2pm_v2_beta",
        gen=2,
        model=MODEL_PLUS_2PM_V2,
        beta=True,
        expected=GEN2_BETA_RELEASE_URL,
    ),
)
def get_release_url_test(
    gen: int, model: str, beta: bool, expected: str | None
) -> None:
    """Test get_release_url() with a device without a release note URL."""
    result = get_release_url(gen, model, beta)

    expect(result).to_be(expected)


@test.cases(
    test.case(
        "hostname",
        host="shelly_device.local",
        expected="shelly_device.local",
    ),
    test.case("ipv4", host="192.168.178.12", expected="192.168.178.12"),
    test.case(
        "ipv6",
        host="2001:0db8:85a3:0000:0000:8a2e:0370:7334",
        expected="[2001:0db8:85a3:0000:0000:8a2e:0370:7334]",
    ),
)
def get_host_test(host: str, expected: str) -> None:
    """Test get_host function."""
    expect(get_host(host)).to_equal(expected)


@test.cases(
    test.case(
        "mac_in_name",
        name="shelly1pm-AABBCCDDEEFF",
        result="AABBCCDDEEFF",
    ),
    test.case("bracketed", name="Shelly Plus 1 [DDEEFF]", result=None),
    test.case("schlafzimmer", name="S11-Schlafzimmer", result=None),
    test.case("kueche", name="22-Kueche-links", result=None),
)
def mac_address_from_name_test(name: str, result: str | None) -> None:
    """Test mac_address_from_name() function."""
    expect(mac_address_from_name(name)).to_equal(result)


@test
async def shelly_receiver_get(
    _t: int = Depends(_trigger_executor),
) -> None:
    """Test ShellyReceiver get method."""
    ws_server = Mock(spec=WsServer)
    ws_server.websocket_handler = AsyncMock(return_value="test_response")
    receiver = ShellyReceiver(ws_server)
    mock_request = Mock(spec=Request)

    response = await receiver.get(mock_request)

    ws_server.websocket_handler.assert_awaited_once_with(mock_request)
    expect(response).to_equal("test_response")


@test.cases(
    test.case("switch_0", key="switch:0", expected="Test name Output 0"),
    test.case("switch_1", key="switch:1", expected="Test name Output 1"),
    test.case("cover_0", key="cover:0", expected="Test name Cover 0"),
    test.case("light_0", key="light:0", expected="Test name Light 0"),
    test.case("rgb_0", key="rgb:0", expected="Test name RGB light 0"),
    test.case("rgbw_1", key="rgbw:1", expected="Test name RGBW light 1"),
    test.case("cct_0", key="cct:0", expected="Test name CCT light 0"),
    test.case("em1_0", key="em1:0", expected="Test name Energy Meter 0"),
)
async def get_rpc_sub_device_name_test(
    key: str,
    expected: str,
    _t: int = Depends(_trigger_executor),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test get RPC sub-device name."""
    with _patches() as monkeypatch:
        config = {key: {"name": None}}
        monkeypatch.setattr(mock_rpc_device, "config", config)

        expect(get_rpc_sub_device_name(mock_rpc_device, key)).to_equal(expected)


@test
async def get_rpc_sub_device_name_with_custom_name(
    _t: int = Depends(_trigger_executor),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test get RPC sub-device name with custom name."""
    with _patches() as monkeypatch:
        config = {"switch:0": {"name": "My Custom Output"}}
        monkeypatch.setattr(mock_rpc_device, "config", config)

        expect(get_rpc_sub_device_name(mock_rpc_device, "switch:0")).to_equal(
            "My Custom Output"
        )


@test
async def get_rpc_sub_device_name_with_emeter_phase(
    _t: int = Depends(_trigger_executor),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test get RPC sub-device name with emeter phase."""
    with _patches() as monkeypatch:
        config = {"em:0": {"name": None}}
        monkeypatch.setattr(mock_rpc_device, "config", config)

        expect(get_rpc_sub_device_name(mock_rpc_device, "em:0", "A")).to_equal(
            "Test name Phase A"
        )
        expect(get_rpc_sub_device_name(mock_rpc_device, "em:0", "B")).to_equal(
            "Test name Phase B"
        )
