"""Test the Azure DevOps config flow."""

from unittest.mock import AsyncMock

import aiohttp
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.azure_devops.const import CONF_ORG, CONF_PROJECT, DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import FIXTURE_REAUTH_INPUT, FIXTURE_USER_INPUT
from ._fixtures import mock_config_entry, mock_devops_client, mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def show_user_form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that the setup form is served."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")


@test
async def authorization_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    devops_client: AsyncMock = Depends(mock_devops_client),
) -> None:
    """Test we show user form on Azure DevOps authorization error."""
    devops_client.authorize.return_value = False
    devops_client.authorized = False

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        FIXTURE_USER_INPUT,
    )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["step_id"]).to_equal("user")
    expect(result2["errors"]).to_equal({"base": "invalid_auth"})


@test
async def reauth_authorization_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    devops_client: AsyncMock = Depends(mock_devops_client),
) -> None:
    """Test we show user form on Azure DevOps authorization error."""
    config_entry.add_to_hass(hass)
    devops_client.authorize.return_value = False
    devops_client.authorized = False

    result = await config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        FIXTURE_REAUTH_INPUT,
    )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["step_id"]).to_equal("reauth_confirm")
    expect(result2["errors"]).to_equal({"base": "invalid_auth"})


@test
async def connection_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    devops_client: AsyncMock = Depends(mock_devops_client),
) -> None:
    """Test we show user form on Azure DevOps connection error."""
    devops_client.authorize.side_effect = aiohttp.ClientError
    devops_client.authorized = False

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        FIXTURE_USER_INPUT,
    )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["step_id"]).to_equal("user")
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def reauth_connection_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    devops_client: AsyncMock = Depends(mock_devops_client),
) -> None:
    """Test we show user form on Azure DevOps connection error."""
    config_entry.add_to_hass(hass)
    devops_client.authorize.side_effect = aiohttp.ClientError
    devops_client.authorized = False

    result = await config_entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        FIXTURE_REAUTH_INPUT,
    )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["step_id"]).to_equal("reauth_confirm")
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def project_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    devops_client: AsyncMock = Depends(mock_devops_client),
) -> None:
    """Test we show user form on Azure DevOps connection error."""
    devops_client.authorize.return_value = True
    devops_client.authorized = True
    devops_client.get_project.return_value = None

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        FIXTURE_USER_INPUT,
    )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["step_id"]).to_equal("user")
    expect(result2["errors"]).to_equal({"base": "project_error"})


@test
async def reauth_project_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    devops_client: AsyncMock = Depends(mock_devops_client),
) -> None:
    """Test we show user form on Azure DevOps project error."""
    devops_client.authorize.return_value = True
    devops_client.authorized = True
    devops_client.get_project.return_value = None

    config_entry.add_to_hass(hass)

    result = await config_entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        FIXTURE_REAUTH_INPUT,
    )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["step_id"]).to_equal("reauth_confirm")
    expect(result2["errors"]).to_equal({"base": "project_error"})


@test
async def reauth_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    devops_client: AsyncMock = Depends(mock_devops_client),
) -> None:
    """Test reauth works."""
    devops_client.authorize.return_value = False
    devops_client.authorized = False

    config_entry.add_to_hass(hass)

    result = await config_entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    devops_client.authorize.return_value = True
    devops_client.authorized = True

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        FIXTURE_REAUTH_INPUT,
    )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("reauth_successful")


@test
async def full_flow_implementation(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    _devops_client: AsyncMock = Depends(mock_devops_client),
) -> None:
    """Test registering an integration and finishing flow works."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        FIXTURE_USER_INPUT,
    )
    await hass.async_block_till_done()
    expect(len(setup_entry.mock_calls)).to_equal(1)

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal(
        f"{FIXTURE_USER_INPUT[CONF_ORG]}/{FIXTURE_USER_INPUT[CONF_PROJECT]}"
    )
    expect(result2["data"][CONF_ORG]).to_equal(FIXTURE_USER_INPUT[CONF_ORG])
    expect(result2["data"][CONF_PROJECT]).to_equal(FIXTURE_USER_INPUT[CONF_PROJECT])
