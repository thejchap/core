"""Test Modem Caller ID config flow."""

from unittest.mock import AsyncMock, patch

import phone_modem
from tryke import Depends, expect, fixture, test

from homeassistant.components import usb
from homeassistant.components.modem_callerid.const import DOMAIN
from homeassistant.config_entries import SOURCE_USB, SOURCE_USER
from homeassistant.const import CONF_DEVICE, CONF_SOURCE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.usb import UsbServiceInfo

from . import com_port, patch_config_flow_modem

from tests.hass_fixtures import hass as hass_fixture, mock_network

DISCOVERY_INFO = UsbServiceInfo(
    device=phone_modem.DEFAULT_PORT,
    pid="1340",
    vid="0572",
    serial_number="1234",
    description="modem",
    manufacturer="Connexant",
)


@fixture
def _trigger_executor(_mn: None = Depends(mock_network)) -> None:
    """Trigger the hook executor path."""
    return None


def _patch_setup():
    return patch(
        "homeassistant.components.modem_callerid.async_setup_entry",
    )


@test
@patch(
    "homeassistant.components.modem_callerid.config_flow.usb.async_scan_serial_ports",
    AsyncMock(return_value=[com_port()]),
)
async def flow_usb(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test usb discovery flow."""
    with patch_config_flow_modem(), _patch_setup():
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={CONF_SOURCE: SOURCE_USB},
            data=DISCOVERY_INFO,
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("usb_confirm")

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_DEVICE: phone_modem.DEFAULT_PORT},
        )
        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["data"]).to_equal({CONF_DEVICE: com_port().device})


@test
@patch(
    "homeassistant.components.modem_callerid.config_flow.usb.async_scan_serial_ports",
    AsyncMock(return_value=[com_port()]),
)
async def flow_usb_cannot_connect(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test usb flow connection error."""
    with patch_config_flow_modem() as modemmock:
        modemmock.side_effect = phone_modem.exceptions.SerialError
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={CONF_SOURCE: SOURCE_USB}, data=DISCOVERY_INFO
        )
        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("cannot_connect")


@test
@patch(
    "homeassistant.components.modem_callerid.config_flow.usb.async_scan_serial_ports",
    AsyncMock(return_value=[com_port()]),
)
async def flow_user(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test user initialized flow."""
    port = com_port()
    port_select = usb.human_readable_device_name(
        port.device,
        port.serial_number,
        port.manufacturer,
        port.description,
        port.vid,
        port.pid,
    )
    with patch_config_flow_modem(), _patch_setup():
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={CONF_SOURCE: SOURCE_USER},
            data={CONF_DEVICE: port_select},
        )
        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["data"]).to_equal({CONF_DEVICE: port.device})

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={CONF_SOURCE: SOURCE_USER},
            data={CONF_DEVICE: port_select},
        )
        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("no_devices_found")


@test
@patch(
    "homeassistant.components.modem_callerid.config_flow.usb.async_scan_serial_ports",
    AsyncMock(return_value=[com_port()]),
)
async def flow_user_error(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test user initialized flow with unreachable device."""
    port = com_port()
    port_select = usb.human_readable_device_name(
        port.device,
        port.serial_number,
        port.manufacturer,
        port.description,
        port.vid,
        port.pid,
    )
    with patch_config_flow_modem() as modemmock:
        modemmock.side_effect = phone_modem.exceptions.SerialError
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={CONF_SOURCE: SOURCE_USER}, data={CONF_DEVICE: port_select}
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")
        expect(result["errors"]).to_equal({"base": "cannot_connect"})

        modemmock.side_effect = None
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_DEVICE: port_select},
        )
        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["data"]).to_equal({CONF_DEVICE: port.device})


@test
@patch(
    "homeassistant.components.modem_callerid.config_flow.usb.async_scan_serial_ports",
    AsyncMock(return_value=[]),
)
async def flow_user_no_port_list(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test user with no list of ports."""
    with patch_config_flow_modem():
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={CONF_SOURCE: SOURCE_USER},
            data={CONF_DEVICE: phone_modem.DEFAULT_PORT},
        )
        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("no_devices_found")


@test
async def abort_user_with_existing_flow(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test user flow is aborted when another discovery has happened."""
    with patch_config_flow_modem():
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={CONF_SOURCE: SOURCE_USB},
            data=DISCOVERY_INFO,
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("usb_confirm")

        result2 = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={CONF_SOURCE: SOURCE_USER},
            data={},
        )

        expect(result2["type"]).to_be(FlowResultType.ABORT)
        expect(result2["reason"]).to_equal("already_in_progress")
