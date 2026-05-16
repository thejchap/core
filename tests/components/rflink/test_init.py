"""Common functions for RFLink component tests and generic platform tests."""

from __future__ import annotations

import logging
from unittest.mock import Mock, patch

from tryke import Depends, expect, fixture, test
from voluptuous.error import MultipleInvalid

from homeassistant.components.rflink import (
    CONF_KEEPALIVE_IDLE,
    CONF_RECONNECT_INTERVAL,
    DATA_ENTITY_LOOKUP,
    DEFAULT_TCP_KEEPALIVE_IDLE_TIMER,
    DOMAIN,
    EVENT_KEY_COMMAND,
    EVENT_KEY_SENSOR,
    SERVICE_SEND_COMMAND,
    TMP_ENTITY,
    RflinkCommand,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    CONF_HOST,
    CONF_PORT,
    EVENT_LOGGING_CHANGED,
    SERVICE_STOP_COVER,
    SERVICE_TURN_OFF,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fixture,
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
)
from tests.hass_tryke_helpers import expect_raises_async


@fixture
def _trigger_executor() -> int:
    """Anchor for tryke fixture resolution."""
    return 0


async def mock_rflink(
    hass: HomeAssistant,
    config,
    domain,
    failures=None,
    failcommand=False,
):
    """Create mock RFLink asyncio protocol, test component setup."""
    transport, protocol = (Mock(), Mock())

    async def send_command_ack(*command):
        return not failcommand

    protocol.send_command_ack = Mock(wraps=send_command_ack)

    def send_command(*command):
        return not failcommand

    protocol.send_command = Mock(wraps=send_command)

    async def create_rflink_connection(*args, **kwargs):
        """Return mocked transport and protocol."""
        # failures can be a list of booleans indicating in which sequence
        # creating a connection should success or fail
        if failures:
            fail = failures.pop(0)  # removes from left to right
        else:
            fail = False

        if fail:
            raise ConnectionRefusedError
        return transport, protocol

    mock_create = Mock(wraps=create_rflink_connection)
    patcher = patch(
        "homeassistant.components.rflink.create_rflink_connection", mock_create
    )
    patcher.start()

    await async_setup_component(hass, "rflink", config)
    await async_setup_component(hass, domain, config)
    await hass.async_block_till_done()

    event_callback = mock_create.call_args_list[0][1]["event_callback"]
    expect(event_callback).to_be_truthy()

    disconnect_callback = mock_create.call_args_list[0][1]["disconnect_callback"]

    return event_callback, mock_create, protocol, disconnect_callback


@test
async def version_banner(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test sending unknown commands doesn't cause issues."""
    domain = "sensor"
    config = {
        "rflink": {"port": "/dev/ttyABC0"},
        domain: {
            "platform": "rflink",
            "devices": {"test": {"name": "test", "sensor_type": "temperature"}},
        },
    }

    event_callback, _, _, _ = await mock_rflink(hass, config, domain)

    event_callback(
        {
            "hardware": "Nodo RadioFrequencyLink",
            "firmware": "RFLink Gateway",
            "version": "1.1",
            "revision": "45",
        }
    )


@test
async def send_no_wait(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test command sending without ack."""
    domain = "switch"
    config = {
        "rflink": {"port": "/dev/ttyABC0", "wait_for_ack": False},
        domain: {
            "platform": "rflink",
            "devices": {
                "protocol_0_0": {"name": "test", "aliases": ["test_alias_0_0"]}
            },
        },
    }

    _, _, protocol, _ = await mock_rflink(hass, config, domain)

    await hass.services.async_call(
        domain, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: "switch.test"}
    )
    await hass.async_block_till_done()
    expect(protocol.send_command.call_args_list[0][0][0]).to_equal("protocol_0_0")
    expect(protocol.send_command.call_args_list[0][0][1]).to_equal("off")


@test
async def cover_send_no_wait(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test command sending to a cover device without ack."""
    domain = "cover"
    config = {
        "rflink": {"port": "/dev/ttyABC0", "wait_for_ack": False},
        domain: {
            "platform": "rflink",
            "devices": {
                "RTS_0100F2_0": {"name": "test", "aliases": ["test_alias_0_0"]}
            },
        },
    }

    _, _, protocol, _ = await mock_rflink(hass, config, domain)

    await hass.services.async_call(
        domain, SERVICE_STOP_COVER, {ATTR_ENTITY_ID: "cover.test"}
    )
    await hass.async_block_till_done()
    expect(protocol.send_command.call_args_list[0][0][0]).to_equal("RTS_0100F2_0")
    expect(protocol.send_command.call_args_list[0][0][1]).to_equal("STOP")


@test
async def send_command(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test send_command service."""
    domain = "rflink"
    config = {"rflink": {"port": "/dev/ttyABC0"}}

    _, _, protocol, _ = await mock_rflink(hass, config, domain)

    await hass.services.async_call(
        domain,
        SERVICE_SEND_COMMAND,
        {"device_id": "newkaku_0000c6c2_1", "command": "on"},
    )
    await hass.async_block_till_done()
    expect(protocol.send_command_ack.call_args_list[0][0][0]).to_equal(
        "newkaku_0000c6c2_1"
    )
    expect(protocol.send_command_ack.call_args_list[0][0][1]).to_equal("on")


@test
async def send_command_invalid_arguments(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test send_command service."""
    domain = "rflink"
    config = {"rflink": {"port": "/dev/ttyABC0"}}

    _, _, protocol, _ = await mock_rflink(hass, config, domain)

    # one argument missing
    async with expect_raises_async(MultipleInvalid):
        await hass.services.async_call(domain, SERVICE_SEND_COMMAND, {"command": "on"})

    async with expect_raises_async(MultipleInvalid):
        await hass.services.async_call(
            domain, SERVICE_SEND_COMMAND, {"device_id": "newkaku_0000c6c2_1"}
        )

    # no arguments
    async with expect_raises_async(MultipleInvalid):
        await hass.services.async_call(domain, SERVICE_SEND_COMMAND, {})

    await hass.async_block_till_done()
    expect(protocol.send_command_ack.call_args_list).to_equal([])

    # bad command (no_command)
    success = await hass.services.async_call(
        domain,
        SERVICE_SEND_COMMAND,
        {"device_id": "newkaku_0000c6c2_1", "command": "no_command"},
    )
    expect(success).to_be_falsy()


@test
async def send_command_event_propagation(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test event propagation for send_command service."""
    domain = "light"
    config = {
        "rflink": {"port": "/dev/ttyABC0"},
        domain: {
            "platform": "rflink",
            "devices": {
                "protocol_0_1": {"name": "test1"},
            },
        },
    }

    _, _, protocol, _ = await mock_rflink(hass, config, domain)

    # default value = 'off'
    expect(hass.states.get(f"{domain}.test1").state).to_equal("off")

    await hass.services.async_call(
        "rflink",
        SERVICE_SEND_COMMAND,
        {"device_id": "protocol_0_1", "command": "on"},
        blocking=True,
    )
    await hass.async_block_till_done()
    expect(protocol.send_command_ack.call_args_list[0][0][0]).to_equal("protocol_0_1")
    expect(protocol.send_command_ack.call_args_list[0][0][1]).to_equal("on")
    expect(hass.states.get(f"{domain}.test1").state).to_equal("on")

    await hass.services.async_call(
        "rflink",
        SERVICE_SEND_COMMAND,
        {"device_id": "protocol_0_1", "command": "alloff"},
        blocking=True,
    )
    await hass.async_block_till_done()
    expect(protocol.send_command_ack.call_args_list[1][0][0]).to_equal("protocol_0_1")
    expect(protocol.send_command_ack.call_args_list[1][0][1]).to_equal("alloff")
    expect(hass.states.get(f"{domain}.test1").state).to_equal("off")


@test
async def reconnecting_after_disconnect(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """An unexpected disconnect should cause a reconnect."""
    domain = "sensor"
    config = {
        "rflink": {"port": "/dev/ttyABC0", CONF_RECONNECT_INTERVAL: 0},
        domain: {"platform": "rflink"},
    }

    _, mock_create, _, disconnect_callback = await mock_rflink(hass, config, domain)

    expect(disconnect_callback).to_be_truthy()

    # rflink initiated disconnect
    disconnect_callback(None)

    await hass.async_block_till_done()

    # we expect 2 call, the initial and reconnect
    expect(mock_create.call_count).to_equal(2)


@test
async def reconnecting_after_failure(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """A failure to reconnect should be retried."""
    domain = "sensor"
    config = {
        "rflink": {"port": "/dev/ttyABC0", CONF_RECONNECT_INTERVAL: 0},
        domain: {"platform": "rflink"},
    }

    # success first time but fail second
    failures = [False, True, False]

    _, mock_create, _, disconnect_callback = await mock_rflink(
        hass, config, domain, failures=failures
    )

    # rflink initiated disconnect
    disconnect_callback(None)

    # wait for reconnects to have happened
    await hass.async_block_till_done()
    await hass.async_block_till_done()

    # we expect 3 calls, the initial and 2 reconnects
    expect(mock_create.call_count).to_equal(3)


@test
async def error_when_not_connected(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Sending command should error when not connected."""
    domain = "switch"
    config = {
        "rflink": {"port": "/dev/ttyABC0", CONF_RECONNECT_INTERVAL: 0},
        domain: {
            "platform": "rflink",
            "devices": {
                "protocol_0_0": {"name": "test", "aliases": ["test_alias_0_0"]}
            },
        },
    }

    # success first time but fail second
    failures = [False, True, False]

    _, _, _, disconnect_callback = await mock_rflink(
        hass, config, domain, failures=failures
    )

    # rflink initiated disconnect
    disconnect_callback(None)

    success = await hass.services.async_call(
        domain, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: "switch.test"}
    )
    expect(success).to_be_falsy()


@test
async def async_send_command_error(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Sending command should error when protocol fails."""
    domain = "rflink"
    config = {"rflink": {"port": "/dev/ttyABC0"}}

    _, _, protocol, _ = await mock_rflink(hass, config, domain, failcommand=True)

    success = await hass.services.async_call(
        domain,
        SERVICE_SEND_COMMAND,
        {"device_id": "newkaku_0000c6c2_1", "command": SERVICE_TURN_OFF},
    )
    await hass.async_block_till_done()
    expect(success).to_be_falsy()
    expect(protocol.send_command_ack.call_args_list[0][0][0]).to_equal(
        "newkaku_0000c6c2_1"
    )
    expect(protocol.send_command_ack.call_args_list[0][0][1]).to_equal(SERVICE_TURN_OFF)


@test
async def race_condition(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test race condition for unknown components."""
    domain = "light"
    config = {"rflink": {"port": "/dev/ttyABC0"}, domain: {"platform": "rflink"}}
    tmp_entity = TMP_ENTITY.format("test3")

    event_callback, _, _, _ = await mock_rflink(hass, config, domain)

    # test event for new unconfigured sensor
    event_callback({"id": "test3", "command": "off"})
    event_callback({"id": "test3", "command": "on"})

    # tmp_entity added to EVENT_KEY_COMMAND
    expect(
        tmp_entity in hass.data[DATA_ENTITY_LOOKUP][EVENT_KEY_COMMAND]["test3"]
    ).to_be(True)
    # tmp_entity must no be added to EVENT_KEY_SENSOR
    expect(
        tmp_entity not in hass.data[DATA_ENTITY_LOOKUP][EVENT_KEY_SENSOR]["test3"]
    ).to_be(True)

    await hass.async_block_till_done()

    # test  state of new sensor
    new_sensor = hass.states.get(f"{domain}.test3")
    expect(new_sensor).to_be_truthy()
    expect(new_sensor.state).to_equal("off")

    event_callback({"id": "test3", "command": "on"})
    await hass.async_block_till_done()
    # tmp_entity must be deleted from EVENT_KEY_COMMAND
    expect(
        tmp_entity not in hass.data[DATA_ENTITY_LOOKUP][EVENT_KEY_COMMAND]["test3"]
    ).to_be(True)

    # test  state of new sensor
    new_sensor = hass.states.get(f"{domain}.test3")
    expect(new_sensor).to_be_truthy()
    expect(new_sensor.state).to_equal("on")


@test
async def not_connected() -> None:
    """Test Error when sending commands to a disconnected device."""
    test_device = RflinkCommand("DUMMY_DEVICE")
    RflinkCommand.set_rflink_protocol(None)
    async with expect_raises_async(HomeAssistantError):
        await test_device._async_handle_command("turn_on")


@test
async def keepalive(
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Validate negative keepalive values."""
    keepalive_value = -3
    domain = DOMAIN
    config = {
        DOMAIN: {
            CONF_HOST: "10.10.0.1",
            CONF_PORT: 1234,
            CONF_KEEPALIVE_IDLE: keepalive_value,
        }
    }

    _, mock_create, _, _ = await mock_rflink(hass, config, domain)

    expect(mock_create.call_args_list[0][1]["host"]).to_equal("10.10.0.1")
    expect(mock_create.call_args_list[0][1]["port"]).to_equal(1234)
    # negative keepalive is not allowed
    expect(mock_create.call_args_list[0][1]["keepalive"]).to_be(None)
    expect(
        f"A bogus TCP Keepalive IDLE timer was provided ({keepalive_value} secs)"
        in caplog.text
    ).to_be(True)


@test
async def keepalive_2(
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Validate very short keepalive values."""
    keepalive_value = 30
    domain = DOMAIN
    config = {
        DOMAIN: {
            CONF_HOST: "10.10.0.1",
            CONF_PORT: 1234,
            CONF_KEEPALIVE_IDLE: keepalive_value,
        }
    }

    _, mock_create, _, _ = await mock_rflink(hass, config, domain)

    expect(mock_create.call_args_list[0][1]["host"]).to_equal("10.10.0.1")
    expect(mock_create.call_args_list[0][1]["port"]).to_equal(1234)
    # very short keepalive is allowed but warned
    expect(mock_create.call_args_list[0][1]["keepalive"]).to_equal(keepalive_value)
    expect(
        f"A very short TCP Keepalive IDLE timer was provided ({keepalive_value} secs)"
        in caplog.text
    ).to_be(True)


@test
async def keepalive_3(
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Validate keepalive=0 value."""
    domain = DOMAIN
    config = {DOMAIN: {CONF_HOST: "10.10.0.1", CONF_PORT: 1234, CONF_KEEPALIVE_IDLE: 0}}

    _, mock_create, _, _ = await mock_rflink(hass, config, domain)

    expect(mock_create.call_args_list[0][1]["host"]).to_equal("10.10.0.1")
    expect(mock_create.call_args_list[0][1]["port"]).to_equal(1234)
    # keepalive=0 will disable it
    expect(mock_create.call_args_list[0][1]["keepalive"]).to_be(None)
    expect("TCP Keepalive IDLE timer was provided" not in caplog.text).to_be(True)


@test
async def default_keepalive(
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Validate keepalive=0 value."""
    domain = DOMAIN
    config = {DOMAIN: {CONF_HOST: "10.10.0.1", CONF_PORT: 1234}}

    _, mock_create, _, _ = await mock_rflink(hass, config, domain)

    expect(mock_create.call_args_list[0][1]["host"]).to_equal("10.10.0.1")
    expect(mock_create.call_args_list[0][1]["port"]).to_equal(1234)
    # no keepalive config will default it
    expect(mock_create.call_args_list[0][1]["keepalive"]).to_equal(
        DEFAULT_TCP_KEEPALIVE_IDLE_TIMER
    )
    expect("TCP Keepalive IDLE timer was provided" not in caplog.text).to_be(True)


@test
async def unique_id(
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Validate the device unique_id."""
    sensor_domain = "sensor"
    config = {
        "rflink": {"port": "/dev/ttyABC0"},
        sensor_domain: {
            "platform": "rflink",
            "devices": {
                "my_humidity_device_unique_id": {
                    "name": "humidity_device",
                    "sensor_type": "humidity",
                    "aliases": ["test_alias_02_0"],
                },
                "my_temperature_device_unique_id": {
                    "name": "temperature_device",
                    "sensor_type": "temperature",
                    "aliases": ["test_alias_02_0"],
                },
            },
        },
    }

    await mock_rflink(hass, config, sensor_domain)

    humidity_entry = entity_registry.async_get("sensor.humidity_device")
    expect(humidity_entry).to_be_truthy()
    expect(humidity_entry.unique_id).to_equal("my_humidity_device_unique_id")

    temperature_entry = entity_registry.async_get("sensor.temperature_device")
    expect(temperature_entry).to_be_truthy()
    expect(temperature_entry.unique_id).to_equal("my_temperature_device_unique_id")


@test
async def enable_debug_logs(
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test that changing debug level enables RFDEBUG."""
    domain = DOMAIN
    config = {DOMAIN: {CONF_HOST: "10.10.0.1", CONF_PORT: 1234}}

    await mock_rflink(hass, config, domain)

    logging.getLogger("rflink").setLevel(logging.DEBUG)
    hass.bus.async_fire(EVENT_LOGGING_CHANGED)
    await hass.async_block_till_done()

    expect("RFDEBUG enabled" in caplog.text).to_be(True)
    expect("RFDEBUG disabled" not in caplog.text).to_be(True)

    logging.getLogger("rflink").setLevel(logging.INFO)
    hass.bus.async_fire(EVENT_LOGGING_CHANGED)
    await hass.async_block_till_done()

    expect("RFDEBUG disabled" in caplog.text).to_be(True)
