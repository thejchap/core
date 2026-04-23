"""Test the MySensors config flow."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.mysensors.const import (
    CONF_BAUD_RATE,
    CONF_GATEWAY_TYPE,
    CONF_GATEWAY_TYPE_MQTT,
    CONF_GATEWAY_TYPE_SERIAL,
    CONF_GATEWAY_TYPE_TCP,
    CONF_PERSISTENCE_FILE,
    CONF_RETAIN,
    CONF_TCP_PORT,
    CONF_TOPIC_IN_PREFIX,
    CONF_TOPIC_OUT_PREFIX,
    CONF_VERSION,
    DOMAIN,
    ConfGatewayType,
)
from homeassistant.const import CONF_DEVICE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult, FlowResultType

from ._fixtures import mqtt as mqtt_fixture

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

GATEWAY_TYPE_TO_STEP = {
    CONF_GATEWAY_TYPE_TCP: "gw_tcp",
    CONF_GATEWAY_TYPE_SERIAL: "gw_serial",
    CONF_GATEWAY_TYPE_MQTT: "gw_mqtt",
}


@fixture
def _trigger_executor(_mn: None = Depends(mock_network)) -> None:
    """Trigger the hook executor path."""
    return None


async def _get_form(
    hass: HomeAssistant, gateway_type: ConfGatewayType, expected_step_id: str
) -> FlowResult:
    """Get a form for the given gateway type."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.MENU)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": GATEWAY_TYPE_TO_STEP[gateway_type]}
    )
    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal(expected_step_id)

    return result


@test
async def config_mqtt(
    hass: HomeAssistant = Depends(hass_fixture),
    _mqtt: None = Depends(mqtt_fixture),
) -> None:
    """Test configuring a mqtt gateway."""
    step = await _get_form(hass, CONF_GATEWAY_TYPE_MQTT, "gw_mqtt")
    flow_id = step["flow_id"]

    with patch(
        "homeassistant.components.mysensors.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(
            flow_id,
            {
                CONF_RETAIN: True,
                CONF_TOPIC_IN_PREFIX: "bla",
                CONF_TOPIC_OUT_PREFIX: "blub",
                CONF_VERSION: "2.4",
            },
        )
        await hass.async_block_till_done()

    if "errors" in result:
        expect(result["errors"]).to_be_falsy()
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("mqtt")
    expect(result["data"]).to_equal(
        {
            CONF_DEVICE: "mqtt",
            CONF_RETAIN: True,
            CONF_TOPIC_IN_PREFIX: "bla",
            CONF_TOPIC_OUT_PREFIX: "blub",
            CONF_VERSION: "2.4",
            CONF_GATEWAY_TYPE: "MQTT",
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def missing_mqtt(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test configuring a mqtt gateway without mqtt integration setup."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.MENU)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": GATEWAY_TYPE_TO_STEP[CONF_GATEWAY_TYPE_MQTT]},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("mqtt_required")


@test
async def config_serial(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test configuring a gateway via serial."""
    step = await _get_form(hass, CONF_GATEWAY_TYPE_SERIAL, "gw_serial")
    flow_id = step["flow_id"]

    with (
        patch(
            "homeassistant.components.mysensors.config_flow.is_serial_port",
            return_value=True,
        ),
        patch(
            "homeassistant.components.mysensors.config_flow.try_connect",
            return_value=True,
        ),
        patch(
            "homeassistant.components.mysensors.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_configure(
            flow_id,
            {
                CONF_BAUD_RATE: 115200,
                CONF_DEVICE: "/dev/ttyACM0",
                CONF_VERSION: "2.4",
            },
        )
        await hass.async_block_till_done()

    if "errors" in result:
        expect(result["errors"]).to_be_falsy()
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("/dev/ttyACM0")
    expect(result["data"]).to_equal(
        {
            CONF_DEVICE: "/dev/ttyACM0",
            CONF_BAUD_RATE: 115200,
            CONF_VERSION: "2.4",
            CONF_GATEWAY_TYPE: "Serial",
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def config_tcp(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test configuring a gateway via tcp."""
    step = await _get_form(hass, CONF_GATEWAY_TYPE_TCP, "gw_tcp")
    flow_id = step["flow_id"]

    with (
        patch(
            "homeassistant.components.mysensors.config_flow.try_connect",
            return_value=True,
        ),
        patch("homeassistant.components.mysensors.gateway.socket.getaddrinfo"),
        patch(
            "homeassistant.components.mysensors.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_configure(
            flow_id,
            {
                CONF_TCP_PORT: 5003,
                CONF_DEVICE: "127.0.0.1",
                CONF_VERSION: "2.4",
            },
        )
        await hass.async_block_till_done()

    if "errors" in result:
        expect(result["errors"]).to_be_falsy()
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("127.0.0.1")
    expect(result["data"]).to_equal(
        {
            CONF_DEVICE: "127.0.0.1",
            CONF_TCP_PORT: 5003,
            CONF_VERSION: "2.4",
            CONF_GATEWAY_TYPE: "TCP",
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def fail_to_connect(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test failing to configure a gateway via tcp."""
    step = await _get_form(hass, CONF_GATEWAY_TYPE_TCP, "gw_tcp")
    flow_id = step["flow_id"]

    with (
        patch(
            "homeassistant.components.mysensors.config_flow.try_connect",
            return_value=False,
        ),
        patch("homeassistant.components.mysensors.gateway.socket.getaddrinfo"),
        patch(
            "homeassistant.components.mysensors.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_configure(
            flow_id,
            {
                CONF_TCP_PORT: 5003,
                CONF_DEVICE: "127.0.0.1",
                CONF_VERSION: "2.4",
            },
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    errors = result.get("errors")
    expect(errors).to_be_truthy()
    expect(errors.get("base")).to_equal("cannot_connect")
    expect(len(mock_setup_entry.mock_calls)).to_equal(0)


@test.cases(
    test.case(
        "tcp_bad_version_a",
        CONF_GATEWAY_TYPE_TCP,
        "gw_tcp",
        {CONF_TCP_PORT: 5003, CONF_DEVICE: "127.0.0.1", CONF_VERSION: "a"},
        CONF_VERSION,
        "invalid_version",
    ),
    test.case(
        "tcp_bad_version_ab",
        CONF_GATEWAY_TYPE_TCP,
        "gw_tcp",
        {CONF_TCP_PORT: 5003, CONF_DEVICE: "127.0.0.1", CONF_VERSION: "a.b"},
        CONF_VERSION,
        "invalid_version",
    ),
    test.case(
        "tcp_bad_version_4",
        CONF_GATEWAY_TYPE_TCP,
        "gw_tcp",
        {CONF_TCP_PORT: 5003, CONF_DEVICE: "127.0.0.1", CONF_VERSION: "4"},
        CONF_VERSION,
        "invalid_version",
    ),
    test.case(
        "tcp_bad_version_v3",
        CONF_GATEWAY_TYPE_TCP,
        "gw_tcp",
        {CONF_TCP_PORT: 5003, CONF_DEVICE: "127.0.0.1", CONF_VERSION: "v3"},
        CONF_VERSION,
        "invalid_version",
    ),
    test.case(
        "tcp_bad_ip_short",
        CONF_GATEWAY_TYPE_TCP,
        "gw_tcp",
        {CONF_TCP_PORT: 5003, CONF_DEVICE: "127.0.0.", CONF_VERSION: "2.4"},
        CONF_DEVICE,
        "invalid_ip",
    ),
    test.case(
        "tcp_bad_ip_abcd",
        CONF_GATEWAY_TYPE_TCP,
        "gw_tcp",
        {CONF_TCP_PORT: 5003, CONF_DEVICE: "abcd", CONF_VERSION: "2.4"},
        CONF_DEVICE,
        "invalid_ip",
    ),
    test.case(
        "mqtt_invalid_persistence_file",
        CONF_GATEWAY_TYPE_MQTT,
        "gw_mqtt",
        {
            CONF_RETAIN: True,
            CONF_TOPIC_IN_PREFIX: "bla",
            CONF_TOPIC_OUT_PREFIX: "blub",
            CONF_PERSISTENCE_FILE: "asdf.zip",
            CONF_VERSION: "2.4",
        },
        CONF_PERSISTENCE_FILE,
        "invalid_persistence_file",
    ),
    test.case(
        "mqtt_invalid_subscribe",
        CONF_GATEWAY_TYPE_MQTT,
        "gw_mqtt",
        {
            CONF_RETAIN: True,
            CONF_TOPIC_IN_PREFIX: "/#/#",
            CONF_TOPIC_OUT_PREFIX: "blub",
            CONF_VERSION: "2.4",
        },
        CONF_TOPIC_IN_PREFIX,
        "invalid_subscribe_topic",
    ),
    test.case(
        "mqtt_invalid_publish",
        CONF_GATEWAY_TYPE_MQTT,
        "gw_mqtt",
        {
            CONF_RETAIN: True,
            CONF_TOPIC_IN_PREFIX: "asdf",
            CONF_TOPIC_OUT_PREFIX: "/#/#",
            CONF_VERSION: "2.4",
        },
        CONF_TOPIC_OUT_PREFIX,
        "invalid_publish_topic",
    ),
    test.case(
        "mqtt_same_topic",
        CONF_GATEWAY_TYPE_MQTT,
        "gw_mqtt",
        {
            CONF_RETAIN: True,
            CONF_TOPIC_IN_PREFIX: "asdf",
            CONF_TOPIC_OUT_PREFIX: "asdf",
            CONF_VERSION: "2.4",
        },
        CONF_TOPIC_OUT_PREFIX,
        "same_topic",
    ),
)
async def config_invalid(
    gateway_type: ConfGatewayType,
    expected_step_id: str,
    user_input: dict[str, Any],
    err_field: str,
    err_string: str,
    hass: HomeAssistant = Depends(hass_fixture),
    _mqtt: None = Depends(mqtt_fixture),
) -> None:
    """Perform a test that is expected to generate an error."""
    step = await _get_form(hass, gateway_type, expected_step_id)
    flow_id = step["flow_id"]

    with (
        patch(
            "homeassistant.components.mysensors.config_flow.try_connect",
            return_value=True,
        ),
        patch(
            "homeassistant.components.mysensors.gateway.socket.getaddrinfo",
            side_effect=OSError,
        ),
        patch(
            "homeassistant.components.mysensors.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_configure(flow_id, user_input)
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    errors = result.get("errors")
    expect(errors).to_be_truthy()
    expect(err_field in errors).to_be(True)
    expect(errors[err_field]).to_equal(err_string)
    expect(len(mock_setup_entry.mock_calls)).to_equal(0)


@test.cases(
    test.case(
        "mqtt_same_topics_dup",
        {
            CONF_GATEWAY_TYPE: CONF_GATEWAY_TYPE_MQTT,
            CONF_DEVICE: "mqtt",
            CONF_VERSION: "2.3",
            CONF_TOPIC_IN_PREFIX: "same1",
            CONF_TOPIC_OUT_PREFIX: "same2",
        },
        {
            CONF_GATEWAY_TYPE: CONF_GATEWAY_TYPE_MQTT,
            CONF_VERSION: "2.3",
            CONF_TOPIC_IN_PREFIX: "same1",
            CONF_TOPIC_OUT_PREFIX: "same2",
        },
        FlowResult(
            type=FlowResultType.FORM,
            errors={CONF_TOPIC_IN_PREFIX: "duplicate_topic"},
        ),
    ),
    test.case(
        "mqtt_different_topics_ok",
        {
            CONF_GATEWAY_TYPE: CONF_GATEWAY_TYPE_MQTT,
            CONF_DEVICE: "mqtt",
            CONF_VERSION: "2.3",
            CONF_TOPIC_IN_PREFIX: "different1",
            CONF_TOPIC_OUT_PREFIX: "different2",
        },
        {
            CONF_GATEWAY_TYPE: CONF_GATEWAY_TYPE_MQTT,
            CONF_VERSION: "2.3",
            CONF_TOPIC_IN_PREFIX: "different3",
            CONF_TOPIC_OUT_PREFIX: "different4",
        },
        FlowResult(type=FlowResultType.CREATE_ENTRY),
    ),
    test.case(
        "mqtt_in_topic_dup",
        {
            CONF_GATEWAY_TYPE: CONF_GATEWAY_TYPE_MQTT,
            CONF_DEVICE: "mqtt",
            CONF_VERSION: "2.3",
            CONF_TOPIC_IN_PREFIX: "same1",
            CONF_TOPIC_OUT_PREFIX: "different2",
        },
        {
            CONF_GATEWAY_TYPE: CONF_GATEWAY_TYPE_MQTT,
            CONF_VERSION: "2.3",
            CONF_TOPIC_IN_PREFIX: "same1",
            CONF_TOPIC_OUT_PREFIX: "different4",
        },
        FlowResult(
            type=FlowResultType.FORM,
            errors={CONF_TOPIC_IN_PREFIX: "duplicate_topic"},
        ),
    ),
    test.case(
        "mqtt_swap_in_out_dup",
        {
            CONF_GATEWAY_TYPE: CONF_GATEWAY_TYPE_MQTT,
            CONF_DEVICE: "mqtt",
            CONF_VERSION: "2.3",
            CONF_TOPIC_IN_PREFIX: "same1",
            CONF_TOPIC_OUT_PREFIX: "different2",
        },
        {
            CONF_GATEWAY_TYPE: CONF_GATEWAY_TYPE_MQTT,
            CONF_VERSION: "2.3",
            CONF_TOPIC_IN_PREFIX: "different1",
            CONF_TOPIC_OUT_PREFIX: "same1",
        },
        FlowResult(
            type=FlowResultType.FORM,
            errors={CONF_TOPIC_OUT_PREFIX: "duplicate_topic"},
        ),
    ),
    test.case(
        "mqtt_partial_topic_dup",
        {
            CONF_GATEWAY_TYPE: CONF_GATEWAY_TYPE_MQTT,
            CONF_DEVICE: "mqtt",
            CONF_VERSION: "2.3",
            CONF_TOPIC_IN_PREFIX: "same1",
            CONF_TOPIC_OUT_PREFIX: "different2",
        },
        {
            CONF_GATEWAY_TYPE: CONF_GATEWAY_TYPE_MQTT,
            CONF_VERSION: "2.3",
            CONF_TOPIC_IN_PREFIX: "same1",
            CONF_TOPIC_OUT_PREFIX: "different1",
        },
        FlowResult(
            type=FlowResultType.FORM,
            errors={CONF_TOPIC_IN_PREFIX: "duplicate_topic"},
        ),
    ),
    test.case(
        "tcp_dup_persistence",
        {
            CONF_GATEWAY_TYPE: CONF_GATEWAY_TYPE_TCP,
            CONF_DEVICE: "127.0.0.1",
            CONF_PERSISTENCE_FILE: "same.json",
            CONF_TCP_PORT: 343,
            CONF_VERSION: "2.3",
        },
        {
            CONF_GATEWAY_TYPE: CONF_GATEWAY_TYPE_TCP,
            CONF_DEVICE: "192.168.1.2",
            CONF_PERSISTENCE_FILE: "same.json",
            CONF_TCP_PORT: 343,
            CONF_VERSION: "2.3",
        },
        FlowResult(
            type=FlowResultType.FORM,
            errors={"persistence_file": "duplicate_persistence_file"},
        ),
    ),
    test.case(
        "tcp_no_persistence_ok",
        {
            CONF_GATEWAY_TYPE: CONF_GATEWAY_TYPE_TCP,
            CONF_DEVICE: "127.0.0.1",
            CONF_TCP_PORT: 343,
            CONF_VERSION: "2.3",
        },
        {
            CONF_GATEWAY_TYPE: CONF_GATEWAY_TYPE_TCP,
            CONF_DEVICE: "192.168.1.2",
            CONF_PERSISTENCE_FILE: "same.json",
            CONF_TCP_PORT: 343,
            CONF_VERSION: "2.3",
        },
        FlowResult(type=FlowResultType.CREATE_ENTRY),
    ),
    test.case(
        "tcp_different_ip_ok",
        {
            CONF_GATEWAY_TYPE: CONF_GATEWAY_TYPE_TCP,
            CONF_DEVICE: "127.0.0.1",
            CONF_TCP_PORT: 343,
            CONF_VERSION: "2.3",
        },
        {
            CONF_GATEWAY_TYPE: CONF_GATEWAY_TYPE_TCP,
            CONF_DEVICE: "192.168.1.2",
            CONF_TCP_PORT: 343,
            CONF_VERSION: "2.3",
        },
        FlowResult(type=FlowResultType.CREATE_ENTRY),
    ),
    test.case(
        "tcp_same_device_same_port_dup",
        {
            CONF_GATEWAY_TYPE: CONF_GATEWAY_TYPE_TCP,
            CONF_DEVICE: "192.168.1.2",
            CONF_PERSISTENCE_FILE: "different1.json",
            CONF_TCP_PORT: 343,
            CONF_VERSION: "2.3",
        },
        {
            CONF_GATEWAY_TYPE: CONF_GATEWAY_TYPE_TCP,
            CONF_DEVICE: "192.168.1.2",
            CONF_PERSISTENCE_FILE: "different2.json",
            CONF_TCP_PORT: 343,
            CONF_VERSION: "2.3",
        },
        FlowResult(type=FlowResultType.FORM, errors={"base": "already_configured"}),
    ),
    test.case(
        "tcp_same_device_diff_port_ok",
        {
            CONF_GATEWAY_TYPE: CONF_GATEWAY_TYPE_TCP,
            CONF_DEVICE: "192.168.1.2",
            CONF_PERSISTENCE_FILE: "different1.json",
            CONF_TCP_PORT: 343,
            CONF_VERSION: "2.3",
        },
        {
            CONF_GATEWAY_TYPE: CONF_GATEWAY_TYPE_TCP,
            CONF_DEVICE: "192.168.1.2",
            CONF_PERSISTENCE_FILE: "different2.json",
            CONF_TCP_PORT: 5003,
            CONF_VERSION: "2.3",
        },
        FlowResult(type=FlowResultType.CREATE_ENTRY),
    ),
    test.case(
        "tcp_diff_ip_same_port_ok",
        {
            CONF_GATEWAY_TYPE: CONF_GATEWAY_TYPE_TCP,
            CONF_DEVICE: "192.168.1.2",
            CONF_TCP_PORT: 5003,
            CONF_VERSION: "2.3",
        },
        {
            CONF_GATEWAY_TYPE: CONF_GATEWAY_TYPE_TCP,
            CONF_DEVICE: "192.168.1.3",
            CONF_TCP_PORT: 5003,
            CONF_VERSION: "2.3",
        },
        FlowResult(type=FlowResultType.CREATE_ENTRY),
    ),
    test.case(
        "serial_same_device_dup",
        {
            CONF_GATEWAY_TYPE: CONF_GATEWAY_TYPE_SERIAL,
            CONF_DEVICE: "COM5",
            CONF_VERSION: "2.3",
            CONF_PERSISTENCE_FILE: "different1.json",
        },
        {
            CONF_GATEWAY_TYPE: CONF_GATEWAY_TYPE_SERIAL,
            CONF_DEVICE: "COM5",
            CONF_VERSION: "2.3",
            CONF_PERSISTENCE_FILE: "different2.json",
        },
        FlowResult(type=FlowResultType.FORM, errors={"base": "already_configured"}),
    ),
    test.case(
        "serial_diff_device_ok",
        {
            CONF_GATEWAY_TYPE: CONF_GATEWAY_TYPE_SERIAL,
            CONF_DEVICE: "COM6",
            CONF_BAUD_RATE: 57600,
            CONF_VERSION: "2.3",
        },
        {
            CONF_GATEWAY_TYPE: CONF_GATEWAY_TYPE_SERIAL,
            CONF_DEVICE: "COM5",
            CONF_VERSION: "2.3",
        },
        FlowResult(type=FlowResultType.CREATE_ENTRY),
    ),
    test.case(
        "serial_same_device_diff_baud_dup",
        {
            CONF_GATEWAY_TYPE: CONF_GATEWAY_TYPE_SERIAL,
            CONF_DEVICE: "COM5",
            CONF_BAUD_RATE: 115200,
            CONF_VERSION: "2.3",
            CONF_PERSISTENCE_FILE: "different1.json",
        },
        {
            CONF_GATEWAY_TYPE: CONF_GATEWAY_TYPE_SERIAL,
            CONF_DEVICE: "COM5",
            CONF_BAUD_RATE: 57600,
            CONF_VERSION: "2.3",
            CONF_PERSISTENCE_FILE: "different2.json",
        },
        FlowResult(type=FlowResultType.FORM, errors={"base": "already_configured"}),
    ),
    test.case(
        "serial_diff_device_same_persistence",
        {
            CONF_GATEWAY_TYPE: CONF_GATEWAY_TYPE_SERIAL,
            CONF_DEVICE: "COM5",
            CONF_BAUD_RATE: 115200,
            CONF_VERSION: "2.3",
            CONF_PERSISTENCE_FILE: "same.json",
        },
        {
            CONF_GATEWAY_TYPE: CONF_GATEWAY_TYPE_SERIAL,
            CONF_DEVICE: "COM6",
            CONF_BAUD_RATE: 57600,
            CONF_VERSION: "2.3",
            CONF_PERSISTENCE_FILE: "same.json",
        },
        FlowResult(
            type=FlowResultType.FORM,
            errors={"persistence_file": "duplicate_persistence_file"},
        ),
    ),
    test.case(
        "mqtt_vs_serial_ok",
        {
            CONF_GATEWAY_TYPE: CONF_GATEWAY_TYPE_MQTT,
            CONF_DEVICE: "mqtt",
            CONF_PERSISTENCE_FILE: "bla.json",
            CONF_VERSION: "1.4",
        },
        {
            CONF_GATEWAY_TYPE: CONF_GATEWAY_TYPE_SERIAL,
            CONF_DEVICE: "COM6",
            CONF_PERSISTENCE_FILE: "bla2.json",
            CONF_BAUD_RATE: 115200,
            CONF_VERSION: "1.4",
        },
        FlowResult(type=FlowResultType.CREATE_ENTRY),
    ),
)
async def duplicate(
    first_input: dict,
    second_input: dict,
    expected_result: FlowResult,
    hass: HomeAssistant = Depends(hass_fixture),
    _mqtt: None = Depends(mqtt_fixture),
) -> None:
    """Test duplicate detection."""
    with (
        patch("sys.platform", "win32"),
        patch(
            "homeassistant.components.mysensors.config_flow.try_connect",
            return_value=True,
        ),
        patch("homeassistant.components.mysensors.gateway.socket.getaddrinfo"),
        patch(
            "homeassistant.components.mysensors.async_setup_entry",
            return_value=True,
        ),
    ):
        MockConfigEntry(domain=DOMAIN, data=first_input).add_to_hass(hass)

        second_gateway_type = second_input.pop(CONF_GATEWAY_TYPE)
        result = await _get_form(
            hass, second_gateway_type, GATEWAY_TYPE_TO_STEP[second_gateway_type]
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            second_input,
        )
        await hass.async_block_till_done()

        for key, val in expected_result.items():
            expect(result[key]).to_equal(val)
