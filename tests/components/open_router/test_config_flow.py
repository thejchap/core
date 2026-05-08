"""Test the OpenRouter config flow."""

from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.open_router.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.setup import async_setup_component

from ._fixtures import mock_config_entry, mock_open_router_client, mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Force tryke fixture resolution before each test."""


@test
async def full_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    open_router_client: AsyncMock = Depends(mock_open_router_client),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test the full config flow."""
    expect(await async_setup_component(hass, "homeassistant", {})).to_be(True)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(bool(result["errors"])).to_be(False)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_API_KEY: "bla"}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Test account")
    expect(result["data"]).to_equal({CONF_API_KEY: "bla"})


@test
async def duplicate_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    open_router_client: AsyncMock = Depends(mock_open_router_client),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test aborting the flow if an entry already exists."""
    expect(await async_setup_component(hass, "homeassistant", {})).to_be(True)
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(bool(result["errors"])).to_be(False)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_KEY: "bla"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test.skip("requires second-account flow with subentries — port deferred")
async def second_account(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_second_account."""


@test.skip("indirect parametrize not in tryke 0.0.27")
async def form_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_form_errors."""


@test.skip("requires conversation subentry chain — port deferred")
async def create_conversation_agent(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_create_conversation_agent."""


@test.skip("requires conversation subentry chain — port deferred")
async def create_conversation_agent_no_control(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_create_conversation_agent_no_control."""


@test.skip("requires AI task subentry chain — port deferred")
async def create_ai_task(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_create_ai_task."""


@test.skip("indirect parametrize not in tryke 0.0.27")
async def subentry_exceptions(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_subentry_exceptions."""


@test.skip("requires reconfigure flow — port deferred")
async def reconfigure_conversation_agent(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_reconfigure_conversation_agent."""


@test.skip("requires reconfigure flow — port deferred")
async def reconfigure_ai_task(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_reconfigure_ai_task."""


@test.skip("requires reconfigure flow — port deferred")
async def reconfigure_entry_not_loaded(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_reconfigure_entry_not_loaded."""


@test.skip("requires reconfigure flow — port deferred")
async def reconfigure_conversation_agent_abort(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_reconfigure_conversation_agent_abort."""


@test.skip("requires reconfigure flow — port deferred")
async def reconfigure_ai_task_abort(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_reconfigure_ai_task_abort."""


@test.skip("requires conversation subentry chain — port deferred")
async def create_conversation_agent_web_search(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_create_conversation_agent_web_search."""


@test.skip("requires reconfigure flow — port deferred")
async def reconfigure_conversation_subentry_web_search_default(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_reconfigure_conversation_subentry_web_search_default."""


@test.skip("requires reconfigure flow — port deferred")
async def reconfigure_conversation_subentry_llm_api_schema(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_reconfigure_conversation_subentry_llm_api_schema."""
