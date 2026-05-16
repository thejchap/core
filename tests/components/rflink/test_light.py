"""Test for RFLink light components.

Test setup of RFLink lights component/platform. State tracking and
control of RFLink switch devices.

"""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.light import ATTR_BRIGHTNESS, Profiles
from homeassistant.components.rflink.entity import EVENT_BUTTON_PRESSED
from homeassistant.const import (
    ATTR_ENTITY_ID,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
)
from homeassistant.core import CoreState, HomeAssistant, State, callback

from .test_init import mock_rflink

from tests.common import mock_restore_cache
from tests.hass_fixtures import hass as hass_fixture, mock_network

DOMAIN = "light"

CONFIG = {
    "rflink": {
        "port": "/dev/ttyABC0",
        "ignore_devices": ["ignore_wildcard_*", "ignore_light"],
    },
    DOMAIN: {
        "platform": "rflink",
        "devices": {
            "protocol_0_0": {"name": "test", "aliases": ["test_alias_0_0"]},
            "dimmable_0_0": {"name": "dim_test", "type": "dimmable"},
            "switchable_0_0": {"name": "switch_test", "type": "switchable"},
        },
    },
}


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Anchor for tryke fixture resolution."""
    return 0


@fixture
def mock_light_profiles() -> Generator[dict]:
    """Mock loading of light profiles (autouse equivalent)."""
    data: dict = {}

    def mock_profiles_class(hass: HomeAssistant) -> Profiles:
        profiles = Profiles(hass)
        profiles.data = data
        profiles.async_initialize = AsyncMock()
        return profiles

    with patch(
        "homeassistant.components.light.Profiles",
        side_effect=mock_profiles_class,
    ):
        yield data


@test
async def default_setup(
    hass: HomeAssistant = Depends(hass_fixture),
    _profiles: dict = Depends(mock_light_profiles),
) -> None:
    """Test all basic functionality of the RFLink switch component."""
    # setup mocking rflink module
    event_callback, create, protocol, _ = await mock_rflink(hass, CONFIG, DOMAIN)

    # make sure arguments are passed
    expect(create.call_args_list[0][1]["ignore"]).to_be_truthy()

    # test default state of light loaded from config
    light_initial = hass.states.get(f"{DOMAIN}.test")
    expect(light_initial.state).to_equal("off")
    expect(light_initial.attributes["assumed_state"]).to_be_truthy()

    # light should follow state of the hardware device by interpreting
    # incoming events for its name and aliases

    # mock incoming command event for this device
    event_callback({"id": "protocol_0_0", "command": "on"})
    await hass.async_block_till_done()

    light_after_first_command = hass.states.get(f"{DOMAIN}.test")
    expect(light_after_first_command.state).to_equal("on")
    # also after receiving first command state not longer has to be assumed
    expect(light_after_first_command.attributes.get("assumed_state")).to_be_falsy()

    # mock incoming command event for this device
    event_callback({"id": "protocol_0_0", "command": "off"})
    await hass.async_block_till_done()

    expect(hass.states.get(f"{DOMAIN}.test").state).to_equal("off")

    # should respond to group command
    event_callback({"id": "protocol_0_0", "command": "allon"})
    await hass.async_block_till_done()

    light_after_first_command = hass.states.get(f"{DOMAIN}.test")
    expect(light_after_first_command.state).to_equal("on")

    # should respond to group command
    event_callback({"id": "protocol_0_0", "command": "alloff"})
    await hass.async_block_till_done()

    expect(hass.states.get(f"{DOMAIN}.test").state).to_equal("off")

    # test following aliases
    # mock incoming command event for this device alias
    event_callback({"id": "test_alias_0_0", "command": "on"})
    await hass.async_block_till_done()

    expect(hass.states.get(f"{DOMAIN}.test").state).to_equal("on")

    # test event for new unconfigured sensor
    event_callback({"id": "protocol2_0_1", "command": "on"})
    await hass.async_block_till_done()

    expect(hass.states.get(f"{DOMAIN}.protocol2_0_1").state).to_equal("on")

    # test changing state from HA propagates to RFLink
    await hass.services.async_call(
        DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: f"{DOMAIN}.test"}
    )
    await hass.async_block_till_done()
    expect(hass.states.get(f"{DOMAIN}.test").state).to_equal("off")
    expect(protocol.send_command_ack.call_args_list[0][0][0]).to_equal("protocol_0_0")
    expect(protocol.send_command_ack.call_args_list[0][0][1]).to_equal("off")

    await hass.services.async_call(
        DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: f"{DOMAIN}.test"}
    )
    await hass.async_block_till_done()
    expect(hass.states.get(f"{DOMAIN}.test").state).to_equal("on")
    expect(protocol.send_command_ack.call_args_list[1][0][1]).to_equal("on")

    # protocols supporting dimming and on/off should create hybrid light entity
    event_callback({"id": "newkaku_0_1", "command": "off"})
    await hass.async_block_till_done()
    await hass.services.async_call(
        DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: f"{DOMAIN}.newkaku_0_1"}
    )
    await hass.async_block_till_done()

    # dimmable should send highest dim level when turning on
    expect(protocol.send_command_ack.call_args_list[2][0][1]).to_equal("15")

    # and send on command for fallback
    expect(protocol.send_command_ack.call_args_list[3][0][1]).to_equal("on")

    await hass.services.async_call(
        DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: f"{DOMAIN}.newkaku_0_1", ATTR_BRIGHTNESS: 128},
    )
    await hass.async_block_till_done()

    expect(protocol.send_command_ack.call_args_list[4][0][1]).to_equal("7")

    await hass.services.async_call(
        DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: f"{DOMAIN}.dim_test", ATTR_BRIGHTNESS: 128},
    )
    await hass.async_block_till_done()

    expect(protocol.send_command_ack.call_args_list[5][0][1]).to_equal("7")


@test
async def firing_bus_event(
    hass: HomeAssistant = Depends(hass_fixture),
    _profiles: dict = Depends(mock_light_profiles),
) -> None:
    """Incoming RFLink command events should be put on the HA event bus."""
    config = {
        "rflink": {"port": "/dev/ttyABC0"},
        DOMAIN: {
            "platform": "rflink",
            "devices": {
                "protocol_0_0": {
                    "name": "test",
                    "aliases": ["test_alias_0_0"],
                    "fire_event": True,
                }
            },
        },
    }

    # setup mocking rflink module
    event_callback, _, _, _ = await mock_rflink(hass, config, DOMAIN)

    calls = []

    @callback
    def listener(event):
        calls.append(event)

    hass.bus.async_listen_once(EVENT_BUTTON_PRESSED, listener)

    # test event for new unconfigured sensor
    event_callback({"id": "protocol_0_0", "command": "off"})
    await hass.async_block_till_done()
    await hass.async_block_till_done()

    expect(calls[0].data).to_equal({"state": "off", "entity_id": f"{DOMAIN}.test"})


@test
async def signal_repetitions(
    hass: HomeAssistant = Depends(hass_fixture),
    _profiles: dict = Depends(mock_light_profiles),
) -> None:
    """Command should be sent amount of configured repetitions."""
    config = {
        "rflink": {"port": "/dev/ttyABC0"},
        DOMAIN: {
            "platform": "rflink",
            "device_defaults": {"signal_repetitions": 3},
            "devices": {
                "protocol_0_0": {"name": "test", "signal_repetitions": 2},
                "protocol_0_1": {"name": "test1"},
                "newkaku_0_1": {"type": "hybrid"},
            },
        },
    }

    # setup mocking rflink module
    event_callback, _, protocol, _ = await mock_rflink(hass, config, DOMAIN)

    # test if signal repetition is performed according to configuration
    await hass.services.async_call(
        DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: f"{DOMAIN}.test"}
    )

    # wait for commands and repetitions to finish
    await hass.async_block_till_done()

    expect(protocol.send_command_ack.call_count).to_equal(2)

    # test if default apply to configured devices
    await hass.services.async_call(
        DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: f"{DOMAIN}.test1"}
    )

    # wait for commands and repetitions to finish
    await hass.async_block_till_done()

    expect(protocol.send_command_ack.call_count).to_equal(5)

    # test if device defaults apply to newly created devices
    event_callback({"id": "protocol_0_2", "command": "off"})

    # make sure entity is created before setting state
    await hass.async_block_till_done()

    await hass.services.async_call(
        DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: f"{DOMAIN}.protocol_0_2"}
    )

    # wait for commands and repetitions to finish
    await hass.async_block_till_done()

    expect(protocol.send_command_ack.call_count).to_equal(8)


@test
async def signal_repetitions_alternation(
    hass: HomeAssistant = Depends(hass_fixture),
    _profiles: dict = Depends(mock_light_profiles),
) -> None:
    """Simultaneously switching entities must alternate repetitions."""
    config = {
        "rflink": {"port": "/dev/ttyABC0"},
        DOMAIN: {
            "platform": "rflink",
            "devices": {
                "protocol_0_0": {"name": "test", "signal_repetitions": 2},
                "protocol_0_1": {"name": "test1", "signal_repetitions": 2},
            },
        },
    }

    # setup mocking rflink module
    _, _, protocol, _ = await mock_rflink(hass, config, DOMAIN)

    await hass.services.async_call(
        DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: f"{DOMAIN}.test"}
    )
    await hass.services.async_call(
        DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: f"{DOMAIN}.test1"}
    )

    await hass.async_block_till_done()

    expect(protocol.send_command_ack.call_args_list[0][0][0]).to_equal("protocol_0_0")
    expect(protocol.send_command_ack.call_args_list[1][0][0]).to_equal("protocol_0_1")
    expect(protocol.send_command_ack.call_args_list[2][0][0]).to_equal("protocol_0_0")
    expect(protocol.send_command_ack.call_args_list[3][0][0]).to_equal("protocol_0_1")


@test
async def signal_repetitions_cancelling(
    hass: HomeAssistant = Depends(hass_fixture),
    _profiles: dict = Depends(mock_light_profiles),
) -> None:
    """Cancel outstanding repetitions when state changed."""
    config = {
        "rflink": {"port": "/dev/ttyABC0"},
        DOMAIN: {
            "platform": "rflink",
            "devices": {"protocol_0_0": {"name": "test", "signal_repetitions": 3}},
        },
    }

    # setup mocking rflink module
    _, _, protocol, _ = await mock_rflink(hass, config, DOMAIN)
    await hass.async_block_till_done()

    await hass.services.async_call(
        DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: f"{DOMAIN}.test"}
    )
    await hass.async_block_till_done()

    await hass.services.async_call(
        DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: f"{DOMAIN}.test"}, blocking=True
    )
    await hass.async_block_till_done()

    expect(
        [call[0][1] for call in protocol.send_command_ack.call_args_list]
    ).to_equal(["off", "off", "off", "on", "on", "on"])


@test
async def type_toggle(
    hass: HomeAssistant = Depends(hass_fixture),
    _profiles: dict = Depends(mock_light_profiles),
) -> None:
    """Test toggle type lights (on/on)."""
    config = {
        "rflink": {"port": "/dev/ttyABC0"},
        DOMAIN: {
            "platform": "rflink",
            "devices": {"toggle_0_0": {"name": "toggle_test", "type": "toggle"}},
        },
    }

    # setup mocking rflink module
    event_callback, _, _, _ = await mock_rflink(hass, config, DOMAIN)

    # default value = 'off'
    expect(hass.states.get(f"{DOMAIN}.toggle_test").state).to_equal("off")

    # test sending 'on' command, must set state = 'on'
    event_callback({"id": "toggle_0_0", "command": "on"})
    await hass.async_block_till_done()

    expect(hass.states.get(f"{DOMAIN}.toggle_test").state).to_equal("on")

    # test sending 'on' command again, must set state = 'off'
    event_callback({"id": "toggle_0_0", "command": "on"})
    await hass.async_block_till_done()

    expect(hass.states.get(f"{DOMAIN}.toggle_test").state).to_equal("off")

    # test async_turn_off, must set state = 'on' ('off' + toggle)
    await hass.services.async_call(
        DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: f"{DOMAIN}.toggle_test"}
    )
    await hass.async_block_till_done()

    expect(hass.states.get(f"{DOMAIN}.toggle_test").state).to_equal("on")

    # test async_turn_on, must set state = 'off' (yes, sounds crazy)
    await hass.services.async_call(
        DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: f"{DOMAIN}.toggle_test"}
    )
    await hass.async_block_till_done()

    expect(hass.states.get(f"{DOMAIN}.toggle_test").state).to_equal("off")


@test
async def set_level_command(
    hass: HomeAssistant = Depends(hass_fixture),
    _profiles: dict = Depends(mock_light_profiles),
) -> None:
    """Test 'set_level=XX' events."""
    config = {
        "rflink": {"port": "/dev/ttyABC0"},
        DOMAIN: {
            "platform": "rflink",
            "devices": {
                "newkaku_12345678_0": {"name": "l1"},
                "test_no_dimmable": {"name": "l2"},
                "test_dimmable": {"name": "l3", "type": "dimmable"},
                "test_hybrid": {"name": "l4", "type": "hybrid"},
            },
        },
    }

    # setup mocking rflink module
    event_callback, _, _, _ = await mock_rflink(hass, config, DOMAIN)

    # test sending command to a newkaku device
    event_callback({"id": "newkaku_12345678_0", "command": "set_level=10"})
    await hass.async_block_till_done()
    # should affect state
    state = hass.states.get(f"{DOMAIN}.l1")
    expect(state).to_be_truthy()
    expect(state.state).to_equal(STATE_ON)
    expect(state.attributes[ATTR_BRIGHTNESS]).to_equal(170)
    # turn off
    event_callback({"id": "newkaku_12345678_0", "command": "off"})
    await hass.async_block_till_done()
    state = hass.states.get(f"{DOMAIN}.l1")
    expect(state).to_be_truthy()
    expect(state.state).to_equal(STATE_OFF)
    # off light shouldn't have brightness
    expect(state.attributes.get(ATTR_BRIGHTNESS)).to_be_falsy()
    # turn on
    event_callback({"id": "newkaku_12345678_0", "command": "on"})
    await hass.async_block_till_done()
    state = hass.states.get(f"{DOMAIN}.l1")
    expect(state).to_be_truthy()
    expect(state.state).to_equal(STATE_ON)
    expect(state.attributes[ATTR_BRIGHTNESS]).to_equal(170)

    # test sending command to a no dimmable device
    event_callback({"id": "test_no_dimmable", "command": "set_level=10"})
    await hass.async_block_till_done()
    # should NOT affect state
    state = hass.states.get(f"{DOMAIN}.l2")
    expect(state).to_be_truthy()
    expect(state.state).to_equal(STATE_OFF)
    expect(state.attributes.get(ATTR_BRIGHTNESS)).to_be_falsy()

    # test sending command to a dimmable device
    event_callback({"id": "test_dimmable", "command": "set_level=5"})
    await hass.async_block_till_done()
    # should affect state
    state = hass.states.get(f"{DOMAIN}.l3")
    expect(state).to_be_truthy()
    expect(state.state).to_equal(STATE_ON)
    expect(state.attributes[ATTR_BRIGHTNESS]).to_equal(85)

    # test sending command to a hybrid device
    event_callback({"id": "test_hybrid", "command": "set_level=15"})
    await hass.async_block_till_done()
    # should affect state
    state = hass.states.get(f"{DOMAIN}.l4")
    expect(state).to_be_truthy()
    expect(state.state).to_equal(STATE_ON)
    expect(state.attributes[ATTR_BRIGHTNESS]).to_equal(255)

    event_callback({"id": "test_hybrid", "command": "off"})
    await hass.async_block_till_done()
    # should affect state
    state = hass.states.get(f"{DOMAIN}.l4")
    expect(state).to_be_truthy()
    expect(state.state).to_equal(STATE_OFF)
    # off light shouldn't have brightness
    expect(state.attributes.get(ATTR_BRIGHTNESS)).to_be_falsy()

    event_callback({"id": "test_hybrid", "command": "set_level=0"})
    await hass.async_block_till_done()
    # should affect state
    state = hass.states.get(f"{DOMAIN}.l4")
    expect(state).to_be_truthy()
    expect(state.state).to_equal(STATE_ON)
    expect(state.attributes[ATTR_BRIGHTNESS]).to_equal(0)


@test
async def group_alias(
    hass: HomeAssistant = Depends(hass_fixture),
    _profiles: dict = Depends(mock_light_profiles),
) -> None:
    """Group aliases should only respond to group commands (allon/alloff)."""
    config = {
        "rflink": {"port": "/dev/ttyABC0"},
        DOMAIN: {
            "platform": "rflink",
            "devices": {
                "protocol_0_0": {"name": "test", "group_aliases": ["test_group_0_0"]},
                "protocol_0_1": {
                    "name": "test2",
                    "type": "dimmable",
                    "group_aliases": ["test_group_0_0"],
                },
            },
        },
    }

    # setup mocking rflink module
    event_callback, _, _, _ = await mock_rflink(hass, config, DOMAIN)

    expect(hass.states.get(f"{DOMAIN}.test").state).to_equal("off")

    # test sending group command to group alias
    event_callback({"id": "test_group_0_0", "command": "allon"})
    await hass.async_block_till_done()

    expect(hass.states.get(f"{DOMAIN}.test").state).to_equal("on")
    expect(hass.states.get(f"{DOMAIN}.test2").state).to_equal("on")

    # test sending group command to group alias
    event_callback({"id": "test_group_0_0", "command": "off"})
    await hass.async_block_till_done()

    expect(hass.states.get(f"{DOMAIN}.test").state).to_equal("on")
    expect(hass.states.get(f"{DOMAIN}.test2").state).to_equal("on")


@test
async def nogroup_alias(
    hass: HomeAssistant = Depends(hass_fixture),
    _profiles: dict = Depends(mock_light_profiles),
) -> None:
    """Non group aliases should not respond to group commands."""
    config = {
        "rflink": {"port": "/dev/ttyABC0"},
        DOMAIN: {
            "platform": "rflink",
            "devices": {
                "protocol_0_0": {
                    "name": "test",
                    "nogroup_aliases": ["test_nogroup_0_0"],
                }
            },
        },
    }

    # setup mocking rflink module
    event_callback, _, _, _ = await mock_rflink(hass, config, DOMAIN)

    expect(hass.states.get(f"{DOMAIN}.test").state).to_equal("off")

    # test sending group command to nogroup alias
    event_callback({"id": "test_nogroup_0_0", "command": "allon"})
    await hass.async_block_till_done()
    # should not affect state
    expect(hass.states.get(f"{DOMAIN}.test").state).to_equal("off")

    # test sending group commands to nogroup alias
    event_callback({"id": "test_nogroup_0_0", "command": "on"})
    await hass.async_block_till_done()
    # should affect state
    expect(hass.states.get(f"{DOMAIN}.test").state).to_equal("on")


@test
async def nogroup_device_id(
    hass: HomeAssistant = Depends(hass_fixture),
    _profiles: dict = Depends(mock_light_profiles),
) -> None:
    """Device id that do not respond to group commands (allon/alloff)."""
    config = {
        "rflink": {"port": "/dev/ttyABC0"},
        DOMAIN: {
            "platform": "rflink",
            "devices": {"test_nogroup_0_0": {"name": "test", "group": False}},
        },
    }

    # setup mocking rflink module
    event_callback, _, _, _ = await mock_rflink(hass, config, DOMAIN)

    expect(hass.states.get(f"{DOMAIN}.test").state).to_equal("off")

    # test sending group command to nogroup
    event_callback({"id": "test_nogroup_0_0", "command": "allon"})
    await hass.async_block_till_done()
    # should not affect state
    expect(hass.states.get(f"{DOMAIN}.test").state).to_equal("off")

    # test sending group command to nogroup
    event_callback({"id": "test_nogroup_0_0", "command": "on"})
    await hass.async_block_till_done()
    # should affect state
    expect(hass.states.get(f"{DOMAIN}.test").state).to_equal("on")


@test
async def disable_automatic_add(
    hass: HomeAssistant = Depends(hass_fixture),
    _profiles: dict = Depends(mock_light_profiles),
) -> None:
    """If disabled new devices should not be automatically added."""
    config = {
        "rflink": {"port": "/dev/ttyABC0"},
        DOMAIN: {"platform": "rflink", "automatic_add": False},
    }

    # setup mocking rflink module
    event_callback, _, _, _ = await mock_rflink(hass, config, DOMAIN)

    # test event for new unconfigured sensor
    event_callback({"id": "protocol_0_0", "command": "off"})
    await hass.async_block_till_done()

    # make sure new device is not added
    expect(hass.states.get(f"{DOMAIN}.protocol_0_0")).to_be_falsy()


@test
async def restore_state(
    hass: HomeAssistant = Depends(hass_fixture),
    _profiles: dict = Depends(mock_light_profiles),
) -> None:
    """Ensure states are restored on startup."""
    config = {
        "rflink": {"port": "/dev/ttyABC0"},
        DOMAIN: {
            "platform": "rflink",
            "devices": {
                "NewKaku_12345678_0": {"name": "l1", "type": "hybrid"},
                "test_restore_2": {"name": "l2"},
                "test_restore_3": {"name": "l3"},
                "test_restore_4": {"name": "l4", "type": "dimmable"},
                "test_restore_5": {"name": "l5", "type": "dimmable"},
            },
        },
    }

    mock_restore_cache(
        hass,
        (
            State(f"{DOMAIN}.l1", STATE_ON, {ATTR_BRIGHTNESS: "123"}),
            State(f"{DOMAIN}.l2", STATE_ON, {ATTR_BRIGHTNESS: "321"}),
            State(f"{DOMAIN}.l3", STATE_OFF),
            State(f"{DOMAIN}.l5", STATE_ON, {ATTR_BRIGHTNESS: "222"}),
        ),
    )

    hass.set_state(CoreState.starting)

    # setup mocking rflink module
    _, _, _, _ = await mock_rflink(hass, config, DOMAIN)

    # hybrid light must restore brightness
    state = hass.states.get(f"{DOMAIN}.l1")
    expect(state).to_be_truthy()
    expect(state.state).to_equal(STATE_ON)
    expect(state.attributes[ATTR_BRIGHTNESS]).to_equal(123)

    # normal light do NOT must restore brightness
    state = hass.states.get(f"{DOMAIN}.l2")
    expect(state).to_be_truthy()
    expect(state.state).to_equal(STATE_ON)
    expect(state.attributes.get(ATTR_BRIGHTNESS)).to_be_falsy()

    # OFF state also restores (or not)
    state = hass.states.get(f"{DOMAIN}.l3")
    expect(state).to_be_truthy()
    expect(state.state).to_equal(STATE_OFF)

    # not cached light must default values
    state = hass.states.get(f"{DOMAIN}.l4")
    expect(state).to_be_truthy()
    expect(state.state).to_equal(STATE_OFF)
    # off light shouldn't have brightness
    expect(state.attributes.get(ATTR_BRIGHTNESS)).to_be_falsy()
    expect(state.attributes["assumed_state"]).to_be_truthy()

    # test coverage for dimmable light
    state = hass.states.get(f"{DOMAIN}.l5")
    expect(state).to_be_truthy()
    expect(state.state).to_equal(STATE_ON)
    expect(state.attributes[ATTR_BRIGHTNESS]).to_equal(222)
