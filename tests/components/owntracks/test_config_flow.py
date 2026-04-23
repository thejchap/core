"""Tests for OwnTracks config flow."""

from __future__ import annotations

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.owntracks import config_flow
from homeassistant.components.owntracks.config_flow import CONF_CLOUDHOOK, CONF_SECRET
from homeassistant.components.owntracks.const import DOMAIN
from homeassistant.const import CONF_WEBHOOK_ID
from homeassistant.core import HomeAssistant
from homeassistant.core_config import async_process_ha_core_config
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.setup import async_setup_component

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

from ._fixtures import (
    SECRET,
    WEBHOOK_ID,
    not_supports_encryption as not_supports_encryption_fx,
    secret as secret_fx,
    webhook_id as webhook_id_fx,
)

CONF_WEBHOOK_URL = "webhook_url"

BASE_URL = "http://example.com"
CLOUDHOOK = False
WEBHOOK_URL = f"{BASE_URL}/api/webhook/webhook_id"


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Wire mock_network for every test."""


async def _init_config_flow(hass: HomeAssistant) -> config_flow.OwnTracksFlow:
    """Init a configuration flow."""
    await async_process_ha_core_config(hass, {"external_url": BASE_URL})
    flow = config_flow.OwnTracksFlow()
    flow.hass = hass
    return flow


@test
async def user(
    hass: HomeAssistant = Depends(hass_fixture),
    _webhook: None = Depends(webhook_id_fx),
    _secret: None = Depends(secret_fx),
) -> None:
    """Test user step."""
    flow = await _init_config_flow(hass)

    result = await flow.async_step_user()
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await flow.async_step_user({})
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("OwnTracks")
    expect(result["data"][CONF_WEBHOOK_ID]).to_equal(WEBHOOK_ID)
    expect(result["data"][CONF_SECRET]).to_equal(SECRET)
    expect(result["data"][CONF_CLOUDHOOK]).to_equal(CLOUDHOOK)
    expect(result["description_placeholders"][CONF_WEBHOOK_URL]).to_equal(WEBHOOK_URL)


@test
async def import_setup(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test that we don't automatically create a config entry."""
    await async_process_ha_core_config(hass, {"external_url": "http://example.com"})

    expect(hass.config_entries.async_entries(DOMAIN)).to_equal([])
    expect(await async_setup_component(hass, DOMAIN, {"owntracks": {}})).to_be(True)
    await hass.async_block_till_done()
    expect(hass.config_entries.async_entries(DOMAIN)).to_equal([])


@test
async def abort_if_already_setup(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test that we can't add more than one instance."""
    MockConfigEntry(domain=DOMAIN, data={}).add_to_hass(hass)
    expect(bool(hass.config_entries.async_entries(DOMAIN))).to_be(True)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("single_instance_allowed")


@test
async def user_not_supports_encryption(
    hass: HomeAssistant = Depends(hass_fixture),
    _not_supports: None = Depends(not_supports_encryption_fx),
) -> None:
    """Test user step."""
    flow = await _init_config_flow(hass)

    result = await flow.async_step_user({})
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["description_placeholders"]["secret"]).to_equal(
        "Encryption is not supported because nacl is not installed."
    )


@test
async def unload(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test unloading a config flow."""
    await async_process_ha_core_config(hass, {"external_url": "http://example.com"})

    with patch(
        "homeassistant.config_entries.ConfigEntries.async_forward_entry_setups"
    ) as mock_forward:
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}, data={}
        )

    expect(len(mock_forward.mock_calls)).to_equal(1)
    entry = result["result"]

    mock_forward.assert_called_once_with(entry, ["device_tracker"])
    expect(entry.data["webhook_id"] in hass.data["webhook"]).to_be(True)

    with patch(
        "homeassistant.config_entries.ConfigEntries.async_unload_platforms",
        return_value=True,
    ) as mock_unload:
        expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)

    expect(len(mock_unload.mock_calls)).to_equal(1)
    mock_forward.assert_called_once_with(entry, ["device_tracker"])
    expect(entry.data["webhook_id"] in hass.data["webhook"]).to_be(False)


@test
async def with_cloud_sub(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test creating a config flow while subscribed."""
    expect(await async_setup_component(hass, "cloud", {})).to_be(True)

    with (
        patch(
            "homeassistant.components.cloud.async_active_subscription",
            return_value=True,
        ),
        patch("homeassistant.components.cloud.async_is_logged_in", return_value=True),
        patch("homeassistant.components.cloud.async_is_connected", return_value=True),
        patch(
            "hass_nabucasa.cloudhooks.Cloudhooks.async_create",
            return_value={"cloudhook_url": "https://hooks.nabu.casa/ABCD"},
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}, data={}
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    entry = result["result"]
    expect(entry.data["cloudhook"]).to_be(True)
    expect(result["description_placeholders"]["webhook_url"]).to_equal(
        "https://hooks.nabu.casa/ABCD"
    )


@test
async def with_cloud_sub_not_connected(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test creating a config flow while subscribed."""
    expect(await async_setup_component(hass, "cloud", {})).to_be(True)

    with (
        patch(
            "homeassistant.components.cloud.async_active_subscription",
            return_value=True,
        ),
        patch("homeassistant.components.cloud.async_is_logged_in", return_value=True),
        patch("homeassistant.components.cloud.async_is_connected", return_value=False),
        patch(
            "hass_nabucasa.cloudhooks.Cloudhooks.async_create",
            return_value={"cloudhook_url": "https://hooks.nabu.casa/ABCD"},
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}, data={}
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("cloud_not_connected")
