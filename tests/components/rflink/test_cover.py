"""Test for RFLink cover components.

Test setup of RFLink covers component/platform. State tracking and
control of RFLink cover devices.

"""

from tryke import Depends, expect, fixture, test

from homeassistant.components.cover import CoverState
from homeassistant.components.rflink.entity import EVENT_BUTTON_PRESSED
from homeassistant.const import ATTR_ENTITY_ID, SERVICE_CLOSE_COVER, SERVICE_OPEN_COVER
from homeassistant.core import CoreState, HomeAssistant, State, callback

from .test_init import mock_rflink

from tests.common import mock_restore_cache
from tests.hass_fixtures import hass as hass_fixture, mock_network

DOMAIN = "cover"

CONFIG = {
    "rflink": {
        "port": "/dev/ttyABC0",
        "ignore_devices": ["ignore_wildcard_*", "ignore_cover"],
    },
    DOMAIN: {
        "platform": "rflink",
        "devices": {
            "protocol_0_0": {"name": "test", "aliases": ["test_alias_0_0"]},
            "cover_0_0": {"name": "dim_test"},
            "cover_0_1": {"name": "cover_test"},
        },
    },
}


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Anchor for tryke fixture resolution."""
    return 0


@test
async def default_setup(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test all basic functionality of the RFLink cover component."""
    # setup mocking rflink module
    event_callback, create, protocol, _ = await mock_rflink(hass, CONFIG, DOMAIN)

    # make sure arguments are passed
    expect(create.call_args_list[0][1]["ignore"]).to_be_truthy()

    # test default state of cover loaded from config
    cover_initial = hass.states.get(f"{DOMAIN}.test")
    expect(cover_initial.state).to_equal(CoverState.CLOSED)
    expect(cover_initial.attributes["assumed_state"]).to_be_truthy()

    # cover should follow state of the hardware device by interpreting
    # incoming events for its name and aliases

    # mock incoming command event for this device
    event_callback({"id": "protocol_0_0", "command": "up"})
    await hass.async_block_till_done()

    cover_after_first_command = hass.states.get(f"{DOMAIN}.test")
    expect(cover_after_first_command.state).to_equal(CoverState.OPEN)
    # not sure why, but cover have always assumed_state=true
    expect(cover_after_first_command.attributes.get("assumed_state")).to_be_truthy()

    # mock incoming command event for this device
    event_callback({"id": "protocol_0_0", "command": "down"})
    await hass.async_block_till_done()

    expect(hass.states.get(f"{DOMAIN}.test").state).to_equal(CoverState.CLOSED)

    # should respond to group command
    event_callback({"id": "protocol_0_0", "command": "allon"})
    await hass.async_block_till_done()

    cover_after_first_command = hass.states.get(f"{DOMAIN}.test")
    expect(cover_after_first_command.state).to_equal(CoverState.OPEN)

    # should respond to group command
    event_callback({"id": "protocol_0_0", "command": "alloff"})
    await hass.async_block_till_done()

    expect(hass.states.get(f"{DOMAIN}.test").state).to_equal(CoverState.CLOSED)

    # test following aliases
    # mock incoming command event for this device alias
    event_callback({"id": "test_alias_0_0", "command": "up"})
    await hass.async_block_till_done()

    expect(hass.states.get(f"{DOMAIN}.test").state).to_equal(CoverState.OPEN)

    # test changing state from HA propagates to RFLink
    await hass.services.async_call(
        DOMAIN, SERVICE_CLOSE_COVER, {ATTR_ENTITY_ID: f"{DOMAIN}.test"}
    )
    await hass.async_block_till_done()
    expect(hass.states.get(f"{DOMAIN}.test").state).to_equal(CoverState.CLOSED)
    expect(protocol.send_command_ack.call_args_list[0][0][0]).to_equal("protocol_0_0")
    expect(protocol.send_command_ack.call_args_list[0][0][1]).to_equal("DOWN")

    await hass.services.async_call(
        DOMAIN, SERVICE_OPEN_COVER, {ATTR_ENTITY_ID: f"{DOMAIN}.test"}
    )
    await hass.async_block_till_done()
    expect(hass.states.get(f"{DOMAIN}.test").state).to_equal(CoverState.OPEN)
    expect(protocol.send_command_ack.call_args_list[1][0][1]).to_equal("UP")


@test
async def firing_bus_event(
    hass: HomeAssistant = Depends(hass_fixture),
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
    event_callback({"id": "protocol_0_0", "command": "down"})
    await hass.async_block_till_done()
    await hass.async_block_till_done()

    expect(calls[0].data).to_equal({"state": "down", "entity_id": f"{DOMAIN}.test"})


@test
async def signal_repetitions(
    hass: HomeAssistant = Depends(hass_fixture),
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
            },
        },
    }

    # setup mocking rflink module
    _, _, protocol, _ = await mock_rflink(hass, config, DOMAIN)

    # test if signal repetition is performed according to configuration
    await hass.services.async_call(
        DOMAIN, SERVICE_OPEN_COVER, {ATTR_ENTITY_ID: f"{DOMAIN}.test"}
    )

    # wait for commands and repetitions to finish
    await hass.async_block_till_done()

    expect(protocol.send_command_ack.call_count).to_equal(2)

    # test if default apply to configured devices
    await hass.services.async_call(
        DOMAIN, SERVICE_OPEN_COVER, {ATTR_ENTITY_ID: f"{DOMAIN}.test1"}
    )

    # wait for commands and repetitions to finish
    await hass.async_block_till_done()

    expect(protocol.send_command_ack.call_count).to_equal(5)


@test
async def signal_repetitions_alternation(
    hass: HomeAssistant = Depends(hass_fixture),
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
        DOMAIN, SERVICE_CLOSE_COVER, {ATTR_ENTITY_ID: f"{DOMAIN}.test"}
    )
    await hass.services.async_call(
        DOMAIN, SERVICE_CLOSE_COVER, {ATTR_ENTITY_ID: f"{DOMAIN}.test1"}
    )

    await hass.async_block_till_done()

    expect(protocol.send_command_ack.call_args_list[0][0][0]).to_equal("protocol_0_0")
    expect(protocol.send_command_ack.call_args_list[1][0][0]).to_equal("protocol_0_1")
    expect(protocol.send_command_ack.call_args_list[2][0][0]).to_equal("protocol_0_0")
    expect(protocol.send_command_ack.call_args_list[3][0][0]).to_equal("protocol_0_1")


@test
async def signal_repetitions_cancelling(
    hass: HomeAssistant = Depends(hass_fixture),
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

    await hass.services.async_call(
        DOMAIN, SERVICE_CLOSE_COVER, {ATTR_ENTITY_ID: f"{DOMAIN}.test"}
    )

    await hass.services.async_call(
        DOMAIN, SERVICE_OPEN_COVER, {ATTR_ENTITY_ID: f"{DOMAIN}.test"}
    )

    await hass.async_block_till_done()

    expect(protocol.send_command_ack.call_args_list[0][0][1]).to_equal("DOWN")
    expect(protocol.send_command_ack.call_args_list[1][0][1]).to_equal("UP")
    expect(protocol.send_command_ack.call_args_list[2][0][1]).to_equal("UP")
    expect(protocol.send_command_ack.call_args_list[3][0][1]).to_equal("UP")


@test
async def group_alias(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Group aliases should only respond to group commands (allon/alloff)."""
    config = {
        "rflink": {"port": "/dev/ttyABC0"},
        DOMAIN: {
            "platform": "rflink",
            "devices": {
                "protocol_0_0": {"name": "test", "group_aliases": ["test_group_0_0"]}
            },
        },
    }

    # setup mocking rflink module
    event_callback, _, _, _ = await mock_rflink(hass, config, DOMAIN)

    expect(hass.states.get(f"{DOMAIN}.test").state).to_equal(CoverState.CLOSED)

    # test sending group command to group alias
    event_callback({"id": "test_group_0_0", "command": "allon"})
    await hass.async_block_till_done()

    expect(hass.states.get(f"{DOMAIN}.test").state).to_equal(CoverState.OPEN)

    # test sending group command to group alias
    event_callback({"id": "test_group_0_0", "command": "down"})
    await hass.async_block_till_done()

    expect(hass.states.get(f"{DOMAIN}.test").state).to_equal(CoverState.OPEN)


@test
async def nogroup_alias(
    hass: HomeAssistant = Depends(hass_fixture),
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

    expect(hass.states.get(f"{DOMAIN}.test").state).to_equal(CoverState.CLOSED)

    # test sending group command to nogroup alias
    event_callback({"id": "test_nogroup_0_0", "command": "allon"})
    await hass.async_block_till_done()
    # should not affect state
    expect(hass.states.get(f"{DOMAIN}.test").state).to_equal(CoverState.CLOSED)

    # test sending group command to nogroup alias
    event_callback({"id": "test_nogroup_0_0", "command": "up"})
    await hass.async_block_till_done()
    # should affect state
    expect(hass.states.get(f"{DOMAIN}.test").state).to_equal(CoverState.OPEN)


@test
async def nogroup_device_id(
    hass: HomeAssistant = Depends(hass_fixture),
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

    expect(hass.states.get(f"{DOMAIN}.test").state).to_equal(CoverState.CLOSED)

    # test sending group command to nogroup
    event_callback({"id": "test_nogroup_0_0", "command": "allon"})
    await hass.async_block_till_done()
    # should not affect state
    expect(hass.states.get(f"{DOMAIN}.test").state).to_equal(CoverState.CLOSED)

    # test sending group command to nogroup
    event_callback({"id": "test_nogroup_0_0", "command": "up"})
    await hass.async_block_till_done()
    # should affect state
    expect(hass.states.get(f"{DOMAIN}.test").state).to_equal(CoverState.OPEN)


@test
async def restore_state(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Ensure states are restored on startup."""
    config = {
        "rflink": {"port": "/dev/ttyABC0"},
        DOMAIN: {
            "platform": "rflink",
            "devices": {
                "RTS_12345678_0": {"name": "c1"},
                "test_restore_2": {"name": "c2"},
                "test_restore_3": {"name": "c3"},
                "test_restore_4": {"name": "c4"},
            },
        },
    }

    mock_restore_cache(
        hass,
        (
            State(f"{DOMAIN}.c1", CoverState.OPEN),
            State(f"{DOMAIN}.c2", CoverState.CLOSED),
        ),
    )

    hass.set_state(CoreState.starting)

    # setup mocking rflink module
    _, _, _, _ = await mock_rflink(hass, config, DOMAIN)

    state = hass.states.get(f"{DOMAIN}.c1")
    expect(state).to_be_truthy()
    expect(state.state).to_equal(CoverState.OPEN)

    state = hass.states.get(f"{DOMAIN}.c2")
    expect(state).to_be_truthy()
    expect(state.state).to_equal(CoverState.CLOSED)

    state = hass.states.get(f"{DOMAIN}.c3")
    expect(state).to_be_truthy()
    expect(state.state).to_equal(CoverState.CLOSED)

    # not cached cover must default values
    state = hass.states.get(f"{DOMAIN}.c4")
    expect(state).to_be_truthy()
    expect(state.state).to_equal(CoverState.CLOSED)
    expect(state.attributes["assumed_state"]).to_be_truthy()


# The code checks the ID, it will use the
# 'inverted' class when the name starts with
# 'newkaku'
@test
async def inverted_cover(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Ensure states are restored on startup."""
    config = {
        "rflink": {"port": "/dev/ttyABC0"},
        DOMAIN: {
            "platform": "rflink",
            "devices": {
                "nonkaku_device_1": {
                    "name": "nonkaku_type_standard",
                    "type": "standard",
                },
                "nonkaku_device_2": {"name": "nonkaku_type_none"},
                "nonkaku_device_3": {
                    "name": "nonkaku_type_inverted",
                    "type": "inverted",
                },
                "newkaku_device_4": {
                    "name": "newkaku_type_standard",
                    "type": "standard",
                },
                "newkaku_device_5": {"name": "newkaku_type_none"},
                "newkaku_device_6": {
                    "name": "newkaku_type_inverted",
                    "type": "inverted",
                },
            },
        },
    }

    # setup mocking rflink module
    event_callback, _, protocol, _ = await mock_rflink(hass, config, DOMAIN)

    # test default state of cover loaded from config
    standard_cover = hass.states.get(f"{DOMAIN}.nonkaku_type_standard")
    expect(standard_cover.state).to_equal(CoverState.CLOSED)
    expect(standard_cover.attributes["assumed_state"]).to_be_truthy()

    # mock incoming up command event for nonkaku_device_1
    event_callback({"id": "nonkaku_device_1", "command": "up"})
    await hass.async_block_till_done()

    standard_cover = hass.states.get(f"{DOMAIN}.nonkaku_type_standard")
    expect(standard_cover.state).to_equal(CoverState.OPEN)
    expect(standard_cover.attributes.get("assumed_state")).to_be_truthy()

    # mock incoming up command event for nonkaku_device_2
    event_callback({"id": "nonkaku_device_2", "command": "up"})
    await hass.async_block_till_done()

    standard_cover = hass.states.get(f"{DOMAIN}.nonkaku_type_none")
    expect(standard_cover.state).to_equal(CoverState.OPEN)
    expect(standard_cover.attributes.get("assumed_state")).to_be_truthy()

    # mock incoming up command event for nonkaku_device_3
    event_callback({"id": "nonkaku_device_3", "command": "up"})

    await hass.async_block_till_done()

    inverted_cover = hass.states.get(f"{DOMAIN}.nonkaku_type_inverted")
    expect(inverted_cover.state).to_equal(CoverState.OPEN)
    expect(inverted_cover.attributes.get("assumed_state")).to_be_truthy()

    # mock incoming up command event for newkaku_device_4
    event_callback({"id": "newkaku_device_4", "command": "up"})

    await hass.async_block_till_done()

    inverted_cover = hass.states.get(f"{DOMAIN}.newkaku_type_standard")
    expect(inverted_cover.state).to_equal(CoverState.OPEN)
    expect(inverted_cover.attributes.get("assumed_state")).to_be_truthy()

    # mock incoming up command event for newkaku_device_5
    event_callback({"id": "newkaku_device_5", "command": "up"})

    await hass.async_block_till_done()

    inverted_cover = hass.states.get(f"{DOMAIN}.newkaku_type_none")
    expect(inverted_cover.state).to_equal(CoverState.OPEN)
    expect(inverted_cover.attributes.get("assumed_state")).to_be_truthy()

    # mock incoming up command event for newkaku_device_6
    event_callback({"id": "newkaku_device_6", "command": "up"})

    await hass.async_block_till_done()

    inverted_cover = hass.states.get(f"{DOMAIN}.newkaku_type_inverted")
    expect(inverted_cover.state).to_equal(CoverState.OPEN)
    expect(inverted_cover.attributes.get("assumed_state")).to_be_truthy()

    # mock incoming down command event for nonkaku_device_1
    event_callback({"id": "nonkaku_device_1", "command": "down"})

    await hass.async_block_till_done()

    standard_cover = hass.states.get(f"{DOMAIN}.nonkaku_type_standard")
    expect(standard_cover.state).to_equal(CoverState.CLOSED)
    expect(standard_cover.attributes.get("assumed_state")).to_be_truthy()

    # mock incoming down command event for nonkaku_device_2
    event_callback({"id": "nonkaku_device_2", "command": "down"})

    await hass.async_block_till_done()

    standard_cover = hass.states.get(f"{DOMAIN}.nonkaku_type_none")
    expect(standard_cover.state).to_equal(CoverState.CLOSED)
    expect(standard_cover.attributes.get("assumed_state")).to_be_truthy()

    # mock incoming down command event for nonkaku_device_3
    event_callback({"id": "nonkaku_device_3", "command": "down"})

    await hass.async_block_till_done()

    inverted_cover = hass.states.get(f"{DOMAIN}.nonkaku_type_inverted")
    expect(inverted_cover.state).to_equal(CoverState.CLOSED)
    expect(inverted_cover.attributes.get("assumed_state")).to_be_truthy()

    # mock incoming down command event for newkaku_device_4
    event_callback({"id": "newkaku_device_4", "command": "down"})

    await hass.async_block_till_done()

    inverted_cover = hass.states.get(f"{DOMAIN}.newkaku_type_standard")
    expect(inverted_cover.state).to_equal(CoverState.CLOSED)
    expect(inverted_cover.attributes.get("assumed_state")).to_be_truthy()

    # mock incoming down command event for newkaku_device_5
    event_callback({"id": "newkaku_device_5", "command": "down"})

    await hass.async_block_till_done()

    inverted_cover = hass.states.get(f"{DOMAIN}.newkaku_type_none")
    expect(inverted_cover.state).to_equal(CoverState.CLOSED)
    expect(inverted_cover.attributes.get("assumed_state")).to_be_truthy()

    # mock incoming down command event for newkaku_device_6
    event_callback({"id": "newkaku_device_6", "command": "down"})

    await hass.async_block_till_done()

    inverted_cover = hass.states.get(f"{DOMAIN}.newkaku_type_inverted")
    expect(inverted_cover.state).to_equal(CoverState.CLOSED)
    expect(inverted_cover.attributes.get("assumed_state")).to_be_truthy()

    # We are only testing the 'inverted' devices, the 'standard' devices
    # are already covered by other test cases.

    # should respond to group command
    event_callback({"id": "nonkaku_device_3", "command": "alloff"})

    await hass.async_block_till_done()

    inverted_cover = hass.states.get(f"{DOMAIN}.nonkaku_type_inverted")
    expect(inverted_cover.state).to_equal(CoverState.CLOSED)

    # should respond to group command
    event_callback({"id": "nonkaku_device_3", "command": "allon"})

    await hass.async_block_till_done()

    inverted_cover = hass.states.get(f"{DOMAIN}.nonkaku_type_inverted")
    expect(inverted_cover.state).to_equal(CoverState.OPEN)

    # should respond to group command
    event_callback({"id": "newkaku_device_4", "command": "alloff"})

    await hass.async_block_till_done()

    inverted_cover = hass.states.get(f"{DOMAIN}.newkaku_type_standard")
    expect(inverted_cover.state).to_equal(CoverState.CLOSED)

    # should respond to group command
    event_callback({"id": "newkaku_device_4", "command": "allon"})

    await hass.async_block_till_done()

    inverted_cover = hass.states.get(f"{DOMAIN}.newkaku_type_standard")
    expect(inverted_cover.state).to_equal(CoverState.OPEN)

    # should respond to group command
    event_callback({"id": "newkaku_device_5", "command": "alloff"})

    await hass.async_block_till_done()

    inverted_cover = hass.states.get(f"{DOMAIN}.newkaku_type_none")
    expect(inverted_cover.state).to_equal(CoverState.CLOSED)

    # should respond to group command
    event_callback({"id": "newkaku_device_5", "command": "allon"})

    await hass.async_block_till_done()

    inverted_cover = hass.states.get(f"{DOMAIN}.newkaku_type_none")
    expect(inverted_cover.state).to_equal(CoverState.OPEN)

    # should respond to group command
    event_callback({"id": "newkaku_device_6", "command": "alloff"})

    await hass.async_block_till_done()

    inverted_cover = hass.states.get(f"{DOMAIN}.newkaku_type_inverted")
    expect(inverted_cover.state).to_equal(CoverState.CLOSED)

    # should respond to group command
    event_callback({"id": "newkaku_device_6", "command": "allon"})

    await hass.async_block_till_done()

    inverted_cover = hass.states.get(f"{DOMAIN}.newkaku_type_inverted")
    expect(inverted_cover.state).to_equal(CoverState.OPEN)

    # Sending the close command from HA should result
    # in an 'DOWN' command sent to a non-newkaku device
    # that has its type set to 'standard'.
    await hass.services.async_call(
        DOMAIN,
        SERVICE_CLOSE_COVER,
        {ATTR_ENTITY_ID: f"{DOMAIN}.nonkaku_type_standard"},
    )

    await hass.async_block_till_done()

    expect(hass.states.get(f"{DOMAIN}.nonkaku_type_standard").state).to_equal(
        CoverState.CLOSED
    )
    expect(protocol.send_command_ack.call_args_list[0][0][0]).to_equal(
        "nonkaku_device_1"
    )
    expect(protocol.send_command_ack.call_args_list[0][0][1]).to_equal("DOWN")

    # Sending the open command from HA should result
    # in an 'UP' command sent to a non-newkaku device
    # that has its type set to 'standard'.
    await hass.services.async_call(
        DOMAIN,
        SERVICE_OPEN_COVER,
        {ATTR_ENTITY_ID: f"{DOMAIN}.nonkaku_type_standard"},
    )

    await hass.async_block_till_done()

    expect(hass.states.get(f"{DOMAIN}.nonkaku_type_standard").state).to_equal(
        CoverState.OPEN
    )
    expect(protocol.send_command_ack.call_args_list[1][0][0]).to_equal(
        "nonkaku_device_1"
    )
    expect(protocol.send_command_ack.call_args_list[1][0][1]).to_equal("UP")

    # Sending the close command from HA should result
    # in an 'DOWN' command sent to a non-newkaku device
    # that has its type not specified.
    await hass.services.async_call(
        DOMAIN, SERVICE_CLOSE_COVER, {ATTR_ENTITY_ID: f"{DOMAIN}.nonkaku_type_none"}
    )

    await hass.async_block_till_done()

    expect(hass.states.get(f"{DOMAIN}.nonkaku_type_none").state).to_equal(
        CoverState.CLOSED
    )
    expect(protocol.send_command_ack.call_args_list[2][0][0]).to_equal(
        "nonkaku_device_2"
    )
    expect(protocol.send_command_ack.call_args_list[2][0][1]).to_equal("DOWN")

    # Sending the open command from HA should result
    # in an 'UP' command sent to a non-newkaku device
    # that has its type not specified.
    await hass.services.async_call(
        DOMAIN, SERVICE_OPEN_COVER, {ATTR_ENTITY_ID: f"{DOMAIN}.nonkaku_type_none"}
    )

    await hass.async_block_till_done()

    expect(hass.states.get(f"{DOMAIN}.nonkaku_type_none").state).to_equal(
        CoverState.OPEN
    )
    expect(protocol.send_command_ack.call_args_list[3][0][0]).to_equal(
        "nonkaku_device_2"
    )
    expect(protocol.send_command_ack.call_args_list[3][0][1]).to_equal("UP")

    # Sending the close command from HA should result
    # in an 'UP' command sent to a non-newkaku device
    # that has its type set to 'inverted'.
    await hass.services.async_call(
        DOMAIN,
        SERVICE_CLOSE_COVER,
        {ATTR_ENTITY_ID: f"{DOMAIN}.nonkaku_type_inverted"},
    )

    await hass.async_block_till_done()

    expect(hass.states.get(f"{DOMAIN}.nonkaku_type_inverted").state).to_equal(
        CoverState.CLOSED
    )
    expect(protocol.send_command_ack.call_args_list[4][0][0]).to_equal(
        "nonkaku_device_3"
    )
    expect(protocol.send_command_ack.call_args_list[4][0][1]).to_equal("UP")

    # Sending the open command from HA should result
    # in an 'DOWN' command sent to a non-newkaku device
    # that has its type set to 'inverted'.
    await hass.services.async_call(
        DOMAIN,
        SERVICE_OPEN_COVER,
        {ATTR_ENTITY_ID: f"{DOMAIN}.nonkaku_type_inverted"},
    )

    await hass.async_block_till_done()

    expect(hass.states.get(f"{DOMAIN}.nonkaku_type_inverted").state).to_equal(
        CoverState.OPEN
    )
    expect(protocol.send_command_ack.call_args_list[5][0][0]).to_equal(
        "nonkaku_device_3"
    )
    expect(protocol.send_command_ack.call_args_list[5][0][1]).to_equal("DOWN")

    # Sending the close command from HA should result
    # in an 'DOWN' command sent to a newkaku device
    # that has its type set to 'standard'.
    await hass.services.async_call(
        DOMAIN,
        SERVICE_CLOSE_COVER,
        {ATTR_ENTITY_ID: f"{DOMAIN}.newkaku_type_standard"},
    )

    await hass.async_block_till_done()

    expect(hass.states.get(f"{DOMAIN}.newkaku_type_standard").state).to_equal(
        CoverState.CLOSED
    )
    expect(protocol.send_command_ack.call_args_list[6][0][0]).to_equal(
        "newkaku_device_4"
    )
    expect(protocol.send_command_ack.call_args_list[6][0][1]).to_equal("DOWN")

    # Sending the open command from HA should result
    # in an 'UP' command sent to a newkaku device
    # that has its type set to 'standard'.
    await hass.services.async_call(
        DOMAIN,
        SERVICE_OPEN_COVER,
        {ATTR_ENTITY_ID: f"{DOMAIN}.newkaku_type_standard"},
    )

    await hass.async_block_till_done()

    expect(hass.states.get(f"{DOMAIN}.newkaku_type_standard").state).to_equal(
        CoverState.OPEN
    )
    expect(protocol.send_command_ack.call_args_list[7][0][0]).to_equal(
        "newkaku_device_4"
    )
    expect(protocol.send_command_ack.call_args_list[7][0][1]).to_equal("UP")

    # Sending the close command from HA should result
    # in an 'UP' command sent to a newkaku device
    # that has its type not specified.
    await hass.services.async_call(
        DOMAIN, SERVICE_CLOSE_COVER, {ATTR_ENTITY_ID: f"{DOMAIN}.newkaku_type_none"}
    )

    await hass.async_block_till_done()

    expect(hass.states.get(f"{DOMAIN}.newkaku_type_none").state).to_equal(
        CoverState.CLOSED
    )
    expect(protocol.send_command_ack.call_args_list[8][0][0]).to_equal(
        "newkaku_device_5"
    )
    expect(protocol.send_command_ack.call_args_list[8][0][1]).to_equal("UP")

    # Sending the open command from HA should result
    # in an 'DOWN' command sent to a newkaku device
    # that has its type not specified.
    await hass.services.async_call(
        DOMAIN, SERVICE_OPEN_COVER, {ATTR_ENTITY_ID: f"{DOMAIN}.newkaku_type_none"}
    )

    await hass.async_block_till_done()

    expect(hass.states.get(f"{DOMAIN}.newkaku_type_none").state).to_equal(
        CoverState.OPEN
    )
    expect(protocol.send_command_ack.call_args_list[9][0][0]).to_equal(
        "newkaku_device_5"
    )
    expect(protocol.send_command_ack.call_args_list[9][0][1]).to_equal("DOWN")

    # Sending the close command from HA should result
    # in an 'UP' command sent to a newkaku device
    # that has its type set to 'inverted'.
    await hass.services.async_call(
        DOMAIN,
        SERVICE_CLOSE_COVER,
        {ATTR_ENTITY_ID: f"{DOMAIN}.newkaku_type_inverted"},
    )

    await hass.async_block_till_done()

    expect(hass.states.get(f"{DOMAIN}.newkaku_type_inverted").state).to_equal(
        CoverState.CLOSED
    )
    expect(protocol.send_command_ack.call_args_list[10][0][0]).to_equal(
        "newkaku_device_6"
    )
    expect(protocol.send_command_ack.call_args_list[10][0][1]).to_equal("UP")

    # Sending the open command from HA should result
    # in an 'DOWN' command sent to a newkaku device
    # that has its type set to 'inverted'.
    await hass.services.async_call(
        DOMAIN,
        SERVICE_OPEN_COVER,
        {ATTR_ENTITY_ID: f"{DOMAIN}.newkaku_type_inverted"},
    )

    await hass.async_block_till_done()

    expect(hass.states.get(f"{DOMAIN}.newkaku_type_inverted").state).to_equal(
        CoverState.OPEN
    )
    expect(protocol.send_command_ack.call_args_list[11][0][0]).to_equal(
        "newkaku_device_6"
    )
    expect(protocol.send_command_ack.call_args_list[11][0][1]).to_equal("DOWN")
