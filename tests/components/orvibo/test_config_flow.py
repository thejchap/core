"""Tests for the Orvibo config flow in Home Assistant core."""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import MagicMock, patch

with patch("socket.socket.bind"):
    from orvibo.s20 import S20Exception
from tryke import Depends, expect, fixture, test
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components.orvibo.const import CONF_SWITCH_LIST, DEFAULT_NAME, DOMAIN
from homeassistant.const import CONF_HOST, CONF_MAC
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

from ._fixtures import (
    mock_config_entry as mock_config_entry_fx,
    mock_discover as mock_discover_fx,
    mock_s20 as mock_s20_fx,
    mock_setup_entry as mock_setup_entry_fx,
)


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Wire mock_network for every test."""


@test
async def user_menu_display(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Initial step displays the user menu correctly."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_equal(FlowResultType.MENU)
    expect(result["step_id"]).to_equal("user")
    expect(set(result["menu_options"])).to_equal({"start_discovery", "edit"})


@test.cases(
    test.case(
        "with_mac",
        {CONF_HOST: "192.168.1.2", CONF_MAC: "ac:cf:23:12:34:56"},
        "ac:cf:23:12:34:56",
        None,
    ),
    test.case(
        "discovered_mac",
        {CONF_HOST: "192.168.1.2"},
        "aa:bb:cc:dd:ee:ff",
        b"\xaa\xbb\xcc\xdd\xee\xff",
    ),
)
async def edit_flow_success(
    user_input: dict[str, Any],
    expected_mac: str,
    mock_mac_bytes: bytes | None,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_discover: MagicMock = Depends(mock_discover_fx),
    mock_setup_entry: MagicMock = Depends(mock_setup_entry_fx),
    mock_s20: MagicMock = Depends(mock_s20_fx),
) -> None:
    """Test manual flow succeeds with provided MAC or discovered MAC."""
    mock_s20.return_value._mac = mock_mac_bytes
    mock_discover.return_value = {"192.168.1.2": {"mac": b"\xaa\xbb\xcc\xdd\xee\xff"}}

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "edit"}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input
    )

    expect(result["type"]).to_equal(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(f"{DEFAULT_NAME} (192.168.1.2)")
    expect(result["data"][CONF_HOST]).to_equal("192.168.1.2")
    expect(result["data"][CONF_MAC]).to_equal(expected_mac)
    expect(result["result"].unique_id).to_equal(expected_mac)


@test.cases(
    test.case(
        "invalid_mac",
        {CONF_HOST: "192.168.1.2", CONF_MAC: "not_a_mac"},
        "invalid_mac",
        None,
        b"dummy",
    ),
    test.case(
        "cannot_discover",
        {CONF_HOST: "192.168.1.99"},
        "cannot_discover",
        None,
        None,
    ),
    test.case(
        "cannot_connect",
        {CONF_HOST: "192.168.1.3", CONF_MAC: "ac:cf:23:12:34:56"},
        "cannot_connect",
        S20Exception("Connection failed"),
        b"dummy",
    ),
)
async def edit_flow_errors(
    user_input: dict[str, Any],
    expected_error: str,
    mock_exception: Exception | None,
    mock_mac_bytes: bytes | None,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_s20: MagicMock = Depends(mock_s20_fx),
    mock_discover: MagicMock = Depends(mock_discover_fx),
    mock_setup_entry: MagicMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test various errors in the manual (edit) step and recover."""
    mock_discover.return_value = {}
    mock_s20.side_effect = mock_exception
    mock_s20.return_value._mac = mock_mac_bytes

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "edit"}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input
    )

    expect(result["type"]).to_equal(FlowResultType.FORM)
    expect(result["errors"]["base"]).to_equal(expected_error)

    mock_s20.side_effect = None
    mock_s20.return_value._mac = b"\xac\xcf\x23\x12\x34\x56"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "192.168.1.2", CONF_MAC: "ac:cf:23:12:34:56"},
    )

    expect(result["type"]).to_equal(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(f"{DEFAULT_NAME} (192.168.1.2)")
    expect(result["data"][CONF_HOST]).to_equal("192.168.1.2")
    expect(result["data"][CONF_MAC]).to_equal("ac:cf:23:12:34:56")


@test
async def discovery_success(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_discover: MagicMock = Depends(mock_discover_fx),
    mock_setup_entry: MagicMock = Depends(mock_setup_entry_fx),
) -> None:
    """Verify discovery finds devices and completes config entry creation."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_equal(FlowResultType.MENU)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "start_discovery"}
    )
    expect(result["type"]).to_equal(FlowResultType.SHOW_PROGRESS)
    expect(result["step_id"]).to_equal("start_discovery")
    expect(result["progress_action"]).to_equal("start_discovery")

    await hass.async_block_till_done()

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["type"]).to_equal(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("choose_switch")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_SWITCH_LIST: "192.168.1.100"}
    )

    expect(result["type"]).to_equal(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(f"{DEFAULT_NAME} (192.168.1.100)")
    expect(result["data"][CONF_HOST]).to_equal("192.168.1.100")
    expect(result["data"][CONF_MAC]).to_equal("ac:cf:23:12:34:56")
    expect(result["result"].unique_id).to_equal("ac:cf:23:12:34:56")


@test
async def discovery_no_devices(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_discover: MagicMock = Depends(mock_discover_fx),
    mock_s20: MagicMock = Depends(mock_s20_fx),
    mock_setup_entry: MagicMock = Depends(mock_setup_entry_fx),
) -> None:
    """Discovery with no found devices should go to discovery_failed and recover via edit."""
    mock_discover.return_value = {}

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "start_discovery"}
    )
    await hass.async_block_till_done()

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["type"]).to_equal(FlowResultType.MENU)
    expect(result["step_id"]).to_equal("discovery_failed")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "edit"}
    )

    expect(result["type"]).to_equal(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("edit")

    mock_s20.return_value._mac = b"\xaa\xbb\xcc\xdd\xee\xff"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "192.168.1.10", CONF_MAC: "aa:bb:cc:dd:ee:ff"},
    )

    expect(result["type"]).to_equal(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(f"{DEFAULT_NAME} (192.168.1.10)")
    expect(result["data"][CONF_HOST]).to_equal("192.168.1.10")
    expect(result["data"][CONF_MAC]).to_equal("aa:bb:cc:dd:ee:ff")


@test.cases(
    test.case(
        "with_mac",
        {CONF_HOST: "192.168.1.5", CONF_MAC: "ac:cf:23:12:34:56"},
        "ac:cf:23:12:34:56",
        None,
    ),
    test.case(
        "discovered_mac",
        {CONF_HOST: "192.168.1.5"},
        "11:22:33:44:55:66",
        b"\x11\x22\x33\x44\x55\x66",
    ),
)
async def import_flow_success(
    import_data: dict[str, Any],
    expected_mac: str,
    mock_mac_bytes: bytes | None,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_discover: MagicMock = Depends(mock_discover_fx),
    mock_setup_entry: MagicMock = Depends(mock_setup_entry_fx),
    mock_s20: MagicMock = Depends(mock_s20_fx),
) -> None:
    """Test importing configuration.yaml entry succeeds with provided or discovered MAC."""
    mock_s20.return_value._mac = mock_mac_bytes
    mock_discover.return_value = {"192.168.1.5": {"mac": b"\x11\x22\x33\x44\x55\x66"}}

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_IMPORT}, data=import_data
    )

    expect(result["type"]).to_equal(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("192.168.1.5")
    expect(result["data"][CONF_MAC]).to_equal(expected_mac)


@test.cases(
    test.case(
        "cannot_discover",
        {CONF_HOST: "192.168.1.5"},
        "cannot_discover",
        None,
        None,
    ),
    test.case(
        "cannot_connect",
        {CONF_HOST: "192.168.1.5", CONF_MAC: "ac:cf:23:12:34:56"},
        "cannot_connect",
        S20Exception("Connection failed"),
        b"dummy",
    ),
)
async def import_flow_errors(
    import_data: dict[str, Any],
    expected_reason: str,
    mock_exception: Exception | None,
    mock_mac_bytes: bytes | None,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_s20: MagicMock = Depends(mock_s20_fx),
    mock_discover: MagicMock = Depends(mock_discover_fx),
) -> None:
    """Test various abort errors in the import flow."""
    mock_discover.return_value = {}
    mock_s20.side_effect = mock_exception
    mock_s20.return_value._mac = mock_mac_bytes

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_IMPORT}, data=import_data
    )

    expect(result["type"]).to_equal(FlowResultType.ABORT)
    expect(result["reason"]).to_equal(expected_reason)


@test
async def discover_skips_existing_and_invalid_mac(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
    mock_discover: MagicMock = Depends(mock_discover_fx),
) -> None:
    """Test discovery ignores devices already configured and devices without MACs."""
    mock_config_entry.add_to_hass(hass)

    mock_discover.return_value = {
        "192.168.1.10": {"mac": b"\xaa\xbb\xcc\xdd\xee\xff"},
        "192.168.1.11": {},
        "192.168.1.12": {"mac": b"\x11\x22\x33\x44\x55\x66"},
    }

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "start_discovery"}
    )

    await hass.async_block_till_done()

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["type"]).to_equal(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("choose_switch")

    schema = result["data_schema"].schema
    dropdown_options = schema[vol.Required(CONF_SWITCH_LIST)].container

    expect("192.168.1.12" in dropdown_options).to_be(True)
    expect("192.168.1.10" not in dropdown_options).to_be(True)
    expect("192.168.1.11" not in dropdown_options).to_be(True)


@test
async def start_discovery_shows_progress(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test polling the flow while discovery is still in progress."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    async def delayed_executor_job(*args, **kwargs) -> dict[str, Any]:
        await asyncio.sleep(0.1)
        return {}

    with patch.object(hass, "async_add_executor_job", side_effect=delayed_executor_job):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"next_step_id": "start_discovery"}
        )
        expect(result["type"]).to_equal(FlowResultType.SHOW_PROGRESS)

        result = await hass.config_entries.flow.async_configure(result["flow_id"])

        expect(result["type"]).to_equal(FlowResultType.SHOW_PROGRESS)
        expect(result["progress_action"]).to_equal("start_discovery")

    await hass.async_block_till_done()


@test
async def discovery_flow_task_exception(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_discover: MagicMock = Depends(mock_discover_fx),
) -> None:
    """Test the discovery process when the background task raises an error."""
    mock_discover.side_effect = S20Exception("Network timeout")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "start_discovery"}
    )

    await hass.async_block_till_done()

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["type"]).to_equal(FlowResultType.MENU)
    expect(result["step_id"]).to_equal("discovery_failed")
