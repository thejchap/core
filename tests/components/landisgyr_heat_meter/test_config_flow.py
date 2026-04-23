"""Test the Landis + Gyr Heat Meter config flow."""

from dataclasses import dataclass
from unittest.mock import AsyncMock, patch

import serial
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.landisgyr_heat_meter import DOMAIN
from homeassistant.components.usb import USBDevice
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

API_HEAT_METER_SERVICE = "homeassistant.components.landisgyr_heat_meter.config_flow.ultraheat_api.HeatMeterService"


@fixture
def _trigger_executor(
    _mn: None = Depends(mock_network),
    _mse: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Trigger the hook executor path."""
    return None


def _make_serial_port() -> USBDevice:
    """Mock of a serial port."""
    return USBDevice(
        device="/dev/ttyUSB1234",
        vid="162E",
        pid="269C",
        serial_number="1234",
        manufacturer="Virtual serial port",
        description="Some serial port",
    )


@dataclass
class MockUltraheatRead:
    """Mock of the response from the read method of the Ultraheat API."""

    model: str
    device_number: str


@test
async def manual_entry(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test manual entry."""
    with patch(API_HEAT_METER_SERVICE) as mock_heat_meter:
        mock_heat_meter().read.return_value = MockUltraheatRead("LUGCUH50", "123456789")

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")
        expect(result["errors"]).to_equal({})

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"device": "Enter Manually"}
        )

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("setup_serial_manual_path")
        expect(result["errors"]).to_equal({})

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"device": "/dev/ttyUSB0"}
        )

        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["title"]).to_equal("LUGCUH50")
        expect(result["data"]).to_equal(
            {
                "device": "/dev/ttyUSB0",
                "model": "LUGCUH50",
                "device_number": "123456789",
            }
        )


@test
async def list_entry(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test select from list entry."""
    with (
        patch(API_HEAT_METER_SERVICE) as mock_heat_meter,
        patch(
            "homeassistant.components.landisgyr_heat_meter.config_flow.usb.async_scan_serial_ports",
            return_value=[_make_serial_port()],
        ),
    ):
        mock_heat_meter().read.return_value = MockUltraheatRead("LUGCUH50", "123456789")
        port = _make_serial_port()

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")
        expect(result["errors"]).to_equal({})

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"device": port.device}
        )
        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["title"]).to_equal("LUGCUH50")
        expect(result["data"]).to_equal(
            {
                "device": port.device,
                "model": "LUGCUH50",
                "device_number": "123456789",
            }
        )


@test
async def manual_entry_fail(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test manual entry fails."""
    with patch(API_HEAT_METER_SERVICE) as mock_heat_meter:
        mock_heat_meter().read.side_effect = serial.SerialException

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")
        expect(result["errors"]).to_equal({})

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"device": "Enter Manually"}
        )

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("setup_serial_manual_path")
        expect(result["errors"]).to_equal({})

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"device": "/dev/ttyUSB0"}
        )

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("setup_serial_manual_path")
        expect(result["errors"]).to_equal({"base": "cannot_connect"})


@test
async def list_entry_fail(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test select from list entry fails."""
    with (
        patch(API_HEAT_METER_SERVICE) as mock_heat_meter,
        patch(
            "homeassistant.components.landisgyr_heat_meter.config_flow.usb.async_scan_serial_ports",
            return_value=[_make_serial_port()],
        ),
    ):
        mock_heat_meter().read.side_effect = serial.SerialException
        port = _make_serial_port()

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")
        expect(result["errors"]).to_equal({})

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"device": port.device}
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")
        expect(result["errors"]).to_equal({"base": "cannot_connect"})


@test
async def already_configured(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we abort if the Heat Meter is already configured."""
    with (
        patch(API_HEAT_METER_SERVICE) as mock_heat_meter,
        patch(
            "homeassistant.components.landisgyr_heat_meter.config_flow.usb.async_scan_serial_ports",
            return_value=[_make_serial_port()],
        ),
    ):
        entry_data = {
            "device": "/dev/USB0",
            "model": "LUGCUH50",
            "device_number": "123456789",
        }
        mock_entry = MockConfigEntry(
            domain=DOMAIN, unique_id="123456789", data=entry_data
        )
        mock_entry.add_to_hass(hass)

        await hass.config_entries.async_setup(mock_entry.entry_id)
        await hass.async_block_till_done()

        mock_heat_meter().read.return_value = MockUltraheatRead("LUGCUH50", "123456789")
        port = _make_serial_port()

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"device": port.device}
        )

        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("already_configured")
