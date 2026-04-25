"""Test the GitHub config flow."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

from aiogithubapi import GitHubException
from tryke import Depends, expect, fixture, test

from homeassistant.components.github.const import (
    CONF_REPOSITORIES,
    DEFAULT_REPOSITORIES,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_ACCESS_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType, UnknownFlow

from ._fixtures import (
    device_activation_event,
    github_client,
    github_device_client,
    mock_config_entry,
    mock_setup_entry,
)
from .const import MOCK_ACCESS_TOKEN

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Apply autouse-equivalent fixtures via this trigger."""


@test
async def full_user_flow_implementation(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: None = Depends(mock_setup_entry),
    _device_client: AsyncMock = Depends(github_device_client),
    _client: AsyncMock = Depends(github_client),
    activation_event: asyncio.Event = Depends(device_activation_event),
) -> None:
    """Test the full manual user flow from start to finish."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["step_id"]).to_equal("device")
    expect(result["type"]).to_be(FlowResultType.SHOW_PROGRESS)

    activation_event.set()
    await hass.async_block_till_done()

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["step_id"]).to_equal("repositories")
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(bool(result["errors"])).to_be(False)

    schema = result["data_schema"]
    repositories = schema.schema[CONF_REPOSITORIES].options
    expect(len(repositories)).to_equal(4)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_REPOSITORIES: DEFAULT_REPOSITORIES}
    )

    expect(result["title"]).to_equal("")
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal({CONF_ACCESS_TOKEN: MOCK_ACCESS_TOKEN})
    expect(result["options"]).to_equal({CONF_REPOSITORIES: DEFAULT_REPOSITORIES})


@test
async def flow_with_registration_failure(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_client: AsyncMock = Depends(github_device_client),
) -> None:
    """Test flow with registration failure of the device."""
    device_client.register.side_effect = GitHubException("Registration failed")
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("could_not_register")


@test
async def flow_with_activation_failure(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_client: AsyncMock = Depends(github_device_client),
    activation_event: asyncio.Event = Depends(device_activation_event),
) -> None:
    """Test flow with activation failure of the device."""

    async def mock_api_device_activation(device_code) -> None:
        await activation_event.wait()
        raise GitHubException("Activation failed")

    device_client.activation = mock_api_device_activation

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["step_id"]).to_equal("device")
    expect(result["type"]).to_be(FlowResultType.SHOW_PROGRESS)

    activation_event.set()
    await hass.async_block_till_done()

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("could_not_register")


@test
async def flow_with_remove_while_activating(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _device_client: AsyncMock = Depends(github_device_client),
) -> None:
    """Test flow with user canceling while activating."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["step_id"]).to_equal("device")
    expect(result["type"]).to_be(FlowResultType.SHOW_PROGRESS)

    expect(bool(hass.config_entries.flow.async_get(result["flow_id"]))).to_be(True)

    hass.config_entries.flow._async_remove_flow_progress(result["flow_id"])
    await hass.async_block_till_done()

    raised = False
    try:
        hass.config_entries.flow.async_get(result["flow_id"])
    except UnknownFlow:
        raised = True
    expect(raised).to_be(True)


@test
async def already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test we abort if already configured."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def no_repositories(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: None = Depends(mock_setup_entry),
    _device_client: AsyncMock = Depends(github_device_client),
    client: AsyncMock = Depends(github_client),
    activation_event: asyncio.Event = Depends(device_activation_event),
) -> None:
    """Test no repositories returns reduced default options."""
    client.user.repos.side_effect = [MagicMock(is_last_page=True, data=[])]
    client.user.starred.side_effect = [MagicMock(is_last_page=True, data=[])]

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["step_id"]).to_equal("device")
    expect(result["type"]).to_be(FlowResultType.SHOW_PROGRESS)

    activation_event.set()
    await hass.async_block_till_done()

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["step_id"]).to_equal("repositories")
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(bool(result["errors"])).to_be(False)

    schema = result["data_schema"]
    repositories = schema.schema[CONF_REPOSITORIES].options
    expect(len(repositories)).to_equal(2)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_REPOSITORIES: DEFAULT_REPOSITORIES}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def exception_during_repository_fetch(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: None = Depends(mock_setup_entry),
    _device_client: AsyncMock = Depends(github_device_client),
    client: AsyncMock = Depends(github_client),
    activation_event: asyncio.Event = Depends(device_activation_event),
) -> None:
    """Test exception during repository fetch falls back to defaults."""
    client.user.repos.side_effect = GitHubException()

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["step_id"]).to_equal("device")
    expect(result["type"]).to_be(FlowResultType.SHOW_PROGRESS)

    activation_event.set()
    await hass.async_block_till_done()

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["step_id"]).to_equal("repositories")
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(bool(result["errors"])).to_be(False)

    schema = result["data_schema"]
    repositories = schema.schema[CONF_REPOSITORIES].options
    expect(len(repositories)).to_equal(2)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_REPOSITORIES: DEFAULT_REPOSITORIES}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def options_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _setup_entry: None = Depends(mock_setup_entry),
) -> None:
    """Test options flow."""
    config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        config_entry,
        options={
            CONF_REPOSITORIES: ["homeassistant/core", "homeassistant/architecture"]
        },
    )

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(config_entry.entry_id)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_REPOSITORIES: ["homeassistant/core"]},
    )

    expect("homeassistant/architecture" not in result["data"][CONF_REPOSITORIES]).to_be(
        True
    )
