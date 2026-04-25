"""Tests for the Prana config flow."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

from prana_local_api_client.exceptions import (
    PranaApiCommunicationError as PranaCommunicationError,
)
from tryke import Depends, expect, fixture, test

from homeassistant.components.prana.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER, SOURCE_ZEROCONF
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from ._fixtures import mock_config_entry, mock_prana_api

from tests.common import MockConfigEntry, load_json_object_fixture
from tests.hass_fixtures import hass as hass_fixture, mock_network

ZEROCONF_INFO = ZeroconfServiceInfo(
    ip_address="192.168.1.30",
    ip_addresses=["192.168.1.30"],
    hostname="prana.local",
    name="TestNew._prana._tcp.local.",
    type="_prana._tcp.local.",
    port=1234,
    properties={},
)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


async def _async_load_fixture(hass: HomeAssistant, filename: str) -> dict:
    """Load a fixture file."""
    return await hass.async_add_executor_job(load_json_object_fixture, filename, DOMAIN)


@test
async def zeroconf_new_device_and_confirm(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _api: AsyncMock = Depends(mock_prana_api),
) -> None:
    """Zeroconf discovery shows confirm form and creates a config entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=ZEROCONF_INFO
    )

    device_info = await _async_load_fixture(hass, "device_info.json")

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(device_info["label"])
    expect(result["result"].unique_id).to_equal(device_info["manufactureId"])
    expect(result["result"].data).to_equal({CONF_HOST: "192.168.1.30"})


@test
async def user_flow_with_manual_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _api: AsyncMock = Depends(mock_prana_api),
) -> None:
    """User flow accepts manual host and creates entry after confirmation."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    device_info = await _async_load_fixture(hass, "device_info.json")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_HOST: "192.168.1.40"}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(device_info["label"])
    expect(result["result"].unique_id).to_equal(device_info["manufactureId"])
    expect(result["result"].data).to_equal({CONF_HOST: "192.168.1.40"})


@test
async def communication_error_on_device_info(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    api: AsyncMock = Depends(mock_prana_api),
) -> None:
    """Communication errors when fetching device info surface as form errors."""
    # Setting an invalid device info, for abort the flow.
    device_info_invalid = await _async_load_fixture(hass, "device_info_invalid.json")
    api.get_device_info.return_value = SimpleNamespace(**device_info_invalid)
    api.get_device_info.side_effect = None
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_HOST: "192.168.1.50"}
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("invalid_device")

    # Simulating a communication error.
    device_info = await _async_load_fixture(hass, "device_info.json")
    api.get_device_info.return_value = SimpleNamespace(**device_info)
    api.get_device_info.side_effect = PranaCommunicationError("Network error")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_HOST: "192.168.1.50"}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect("invalid_device_or_unreachable" in result["errors"].values()).to_be(True)

    # Now simulating a successful fetch, without aborting.
    api.get_device_info.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_HOST: "192.168.1.50"}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(device_info["label"])
    expect(result["result"].unique_id).to_equal(device_info["manufactureId"])
    expect(result["result"].data).to_equal({CONF_HOST: "192.168.1.50"})


@test
async def user_flow_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _api: AsyncMock = Depends(mock_prana_api),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Second configuration for the same device should be aborted."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_HOST: "192.168.1.40"}
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def zeroconf_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _api: AsyncMock = Depends(mock_prana_api),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Zeroconf discovery of an already configured device should be aborted."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=ZEROCONF_INFO
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def zeroconf_invalid_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    api: AsyncMock = Depends(mock_prana_api),
) -> None:
    """Zeroconf discovery of an invalid device should be aborted."""
    api.get_device_info.side_effect = PranaCommunicationError("Network error")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=ZEROCONF_INFO
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("invalid_device_or_unreachable")
