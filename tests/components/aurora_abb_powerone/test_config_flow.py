"""Test the Aurora ABB PowerOne Solar PV config flow."""

from unittest.mock import patch

from aurorapy.client import AuroraError, AuroraTimeoutError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries, setup
from homeassistant.components.aurora_abb_powerone.const import (
    ATTR_FIRMWARE,
    ATTR_MODEL,
    DOMAIN,
)
from homeassistant.components.usb import SerialDevice
from homeassistant.const import ATTR_SERIAL_NUMBER, CONF_ADDRESS, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.hass_fixtures import hass as hass_fixture, mock_network

TEST_DATA = {"device": "/dev/ttyUSB7", "address": 3, "name": "MyAuroraPV"}


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we get the form."""
    await setup.async_setup_component(hass, "persistent_notification", {})

    fakecomports = [
        SerialDevice(
            device="/dev/ttyUSB7",
            serial_number=None,
            manufacturer=None,
            description=None,
        )
    ]
    with patch(
        "homeassistant.components.aurora_abb_powerone.config_flow.usb.async_scan_serial_ports",
        return_value=fakecomports,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with (
        patch(
            "aurorapy.client.AuroraSerialClient.connect",
            return_value=None,
        ),
        patch(
            "aurorapy.client.AuroraSerialClient.serial_number",
            return_value="9876543",
        ),
        patch(
            "aurorapy.client.AuroraSerialClient.version",
            return_value="9.8.7.6",
        ),
        patch(
            "aurorapy.client.AuroraSerialClient.pn",
            return_value="A.B.C",
        ),
        patch(
            "aurorapy.client.AuroraSerialClient.firmware",
            return_value="1.234",
        ) as mock_setup,
        patch(
            "homeassistant.components.aurora_abb_powerone.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_PORT: "/dev/ttyUSB7", CONF_ADDRESS: 7},
        )

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)

    expect(result2["data"]).to_equal(
        {
            CONF_PORT: "/dev/ttyUSB7",
            CONF_ADDRESS: 7,
            ATTR_FIRMWARE: "1.234",
            ATTR_MODEL: "9.8.7.6 (A.B.C)",
            ATTR_SERIAL_NUMBER: "9876543",
            "title": "PhotoVoltaic Inverters",
        }
    )
    await hass.async_block_till_done()
    expect(len(mock_setup.mock_calls)).to_equal(1)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_no_comports(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we display correct info when there are no com ports.."""
    fakecomports: list[SerialDevice] = []
    with patch(
        "homeassistant.components.aurora_abb_powerone.config_flow.usb.async_scan_serial_ports",
        return_value=fakecomports,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_serial_ports")


@test
async def form_invalid_com_ports(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we display correct info when the comport is invalid.."""
    fakecomports = [
        SerialDevice(
            device="/dev/ttyUSB7",
            serial_number=None,
            manufacturer=None,
            description=None,
        )
    ]
    with patch(
        "homeassistant.components.aurora_abb_powerone.config_flow.usb.async_scan_serial_ports",
        return_value=fakecomports,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with patch(
        "aurorapy.client.AuroraSerialClient.connect",
        side_effect=OSError(19, "...no such device..."),
        return_value=None,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_PORT: "/dev/ttyUSB7", CONF_ADDRESS: 7},
        )
    expect(result2["errors"]).to_equal({"base": "invalid_serial_port"})

    with patch(
        "aurorapy.client.AuroraSerialClient.connect",
        side_effect=AuroraError("..could not open port..."),
        return_value=None,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_PORT: "/dev/ttyUSB7", CONF_ADDRESS: 7},
        )
    expect(result2["errors"]).to_equal({"base": "cannot_open_serial_port"})

    with patch(
        "aurorapy.client.AuroraSerialClient.connect",
        side_effect=AuroraTimeoutError("...No response after..."),
        return_value=None,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_PORT: "/dev/ttyUSB7", CONF_ADDRESS: 7},
        )
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})

    with (
        patch(
            "aurorapy.client.AuroraSerialClient.connect",
            side_effect=AuroraError("...Some other message!!!123..."),
            return_value=None,
        ),
        patch(
            "serial.Serial.isOpen",
            return_value=True,
        ),
        patch(
            "aurorapy.client.AuroraSerialClient.close",
        ) as mock_clientclose,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_PORT: "/dev/ttyUSB7", CONF_ADDRESS: 7},
        )
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})
    expect(len(mock_clientclose.mock_calls)).to_equal(1)
