"""Test the Teleinfo config flow."""

from unittest.mock import MagicMock

import serial
from tryke import Depends, expect, fixture, test

from homeassistant.components.teleinfo.const import CONF_SERIAL_PORT, DOMAIN
from homeassistant.config_entries import SOURCE_USB, SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.usb import UsbServiceInfo

from ._fixtures import (
    USB_DISCOVERY_INFO,
    mock_config_entry,
    mock_serial_port,
    mock_setup_entry,
    mock_teleinfo,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup: None = Depends(mock_setup_entry),
) -> None:
    """Apply autouse-equivalent fixtures via this trigger."""


@test
async def user_flow_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _teleinfo: MagicMock = Depends(mock_teleinfo),
    serial_port: MagicMock = Depends(mock_serial_port),
) -> None:
    """Test the full happy path: serial port opens, frame is read and decoded."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_SERIAL_PORT: "/dev/ttyUSB0",
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Teleinfo (/dev/ttyUSB0)")

    config_entry = result["result"]
    expect(config_entry.unique_id).to_equal("021861348497")
    expect(config_entry.data).to_equal(
        {
            CONF_SERIAL_PORT: "/dev/ttyUSB0",
        }
    )


@test.cases(
    test.case(
        "cannot_connect",
        side_effect=serial.SerialException("Port not found"),
        expected_error="cannot_connect",
    ),
    test.case(
        "timeout_connect",
        side_effect=TimeoutError("No data"),
        expected_error="timeout_connect",
    ),
    test.case(
        "unknown",
        side_effect=RuntimeError("unexpected"),
        expected_error="unknown",
    ),
)
async def user_flow_error_recovery(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _teleinfo: MagicMock = Depends(mock_teleinfo),
    serial_port: MagicMock = Depends(mock_serial_port),
    *,
    side_effect: Exception,
    expected_error: str,
) -> None:
    """Test the flow recovers after each failure mode when the port starts working."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    serial_port.side_effect = side_effect

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_SERIAL_PORT: "/dev/ttyUSB0"}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": expected_error})

    # Recover: the port now works.
    serial_port.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_SERIAL_PORT: "/dev/ttyUSB0"}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Teleinfo (/dev/ttyUSB0)")


@test
async def user_flow_duplicate(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _teleinfo: MagicMock = Depends(mock_teleinfo),
    _serial_port: MagicMock = Depends(mock_serial_port),
) -> None:
    """Test we abort when the same serial port is already configured."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_SERIAL_PORT: "/dev/ttyUSB0"}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def user_flow_decode_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    teleinfo: MagicMock = Depends(mock_teleinfo),
    _serial_port: MagicMock = Depends(mock_serial_port),
) -> None:
    """Test we handle decode errors from pyteleinfo."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    teleinfo.decode.side_effect = teleinfo.TeleinfoError("bad frame")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_SERIAL_PORT: "/dev/ttyUSB0"}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "unknown"})

    teleinfo.decode.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_SERIAL_PORT: "/dev/ttyUSB0"}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def usb_discovery_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _teleinfo: MagicMock = Depends(mock_teleinfo),
    _serial_port: MagicMock = Depends(mock_serial_port),
) -> None:
    """Test USB discovery happy path: detect → validate → confirm → create entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USB},
        data=USB_DISCOVERY_INFO,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("usb_confirm")

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Teleinfo (/dev/ttyUSB0)")
    expect(result["data"]).to_equal({CONF_SERIAL_PORT: "/dev/ttyUSB0"})
    expect(result["result"].unique_id).to_equal("021861348497")


@test
async def usb_discovery_not_teleinfo(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _teleinfo: MagicMock = Depends(mock_teleinfo),
    serial_port: MagicMock = Depends(mock_serial_port),
) -> None:
    """Test USB discovery aborts when frame read times out (not a Teleinfo device)."""
    serial_port.side_effect = TimeoutError("No data received")

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USB},
        data=USB_DISCOVERY_INFO,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("not_teleinfo_device")


@test
async def usb_discovery_already_configured_updates_path(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _teleinfo: MagicMock = Depends(mock_teleinfo),
    _serial_port: MagicMock = Depends(mock_serial_port),
) -> None:
    """Test USB discovery updates device path when dongle is re-plugged."""
    # Existing entry with same ADCO but old path
    existing_entry = MockConfigEntry(
        title="Teleinfo (/dev/ttyUSB-old)",
        domain=DOMAIN,
        data={CONF_SERIAL_PORT: "/dev/ttyUSB-old"},
        unique_id="021861348497",
    )
    existing_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USB},
        data=UsbServiceInfo(
            device="/dev/ttyUSB-new",
            pid="6015",
            vid="0403",
            serial_number="AB1234",
            manufacturer="FTDI",
            description="FT230X Basic UART",
        ),
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    # Path should be updated to the new device path
    expect(existing_entry.data[CONF_SERIAL_PORT]).to_equal("/dev/ttyUSB-new")


@test
async def usb_discovery_manual_entry_duplicate(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _teleinfo: MagicMock = Depends(mock_teleinfo),
    _serial_port: MagicMock = Depends(mock_serial_port),
) -> None:
    """Test USB discovery aborts when the meter was already added manually."""
    # config_entry has ADCO unique_id — same as what USB discovery will find
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USB},
        data=USB_DISCOVERY_INFO,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def usb_discovery_decode_error_aborts(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    teleinfo: MagicMock = Depends(mock_teleinfo),
    _serial_port: MagicMock = Depends(mock_serial_port),
) -> None:
    """Test USB discovery aborts when frame is read but decode fails."""
    teleinfo.decode.side_effect = teleinfo.TeleinfoError("bad frame")

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USB},
        data=USB_DISCOVERY_INFO,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("not_teleinfo_device")
