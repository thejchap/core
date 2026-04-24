"""Test Steam config flow."""

from __future__ import annotations

from unittest.mock import patch

import steam
from tryke import Depends, expect, fixture, test

from homeassistant.components.steam_online.const import CONF_ACCOUNTS, DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er

from . import (
    ACCOUNT_1,
    ACCOUNT_2,
    ACCOUNT_NAME_1,
    CONF_DATA,
    CONF_OPTIONS,
    CONF_OPTIONS_2,
    create_entry,
    patch_interface,
    patch_interface_private,
    patch_user_interface_null,
)

from tests.hass_fixtures import (
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def flow_user(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user initialized flow."""
    with (
        patch_interface(),
        patch(
            "homeassistant.components.steam_online.async_setup_entry",
            return_value=True,
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=CONF_DATA,
        )
        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["title"]).to_equal(ACCOUNT_NAME_1)
        expect(result["data"]).to_equal(CONF_DATA)
        expect(result["options"]).to_equal(CONF_OPTIONS)
        expect(result["result"].unique_id).to_equal(ACCOUNT_1)


@test
async def flow_user_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user initialized flow with unreachable server."""
    with patch_interface() as servicemock:
        servicemock.side_effect = steam.api.HTTPTimeoutError
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=CONF_DATA
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")
        expect(result["errors"]["base"]).to_equal("cannot_connect")


@test
async def flow_user_invalid_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user initialized flow with invalid authentication."""
    with patch_interface() as servicemock:
        servicemock.side_effect = steam.api.HTTPError("403")
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=CONF_DATA
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")
        expect(result["errors"]["base"]).to_equal("invalid_auth")


@test
async def flow_user_invalid_account(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user initialized flow with invalid account ID."""
    with patch_user_interface_null():
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=CONF_DATA
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")
        expect(result["errors"]["base"]).to_equal("invalid_account")


@test
async def flow_user_unknown(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user initialized flow with unknown error."""
    with patch_interface() as servicemock:
        servicemock.side_effect = Exception
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=CONF_DATA
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")
        expect(result["errors"]["base"]).to_equal("unknown")


@test
async def flow_user_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user initialized flow with duplicate account."""
    create_entry(hass)
    with patch_interface():
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=CONF_DATA
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def flow_reauth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reauth step."""
    entry = create_entry(hass)
    result = await entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    with patch_interface():
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={},
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")
        new_conf = CONF_DATA | {CONF_API_KEY: "1234567890"}
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=new_conf,
        )
        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("reauth_successful")
        expect(entry.data).to_equal(new_conf)


@test
async def options_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test updating options."""
    entry = create_entry(hass)
    with (
        patch_interface(),
        patch(
            "homeassistant.components.steam_online.config_flow.MAX_IDS_TO_REQUEST",
            return_value=2,
        ),
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        result = await hass.config_entries.options.async_init(entry.entry_id)
        await hass.async_block_till_done()

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("init")

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={CONF_ACCOUNTS: [ACCOUNT_1, ACCOUNT_2]},
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(CONF_OPTIONS_2)


@test
async def options_flow_deselect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test deselecting user."""
    entry = create_entry(hass)
    with (
        patch_interface(),
        patch(
            "homeassistant.components.steam_online.config_flow.MAX_IDS_TO_REQUEST",
            return_value=2,
        ),
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        result = await hass.config_entries.options.async_init(entry.entry_id)
        await hass.async_block_till_done()

    with (
        patch_interface(),
        patch(
            "homeassistant.components.steam_online.async_setup_entry",
            return_value=True,
        ),
    ):
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("init")

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={CONF_ACCOUNTS: []},
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal({CONF_ACCOUNTS: {}})
    expect(len(entity_registry.entities)).to_equal(0)


@test
async def options_flow_timeout(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test updating options timeout getting friends list."""
    entry = create_entry(hass)
    with patch_interface() as servicemock:
        servicemock.side_effect = steam.api.HTTPTimeoutError
        result = await hass.config_entries.options.async_init(entry.entry_id)

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("init")

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={CONF_ACCOUNTS: [ACCOUNT_1]},
        )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(CONF_OPTIONS)


@test
async def options_flow_unauthorized(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test updating options when user's friends list is not public."""
    entry = create_entry(hass)
    with patch_interface_private():
        result = await hass.config_entries.options.async_init(entry.entry_id)

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("init")

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={CONF_ACCOUNTS: [ACCOUNT_1]},
        )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(CONF_OPTIONS)
