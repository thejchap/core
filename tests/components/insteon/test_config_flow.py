"""Test the config flow for the Insteon integration."""

from collections.abc import Callable
from typing import Any
from unittest.mock import AsyncMock, patch

from tryke import Depends, expect, fixture, test
from voluptuous_serialize import convert

from homeassistant import config_entries
from homeassistant.components.insteon.config_flow import (
    STEP_HUB_V1,
    STEP_HUB_V2,
    STEP_PLM,
    STEP_PLM_MANUALLY,
)
from homeassistant.components.insteon.const import CONF_HUB_VERSION, DOMAIN
from homeassistant.config_entries import ConfigEntryState, ConfigFlowResult
from homeassistant.const import CONF_DEVICE, CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo
from homeassistant.helpers.service_info.usb import UsbServiceInfo

from .const import (
    MOCK_DEVICE,
    MOCK_USER_INPUT_HUB_V1,
    MOCK_USER_INPUT_HUB_V2,
    MOCK_USER_INPUT_PLM,
    MOCK_USER_INPUT_PLM_MANUAL,
    PATCH_ASYNC_SETUP_ENTRY,
    PATCH_CONNECTION,
    PATCH_USB_LIST,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

USB_PORTS = {"/dev/ttyUSB0": "/dev/ttyUSB0", MOCK_DEVICE: MOCK_DEVICE}


async def mock_successful_connection(*args, **kwargs):
    """Return a successful connection."""
    return True


async def mock_usb_list(hass: HomeAssistant):
    """Return a mock list of USB devices."""
    return USB_PORTS


async def mock_failed_connection(*args, **kwargs):
    """Return a failed connection."""
    raise ConnectionError("Connection failed")


@fixture
def patch_usb_list():
    """Patch USB list."""
    with patch(
        PATCH_USB_LIST,
        mock_usb_list,
    ):
        yield


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _usb: None = Depends(patch_usb_list),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


async def _init_form(hass: HomeAssistant, modem_type: str) -> ConfigFlowResult:
    """Run the user form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.MENU)

    return await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": modem_type},
    )


async def _device_form(
    hass: HomeAssistant,
    flow_id: str,
    connection: Callable[..., Any],
    user_input: dict[str, Any] | None,
) -> tuple[ConfigFlowResult, AsyncMock]:
    """Test the PLM, Hub v1 or Hub v2 form."""
    with (
        patch(
            PATCH_CONNECTION,
            new=connection,
        ),
        patch(
            PATCH_ASYNC_SETUP_ENTRY,
            return_value=True,
        ) as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_configure(flow_id, user_input)
        await hass.async_block_till_done()
    return result, mock_setup_entry


@test
async def form_select_modem(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we get a modem form."""
    result = await _init_form(hass, STEP_HUB_V2)
    expect(result["step_id"]).to_equal(STEP_HUB_V2)
    expect(result["type"]).to_be(FlowResultType.FORM)


@test
async def fail_on_existing(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we fail if the integration is already configured."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        entry_id="abcde12345",
        data={**MOCK_USER_INPUT_HUB_V2, CONF_HUB_VERSION: 2},
        options={},
    )
    config_entry.add_to_hass(hass)
    expect(config_entry.state).to_be(ConfigEntryState.NOT_LOADED)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        data={**MOCK_USER_INPUT_HUB_V2, CONF_HUB_VERSION: 2},
        context={"source": config_entries.SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("single_instance_allowed")


@test
async def form_select_plm(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we set up the PLM correctly."""
    result = await _init_form(hass, STEP_PLM)

    result2, mock_setup_entry = await _device_form(
        hass, result["flow_id"], mock_successful_connection, MOCK_USER_INPUT_PLM
    )
    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["data"]).to_equal(MOCK_USER_INPUT_PLM)

    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_select_plm_no_usb(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we set up the PLM when no comm ports are found."""
    temp_usb_list = dict(USB_PORTS)
    USB_PORTS.clear()
    result = await _init_form(hass, STEP_PLM)

    result2, _ = await _device_form(
        hass, result["flow_id"], mock_successful_connection, None
    )
    USB_PORTS.update(temp_usb_list)
    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["step_id"]).to_equal(STEP_PLM_MANUALLY)


@test
async def form_select_plm_manual(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we set up the PLM correctly."""
    result = await _init_form(hass, STEP_PLM)

    result2, mock_setup_entry = await _device_form(
        hass, result["flow_id"], mock_failed_connection, MOCK_USER_INPUT_PLM_MANUAL
    )

    result3, mock_setup_entry = await _device_form(
        hass, result2["flow_id"], mock_successful_connection, MOCK_USER_INPUT_PLM
    )
    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result3["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result3["data"]).to_equal(MOCK_USER_INPUT_PLM)

    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_select_hub_v1(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we set up the Hub v1 correctly."""
    result = await _init_form(hass, STEP_HUB_V1)

    result2, mock_setup_entry = await _device_form(
        hass, result["flow_id"], mock_successful_connection, MOCK_USER_INPUT_HUB_V1
    )
    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["data"]).to_equal(
        {
            **MOCK_USER_INPUT_HUB_V1,
            CONF_HUB_VERSION: 1,
        }
    )

    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_select_hub_v2(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we set up the Hub v2 correctly."""
    result = await _init_form(hass, STEP_HUB_V2)

    result2, mock_setup_entry = await _device_form(
        hass, result["flow_id"], mock_successful_connection, MOCK_USER_INPUT_HUB_V2
    )
    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["data"]).to_equal(
        {
            **MOCK_USER_INPUT_HUB_V2,
            CONF_HUB_VERSION: 2,
        }
    )

    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_discovery_dhcp(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the discovery of the Hub via DHCP."""
    discovery_info = DhcpServiceInfo("1.2.3.4", "", "aabbccddeeff")
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_DHCP}, data=discovery_info
    )
    expect(result["type"]).to_be(FlowResultType.MENU)

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": STEP_HUB_V2},
    )
    expect(result2["type"]).to_be(FlowResultType.FORM)
    schema = convert(result2["data_schema"])
    found_host = False
    for field in schema:
        if field["name"] == CONF_HOST:
            expect(field["default"]).to_equal("1.2.3.4")
            found_host = True
    expect(found_host).to_be(True)


@test
async def failed_connection_plm(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test a failed connection with the PLM."""
    result = await _init_form(hass, STEP_PLM)

    result2, _ = await _device_form(
        hass, result["flow_id"], mock_failed_connection, MOCK_USER_INPUT_PLM
    )
    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def failed_connection_plm_manually(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test a failed connection with the PLM."""
    result = await _init_form(hass, STEP_PLM)

    _result2, _ = await _device_form(
        hass, result["flow_id"], mock_successful_connection, MOCK_USER_INPUT_PLM_MANUAL
    )
    result3, _ = await _device_form(
        hass, result["flow_id"], mock_failed_connection, MOCK_USER_INPUT_PLM
    )
    expect(result3["type"]).to_be(FlowResultType.FORM)
    expect(result3["errors"]).to_equal({"base": "cannot_connect"})


@test
async def failed_connection_hub(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test a failed connection with a Hub."""
    result = await _init_form(hass, STEP_HUB_V2)

    result2, _ = await _device_form(
        hass, result["flow_id"], mock_failed_connection, MOCK_USER_INPUT_HUB_V2
    )
    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def discovery_via_usb(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test usb flow."""
    discovery_info = UsbServiceInfo(
        device="/dev/ttyINSTEON",
        pid="AAAA",
        vid="AAAA",
        serial_number="1234",
        description="insteon radio",
        manufacturer="test",
    )
    result = await hass.config_entries.flow.async_init(
        "insteon", context={"source": config_entries.SOURCE_USB}, data=discovery_info
    )
    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("confirm_usb")

    with patch(PATCH_CONNECTION):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["data"]).to_equal({"device": "/dev/ttyINSTEON"})


@test
async def discovery_via_usb_already_setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test usb flow -- already setup."""
    MockConfigEntry(
        domain=DOMAIN, data={CONF_DEVICE: {CONF_DEVICE: "/dev/ttyUSB1"}}
    ).add_to_hass(hass)

    discovery_info = UsbServiceInfo(
        device="/dev/ttyINSTEON",
        pid="AAAA",
        vid="AAAA",
        serial_number="1234",
        description="insteon radio",
        manufacturer="test",
    )
    result = await hass.config_entries.flow.async_init(
        "insteon", context={"source": config_entries.SOURCE_USB}, data=discovery_info
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("single_instance_allowed")
