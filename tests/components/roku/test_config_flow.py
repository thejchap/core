"""Test the Roku config flow."""

from __future__ import annotations

import dataclasses
from unittest.mock import AsyncMock, MagicMock

from rokuecp import Device as RokuDevice, RokuConnectionError
from tryke import Depends, expect, fixture, test

from homeassistant.components.roku.const import CONF_PLAY_MEDIA_APP_ID, DOMAIN
from homeassistant.config_entries import (
    SOURCE_HOMEKIT,
    SOURCE_SSDP,
    SOURCE_USER,
    ConfigFlowResult,
)
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_SOURCE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import (
    HOMEKIT_HOST,
    HOST,
    MOCK_HOMEKIT_DISCOVERY_INFO,
    MOCK_SSDP_DISCOVERY_INFO,
    NAME_ROKUTV,
    UPNP_FRIENDLY_NAME,
)
from ._fixtures import (
    mock_config_entry as mock_config_entry_fx,
    mock_device as mock_device_fx,
    mock_roku_config_flow as mock_roku_config_flow_fx,
    mock_roku_config_flow_rokutv as mock_roku_config_flow_rokutv_fx,
    mock_setup_entry as mock_setup_entry_fx,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

RECONFIGURE_HOST = "192.168.1.190"


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Wire mock_network for every test."""


@test
async def duplicate_error(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
    _flow: MagicMock = Depends(mock_roku_config_flow_fx),
) -> None:
    """Test that errors are shown when duplicates are added."""
    mock_config_entry.add_to_hass(hass)

    user_input = {CONF_HOST: mock_config_entry.data[CONF_HOST]}
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}, data=user_input
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")

    user_input = {CONF_HOST: mock_config_entry.data[CONF_HOST]}
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}, data=user_input
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")

    discovery_info = dataclasses.replace(MOCK_SSDP_DISCOVERY_INFO)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_SSDP}, data=discovery_info
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def form(
    hass: HomeAssistant = Depends(hass_fixture),
    _flow: MagicMock = Depends(mock_roku_config_flow_fx),
    _setup: None = Depends(mock_setup_entry_fx),
) -> None:
    """Test the user step."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    user_input = {CONF_HOST: HOST}
    result = await hass.config_entries.flow.async_configure(
        flow_id=result["flow_id"], user_input=user_input
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("My Roku 3")
    expect("data" in result).to_be(True)
    expect(result["data"][CONF_HOST]).to_equal(HOST)
    expect("result" in result).to_be(True)
    expect(result["result"].unique_id).to_equal("1GU48T017973")


@test
async def form_cannot_connect(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_roku_config_flow: MagicMock = Depends(mock_roku_config_flow_fx),
) -> None:
    """Test we handle cannot connect roku error."""
    mock_roku_config_flow.update.side_effect = RokuConnectionError

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        flow_id=result["flow_id"], user_input={CONF_HOST: HOST}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "cannot_connect"})


@test
async def form_unknown_error(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_roku_config_flow: MagicMock = Depends(mock_roku_config_flow_fx),
) -> None:
    """Test we handle unknown error."""
    mock_roku_config_flow.update.side_effect = Exception

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}
    )
    user_input = {CONF_HOST: HOST}
    result = await hass.config_entries.flow.async_configure(
        flow_id=result["flow_id"], user_input=user_input
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unknown")


@test
async def homekit_cannot_connect(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_roku_config_flow: MagicMock = Depends(mock_roku_config_flow_fx),
) -> None:
    """Test we abort homekit flow on connection error."""
    mock_roku_config_flow.update.side_effect = RokuConnectionError

    discovery_info = dataclasses.replace(MOCK_HOMEKIT_DISCOVERY_INFO)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_HOMEKIT},
        data=discovery_info,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("cannot_connect")


@test
async def homekit_unknown_error(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_roku_config_flow: MagicMock = Depends(mock_roku_config_flow_fx),
) -> None:
    """Test we abort homekit flow on unknown error."""
    mock_roku_config_flow.update.side_effect = Exception

    discovery_info = dataclasses.replace(MOCK_HOMEKIT_DISCOVERY_INFO)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_HOMEKIT},
        data=discovery_info,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unknown")


@test
async def homekit_discovery(
    hass: HomeAssistant = Depends(hass_fixture),
    _flow: MagicMock = Depends(mock_roku_config_flow_rokutv_fx),
    _setup: None = Depends(mock_setup_entry_fx),
) -> None:
    """Test the homekit discovery flow."""
    discovery_info = dataclasses.replace(MOCK_HOMEKIT_DISCOVERY_INFO)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_HOMEKIT}, data=discovery_info
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("discovery_confirm")
    expect(result["description_placeholders"]).to_equal({CONF_NAME: NAME_ROKUTV})

    result = await hass.config_entries.flow.async_configure(
        flow_id=result["flow_id"], user_input={}
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(NAME_ROKUTV)
    expect("data" in result).to_be(True)
    expect(result["data"][CONF_HOST]).to_equal(HOMEKIT_HOST)
    expect(result["data"][CONF_NAME]).to_equal(NAME_ROKUTV)

    discovery_info = dataclasses.replace(MOCK_HOMEKIT_DISCOVERY_INFO)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_HOMEKIT}, data=discovery_info
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def ssdp_cannot_connect(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_roku_config_flow: MagicMock = Depends(mock_roku_config_flow_fx),
) -> None:
    """Test we abort SSDP flow on connection error."""
    mock_roku_config_flow.update.side_effect = RokuConnectionError

    discovery_info = dataclasses.replace(MOCK_SSDP_DISCOVERY_INFO)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_SSDP},
        data=discovery_info,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("cannot_connect")


@test
async def ssdp_unknown_error(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_roku_config_flow: MagicMock = Depends(mock_roku_config_flow_fx),
) -> None:
    """Test we abort SSDP flow on unknown error."""
    mock_roku_config_flow.update.side_effect = Exception

    discovery_info = dataclasses.replace(MOCK_SSDP_DISCOVERY_INFO)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_SSDP},
        data=discovery_info,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unknown")


@test
async def ssdp_discovery(
    hass: HomeAssistant = Depends(hass_fixture),
    _flow: MagicMock = Depends(mock_roku_config_flow_fx),
    _setup: None = Depends(mock_setup_entry_fx),
) -> None:
    """Test the SSDP discovery flow."""
    discovery_info = dataclasses.replace(MOCK_SSDP_DISCOVERY_INFO)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_SSDP}, data=discovery_info
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("discovery_confirm")
    expect(result["description_placeholders"]).to_equal(
        {CONF_NAME: UPNP_FRIENDLY_NAME}
    )

    result = await hass.config_entries.flow.async_configure(
        flow_id=result["flow_id"], user_input={}
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(UPNP_FRIENDLY_NAME)
    expect(bool(result["data"])).to_be(True)
    expect(result["data"][CONF_HOST]).to_equal(HOST)
    expect(result["data"][CONF_NAME]).to_equal(UPNP_FRIENDLY_NAME)


@test
async def options_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(mock_setup_entry_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test options config flow."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("init")

    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_PLAY_MEDIA_APP_ID: "782875"},
    )
    expect(result2.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2.get("data")).to_equal({CONF_PLAY_MEDIA_APP_ID: "782875"})


async def _start_reconfigure_flow(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> ConfigFlowResult:
    """Initialize a reconfigure flow."""
    mock_config_entry.add_to_hass(hass)

    reconfigure_result = await mock_config_entry.start_reconfigure_flow(hass)
    expect(reconfigure_result["type"]).to_be(FlowResultType.FORM)
    expect(reconfigure_result["step_id"]).to_equal("user")

    return await hass.config_entries.flow.async_configure(
        reconfigure_result["flow_id"],
        {CONF_HOST: RECONFIGURE_HOST},
    )


@test
async def reconfigure_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
    _flow: MagicMock = Depends(mock_roku_config_flow_fx),
) -> None:
    """Test reconfigure flow."""
    result = await _start_reconfigure_flow(hass, mock_config_entry)

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")

    entry = hass.config_entries.async_get_entry(mock_config_entry.entry_id)
    expect(bool(entry)).to_be(True)
    expect(entry.data).to_equal({CONF_HOST: RECONFIGURE_HOST})


@test
async def reconfigure_unique_id_mismatch(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_device: RokuDevice = Depends(mock_device_fx),
    _setup: AsyncMock = Depends(mock_setup_entry_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
    _flow: MagicMock = Depends(mock_roku_config_flow_fx),
) -> None:
    """Ensure reconfigure flow aborts when the device changes."""
    mock_device.info.serial_number = "RECONFIG"

    result = await _start_reconfigure_flow(hass, mock_config_entry)

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("wrong_device")
