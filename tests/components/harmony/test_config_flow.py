"""Test the Logitech Harmony Hub config flow."""

from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.harmony.config_flow import CannotConnect
from homeassistant.components.harmony.const import DOMAIN, PREVIOUS_ACTIVE_ACTIVITY
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.ssdp import SsdpServiceInfo

from ._fixtures import mock_hc, mock_write_config

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


def _get_mock_harmonyapi(connect=None, close=None):
    harmonyapi_mock = MagicMock()
    type(harmonyapi_mock).connect = AsyncMock(return_value=connect)
    type(harmonyapi_mock).close = AsyncMock(return_value=close)
    return harmonyapi_mock


@test
async def user_form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we get the user form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    harmonyapi = _get_mock_harmonyapi(connect=True)
    with (
        patch(
            "homeassistant.components.harmony.util.HarmonyAPI",
            return_value=harmonyapi,
        ),
        patch(
            "homeassistant.components.harmony.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": "1.2.3.4", "name": "friend"},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("friend")
    expect(result2["data"]).to_equal({"host": "1.2.3.4", "name": "friend"})
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_ssdp(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we get the form with ssdp source."""
    with patch(
        "homeassistant.components.harmony.config_flow.HubConnector.get_remote_id",
        return_value=1234,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_SSDP},
            data=SsdpServiceInfo(
                ssdp_usn="mock_usn",
                ssdp_st="mock_st",
                ssdp_location="http://192.168.1.12:8088/description",
                upnp={
                    "friendlyName": "Harmony Hub",
                },
            ),
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("link")
    expect(result["errors"]).to_equal({})
    expect(result["description_placeholders"]).to_equal(
        {
            "host": "Harmony Hub",
            "name": "192.168.1.12",
        }
    )
    progress = hass.config_entries.flow.async_progress()
    expect(len(progress)).to_equal(1)
    expect(progress[0]["flow_id"]).to_equal(result["flow_id"])
    expect(progress[0]["context"]["confirm_only"]).to_be(True)

    harmonyapi = _get_mock_harmonyapi(connect=True)

    with (
        patch(
            "homeassistant.components.harmony.util.HarmonyAPI",
            return_value=harmonyapi,
        ),
        patch(
            "homeassistant.components.harmony.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("Harmony Hub")
    expect(result2["data"]).to_equal({"host": "192.168.1.12", "name": "Harmony Hub"})
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_ssdp_fails_to_get_remote_id(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we abort if we cannot get the remote id."""
    with patch(
        "homeassistant.components.harmony.config_flow.HubConnector.get_remote_id",
        side_effect=aiohttp.ClientError,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_SSDP},
            data=SsdpServiceInfo(
                ssdp_usn="mock_usn",
                ssdp_st="mock_st",
                ssdp_location="http://192.168.1.12:8088/description",
                upnp={
                    "friendlyName": "Harmony Hub",
                },
            ),
        )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("cannot_connect")


@test
async def form_ssdp_aborts_before_checking_remoteid_if_host_known(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we abort without connecting if the host is already known."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={"host": "2.2.2.2", "name": "any"},
    )
    config_entry.add_to_hass(hass)

    config_entry_without_host = MockConfigEntry(
        domain=DOMAIN,
        data={"name": "other"},
    )
    config_entry_without_host.add_to_hass(hass)

    harmonyapi = _get_mock_harmonyapi(connect=True)

    with patch(
        "homeassistant.components.harmony.util.HarmonyAPI",
        return_value=harmonyapi,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_SSDP},
            data=SsdpServiceInfo(
                ssdp_usn="mock_usn",
                ssdp_st="mock_st",
                ssdp_location="http://2.2.2.2:8088/description",
                upnp={
                    "friendlyName": "Harmony Hub",
                },
            ),
        )
    expect(result["type"]).to_be(FlowResultType.ABORT)


@test
async def form_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.harmony.util.HarmonyAPI",
        side_effect=CannotConnect,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "1.2.3.4",
                "name": "friend",
                "activity": "Watch TV",
                "delay_secs": 0.2,
            },
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def options_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _hc: None = Depends(mock_hc),
    _write_config: MagicMock = Depends(mock_write_config),
) -> None:
    """Test config flow options."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="abcde12345",
        data={CONF_HOST: "1.2.3.4", CONF_NAME: "Guest Room"},
        options={"activity": "Watch TV", "delay_secs": 0.5},
    )

    config_entry.add_to_hass(hass)
    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)
    await hass.async_block_till_done()
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    await hass.async_block_till_done()
    expect(await hass.config_entries.async_unload(config_entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"activity": PREVIOUS_ACTIVE_ACTIVITY, "delay_secs": 0.4},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(config_entry.options).to_equal(
        {
            "activity": PREVIOUS_ACTIVE_ACTIVITY,
            "delay_secs": 0.4,
        }
    )
