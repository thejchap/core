"""Test Onkyo config flow."""

from __future__ import annotations

from contextlib import nullcontext
from unittest.mock import AsyncMock

from aioonkyo import ReceiverInfo
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.onkyo.const import (
    DOMAIN,
    OPTION_INPUT_SOURCES,
    OPTION_LISTENING_MODES,
    OPTION_MAX_VOLUME,
    OPTION_MAX_VOLUME_DEFAULT,
    OPTION_VOLUME_RESOLUTION,
)
from homeassistant.config_entries import SOURCE_IGNORE, SOURCE_USER
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.ssdp import (
    ATTR_UPNP_FRIENDLY_NAME,
    SsdpServiceInfo,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

from . import RECEIVER_INFO, RECEIVER_INFO_2, mock_discovery, setup_integration
from ._fixtures import (
    mock_config_entry as mock_config_entry_fx,
    mock_default_discovery,
    mock_setup_entry as mock_setup_entry_fx,
)


def _receiver_display_name(receiver_info: ReceiverInfo) -> str:
    return f"{receiver_info.model_name} ({receiver_info.host})"


@fixture
def _trigger_executor(
    _net: None = Depends(mock_network),
    _setup: AsyncMock = Depends(mock_setup_entry_fx),
    _discovery: None = Depends(mock_default_discovery),
) -> None:
    """Wire autouse fixtures for every test."""


@test
async def manual(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test successful manual."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.MENU)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "manual"}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("manual")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_HOST: RECEIVER_INFO_2.host}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("configure_receiver")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            OPTION_VOLUME_RESOLUTION: 200,
            OPTION_INPUT_SOURCES: ["TV"],
            OPTION_LISTENING_MODES: ["THX"],
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"][CONF_HOST]).to_equal(RECEIVER_INFO_2.host)
    expect(result["result"].unique_id).to_equal(RECEIVER_INFO_2.identifier)
    expect(result["title"]).to_equal(RECEIVER_INFO_2.model_name)


@test.cases(
    test.case("discovery_unknown", None, "unknown"),
    test.case("discovery_empty", [], "cannot_connect"),
    test.case("discovery_other_host", [RECEIVER_INFO], "cannot_connect"),
)
async def manual_recoverable_error(
    discovery_receivers: list[ReceiverInfo] | None,
    error_reason: str,
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test manual with a recoverable error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.MENU)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "manual"}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("manual")

    with mock_discovery(discovery_receivers):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_HOST: RECEIVER_INFO_2.host}
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("manual")
    expect(result["errors"]).to_equal({"base": error_reason})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_HOST: RECEIVER_INFO_2.host}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("configure_receiver")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            OPTION_VOLUME_RESOLUTION: 200,
            OPTION_INPUT_SOURCES: ["TV"],
            OPTION_LISTENING_MODES: ["THX"],
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"][CONF_HOST]).to_equal(RECEIVER_INFO_2.host)
    expect(result["result"].unique_id).to_equal(RECEIVER_INFO_2.identifier)
    expect(result["title"]).to_equal(RECEIVER_INFO_2.model_name)


@test
async def manual_error(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test manual with an error."""
    await setup_integration(hass, mock_config_entry)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.MENU)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "manual"}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("manual")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_HOST: RECEIVER_INFO.host}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def eiscp_discovery(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test successful eiscp discovery."""
    await setup_integration(hass, mock_config_entry)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.MENU)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "eiscp_discovery"}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("eiscp_discovery")

    devices = result["data_schema"].schema["device"].container
    expect(devices).to_equal(
        {RECEIVER_INFO_2.identifier: _receiver_display_name(RECEIVER_INFO_2)}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"device": RECEIVER_INFO_2.identifier}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("configure_receiver")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            OPTION_VOLUME_RESOLUTION: 200,
            OPTION_INPUT_SOURCES: ["TV"],
            OPTION_LISTENING_MODES: ["THX"],
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"][CONF_HOST]).to_equal(RECEIVER_INFO_2.host)
    expect(result["result"].unique_id).to_equal(RECEIVER_INFO_2.identifier)
    expect(result["title"]).to_equal(RECEIVER_INFO_2.model_name)


@test.cases(
    test.case("discovery_unknown", None, "unknown"),
    test.case("discovery_empty", [], "no_devices_found"),
    test.case("discovery_other_host", [RECEIVER_INFO], "no_devices_found"),
)
async def eiscp_discovery_error(
    discovery_receivers: list[ReceiverInfo] | None,
    error_reason: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test eiscp discovery with an error."""
    await setup_integration(hass, mock_config_entry)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.MENU)
    expect(result["step_id"]).to_equal("user")

    with mock_discovery(discovery_receivers):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"next_step_id": "eiscp_discovery"}
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal(error_reason)


@test
async def eiscp_discovery_replace_ignored_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test eiscp discovery can replace an ignored config entry."""
    mock_config_entry.source = SOURCE_IGNORE
    await setup_integration(hass, mock_config_entry)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.MENU)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "eiscp_discovery"}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("eiscp_discovery")

    devices = result["data_schema"].schema["device"].container
    expect(devices).to_equal(
        {
            RECEIVER_INFO.identifier: _receiver_display_name(RECEIVER_INFO),
            RECEIVER_INFO_2.identifier: _receiver_display_name(RECEIVER_INFO_2),
        }
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"device": RECEIVER_INFO.identifier}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("configure_receiver")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            OPTION_VOLUME_RESOLUTION: 200,
            OPTION_INPUT_SOURCES: ["TV"],
            OPTION_LISTENING_MODES: ["THX"],
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"][CONF_HOST]).to_equal(RECEIVER_INFO.host)
    expect(result["result"].unique_id).to_equal(RECEIVER_INFO.identifier)
    expect(result["title"]).to_equal(RECEIVER_INFO.model_name)

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)


@test
async def ssdp_discovery(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test successful SSDP discovery."""
    await setup_integration(hass, mock_config_entry)

    discovery_info = SsdpServiceInfo(
        ssdp_location=f"http://{RECEIVER_INFO_2.host}:8080",
        upnp={ATTR_UPNP_FRIENDLY_NAME: "Onkyo Receiver"},
        ssdp_usn="uuid:mock_usn",
        ssdp_udn="uuid:00000000-0000-0000-0000-000000000000",
        ssdp_st="mock_st",
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_SSDP}, data=discovery_info
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("configure_receiver")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            OPTION_VOLUME_RESOLUTION: 200,
            OPTION_INPUT_SOURCES: ["TV"],
            OPTION_LISTENING_MODES: ["THX"],
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"][CONF_HOST]).to_equal(RECEIVER_INFO_2.host)
    expect(result["result"].unique_id).to_equal(RECEIVER_INFO_2.identifier)
    expect(result["title"]).to_equal(RECEIVER_INFO_2.model_name)


@test.cases(
    test.case("ssdp_location_none", None, False, None, "unknown"),
    test.case("ssdp_location_bad", "http://", False, None, "unknown"),
    test.case(
        "discovery_unknown",
        f"http://{RECEIVER_INFO_2.host}:8080",
        True,
        None,
        "unknown",
    ),
    test.case(
        "discovery_empty",
        f"http://{RECEIVER_INFO_2.host}:8080",
        True,
        [],
        "cannot_connect",
    ),
    test.case(
        "discovery_other_host",
        f"http://{RECEIVER_INFO_2.host}:8080",
        True,
        [RECEIVER_INFO],
        "cannot_connect",
    ),
    test.case(
        "already_configured",
        f"http://{RECEIVER_INFO.host}:8080",
        False,
        None,
        "already_configured",
    ),
)
async def ssdp_discovery_error(
    ssdp_location: str | None,
    use_mock_discovery: bool,
    discovery_receivers: list[ReceiverInfo] | None,
    error_reason: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test SSDP discovery with an error."""
    await setup_integration(hass, mock_config_entry)

    discovery_info = SsdpServiceInfo(
        ssdp_location=ssdp_location,
        upnp={ATTR_UPNP_FRIENDLY_NAME: "Onkyo Receiver"},
        ssdp_usn="uuid:mock_usn",
        ssdp_udn="uuid:00000000-0000-0000-0000-000000000000",
        ssdp_st="mock_st",
    )

    discovery_cm = (
        mock_discovery(discovery_receivers) if use_mock_discovery else nullcontext()
    )
    with discovery_cm:
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_SSDP},
            data=discovery_info,
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal(error_reason)


@test
async def configure(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test receiver configure."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.MENU)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "manual"}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("manual")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_HOST: RECEIVER_INFO.host}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("configure_receiver")
    expect(result["description_placeholders"]["name"]).to_equal(
        _receiver_display_name(RECEIVER_INFO)
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            OPTION_VOLUME_RESOLUTION: 200,
            OPTION_INPUT_SOURCES: [],
            OPTION_LISTENING_MODES: ["THX"],
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("configure_receiver")
    expect(result["errors"]).to_equal(
        {OPTION_INPUT_SOURCES: "empty_input_source_list"}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            OPTION_VOLUME_RESOLUTION: 200,
            OPTION_INPUT_SOURCES: ["TV"],
            OPTION_LISTENING_MODES: [],
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("configure_receiver")
    expect(result["errors"]).to_equal(
        {OPTION_LISTENING_MODES: "empty_listening_mode_list"}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            OPTION_VOLUME_RESOLUTION: 200,
            OPTION_INPUT_SOURCES: ["TV"],
            OPTION_LISTENING_MODES: ["THX"],
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["options"]).to_equal(
        {
            OPTION_VOLUME_RESOLUTION: 200,
            OPTION_MAX_VOLUME: OPTION_MAX_VOLUME_DEFAULT,
            OPTION_INPUT_SOURCES: {"12": "TV"},
            OPTION_LISTENING_MODES: {"04": "THX"},
        }
    )


@test
async def reconfigure(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test successful reconfigure flow."""
    await setup_integration(hass, mock_config_entry)

    old_host = mock_config_entry.data[CONF_HOST]
    old_options = mock_config_entry.options

    result = await mock_config_entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("manual")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_HOST: mock_config_entry.data[CONF_HOST]}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("configure_receiver")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={OPTION_VOLUME_RESOLUTION: 200}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")

    expect(mock_config_entry.data[CONF_HOST]).to_equal(old_host)
    expect(mock_config_entry.options[OPTION_VOLUME_RESOLUTION]).to_equal(200)
    for option, option_value in old_options.items():
        if option == OPTION_VOLUME_RESOLUTION:
            continue
        expect(mock_config_entry.options[option]).to_equal(option_value)


@test
async def reconfigure_error(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test reconfigure flow with an error."""
    await setup_integration(hass, mock_config_entry)

    old_unique_id = mock_config_entry.unique_id

    result = await mock_config_entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("manual")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_HOST: RECEIVER_INFO_2.host}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unique_id_mismatch")

    # Unique id should remain unchanged.
    expect(mock_config_entry.unique_id).to_equal(old_unique_id)


@test
async def options_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test options flow."""
    await setup_integration(hass, mock_config_entry)

    old_volume_resolution = mock_config_entry.options[OPTION_VOLUME_RESOLUTION]

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            OPTION_MAX_VOLUME: 42,
            OPTION_INPUT_SOURCES: [],
            OPTION_LISTENING_MODES: ["STEREO"],
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")
    expect(result["errors"]).to_equal(
        {OPTION_INPUT_SOURCES: "empty_input_source_list"}
    )

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            OPTION_MAX_VOLUME: 42,
            OPTION_INPUT_SOURCES: ["TV"],
            OPTION_LISTENING_MODES: [],
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")
    expect(result["errors"]).to_equal(
        {OPTION_LISTENING_MODES: "empty_listening_mode_list"}
    )

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            OPTION_MAX_VOLUME: 42,
            OPTION_INPUT_SOURCES: ["TV"],
            OPTION_LISTENING_MODES: ["STEREO"],
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("names")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            OPTION_INPUT_SOURCES: {"TV": "television"},
            OPTION_LISTENING_MODES: {"STEREO": "Duophonia"},
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(
        {
            OPTION_VOLUME_RESOLUTION: old_volume_resolution,
            OPTION_MAX_VOLUME: 42.0,
            OPTION_INPUT_SOURCES: {"12": "television"},
            OPTION_LISTENING_MODES: {"00": "Duophonia"},
        }
    )
