"""Test the AlarmDecoder config flow."""

from unittest.mock import patch

from alarmdecoder.util import NoDeviceError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.alarmdecoder import config_flow
from homeassistant.components.alarmdecoder.const import (
    CONF_ALT_NIGHT_MODE,
    CONF_AUTO_BYPASS,
    CONF_CODE_ARM_REQUIRED,
    CONF_DEVICE_BAUD,
    CONF_DEVICE_PATH,
    CONF_RELAY_ADDR,
    CONF_RELAY_CHAN,
    CONF_ZONE_LOOP,
    CONF_ZONE_NAME,
    CONF_ZONE_NUMBER,
    CONF_ZONE_RFID,
    CONF_ZONE_TYPE,
    DEFAULT_ARM_OPTIONS,
    DEFAULT_ZONE_OPTIONS,
    DOMAIN,
    OPTIONS_ARM,
    OPTIONS_ZONES,
    PROTOCOL_SERIAL,
    PROTOCOL_SOCKET,
)
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_PROTOCOL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Apply autouse-equivalent fixtures via this trigger."""


@test.cases(
    test.case(
        "socket",
        protocol=PROTOCOL_SOCKET,
        connection={
            CONF_HOST: "alarmdecoder123",
            CONF_PORT: 10001,
        },
        title="alarmdecoder123:10001",
    ),
    test.case(
        "serial",
        protocol=PROTOCOL_SERIAL,
        connection={
            CONF_DEVICE_PATH: "/dev/ttyUSB123",
            CONF_DEVICE_BAUD: 115000,
        },
        title="/dev/ttyUSB123",
    ),
)
async def setups(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    protocol: str,
    connection: dict,
    title: str,
) -> None:
    """Test flow for setting up the available AlarmDecoder protocols."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PROTOCOL: protocol},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("protocol")

    with (
        patch("homeassistant.components.alarmdecoder.config_flow.AdExt.open"),
        patch("homeassistant.components.alarmdecoder.config_flow.AdExt.close"),
        patch(
            "homeassistant.components.alarmdecoder.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], connection
        )
        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["title"]).to_equal(title)
        expect(result["data"]).to_equal(
            {
                **connection,
                CONF_PROTOCOL: protocol,
            }
        )
        await hass.async_block_till_done()

    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def setup_connection_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test flow for setup with a connection error."""
    port = 1001
    host = "alarmdecoder"
    protocol = PROTOCOL_SOCKET
    connection_settings = {CONF_HOST: host, CONF_PORT: port}

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PROTOCOL: protocol},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("protocol")

    with (
        patch(
            "homeassistant.components.alarmdecoder.config_flow.AdExt.open",
            side_effect=NoDeviceError,
        ),
        patch("homeassistant.components.alarmdecoder.config_flow.AdExt.close"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], connection_settings
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["errors"]).to_equal({"base": "cannot_connect"})

    with (
        patch(
            "homeassistant.components.alarmdecoder.config_flow.AdExt.open",
            side_effect=Exception,
        ),
        patch("homeassistant.components.alarmdecoder.config_flow.AdExt.close"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], connection_settings
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["errors"]).to_equal({"base": "unknown"})


@test
async def options_arm_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test arm options flow."""
    user_input = {
        CONF_ALT_NIGHT_MODE: True,
        CONF_AUTO_BYPASS: True,
        CONF_CODE_ARM_REQUIRED: True,
    }
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"edit_selection": "Arming Settings"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("arm_settings")

    with patch(
        "homeassistant.components.alarmdecoder.async_setup_entry", return_value=True
    ):
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input=user_input,
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(entry.options).to_equal(
        {
            OPTIONS_ARM: user_input,
            OPTIONS_ZONES: DEFAULT_ZONE_OPTIONS,
        }
    )


@test
async def options_zone_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test options flow for adding/deleting zones."""
    zone_number = "2"
    zone_settings = {
        CONF_ZONE_NAME: "Front Entry",
        CONF_ZONE_TYPE: BinarySensorDeviceClass.WINDOW,
    }
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"edit_selection": "Zones"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("zone_select")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_ZONE_NUMBER: zone_number},
    )

    with patch(
        "homeassistant.components.alarmdecoder.async_setup_entry", return_value=True
    ):
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input=zone_settings,
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(entry.options).to_equal(
        {
            OPTIONS_ARM: DEFAULT_ARM_OPTIONS,
            OPTIONS_ZONES: {zone_number: zone_settings},
        }
    )

    result = await hass.config_entries.options.async_init(entry.entry_id)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"edit_selection": "Zones"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("zone_select")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_ZONE_NUMBER: zone_number},
    )

    with patch(
        "homeassistant.components.alarmdecoder.async_setup_entry", return_value=True
    ):
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={},
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(entry.options).to_equal(
        {
            OPTIONS_ARM: DEFAULT_ARM_OPTIONS,
            OPTIONS_ZONES: {},
        }
    )


@test
async def options_zone_flow_validation(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test input validation for zone options flow."""
    zone_number = "2"
    zone_settings = {
        CONF_ZONE_NAME: "Front Entry",
        CONF_ZONE_TYPE: BinarySensorDeviceClass.WINDOW,
    }
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"edit_selection": "Zones"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("zone_select")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_ZONE_NUMBER: "asd"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("zone_select")
    expect(result["errors"]).to_equal({CONF_ZONE_NUMBER: "int"})

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_ZONE_NUMBER: zone_number},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("zone_details")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={**zone_settings, CONF_RELAY_ADDR: "1"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("zone_details")
    expect(result["errors"]).to_equal({"base": "relay_inclusive"})

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={**zone_settings, CONF_RELAY_CHAN: "1"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("zone_details")
    expect(result["errors"]).to_equal({"base": "relay_inclusive"})

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={**zone_settings, CONF_RELAY_ADDR: "abc", CONF_RELAY_CHAN: "abc"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("zone_details")
    expect(result["errors"]).to_equal(
        {
            CONF_RELAY_ADDR: "int",
            CONF_RELAY_CHAN: "int",
        }
    )

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={**zone_settings, CONF_ZONE_LOOP: "1"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("zone_details")
    expect(result["errors"]).to_equal({CONF_ZONE_LOOP: "loop_rfid"})

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={**zone_settings, CONF_ZONE_RFID: "rfid123", CONF_ZONE_LOOP: "ab"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("zone_details")
    expect(result["errors"]).to_equal({CONF_ZONE_LOOP: "int"})

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={**zone_settings, CONF_ZONE_RFID: "rfid123", CONF_ZONE_LOOP: "5"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("zone_details")
    expect(result["errors"]).to_equal({CONF_ZONE_LOOP: "loop_range"})

    with patch(
        "homeassistant.components.alarmdecoder.async_setup_entry", return_value=True
    ):
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                **zone_settings,
                CONF_ZONE_RFID: "rfid123",
                CONF_ZONE_LOOP: "2",
                CONF_RELAY_ADDR: "12",
                CONF_RELAY_CHAN: "1",
            },
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(entry.options).to_equal(
        {
            OPTIONS_ARM: DEFAULT_ARM_OPTIONS,
            OPTIONS_ZONES: {
                zone_number: {
                    **zone_settings,
                    CONF_ZONE_RFID: "rfid123",
                    CONF_ZONE_LOOP: 2,
                    CONF_RELAY_ADDR: 12,
                    CONF_RELAY_CHAN: 1,
                }
            },
        }
    )


@test.cases(
    test.case(
        "socket",
        protocol=PROTOCOL_SOCKET,
        connection={
            CONF_HOST: "alarmdecoder123",
            CONF_PORT: 10001,
        },
    ),
    test.case(
        "serial",
        protocol=PROTOCOL_SERIAL,
        connection={
            CONF_DEVICE_PATH: "/dev/ttyUSB123",
            CONF_DEVICE_BAUD: 115000,
        },
    ),
)
async def one_device_allowed(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    protocol: str,
    connection: dict,
) -> None:
    """Test that only one AlarmDecoder device is allowed."""
    flow = config_flow.AlarmDecoderFlowHandler()
    flow.hass = hass

    MockConfigEntry(
        domain=DOMAIN,
        data=connection,
    ).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PROTOCOL: protocol},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("protocol")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], connection
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
