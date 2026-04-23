"""Test the OpenRouter config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock

from python_open_router import OpenRouterError
from tryke import Depends, expect, fixture, test

from homeassistant.components.open_router.const import (
    CONF_PROMPT,
    CONF_WEB_SEARCH,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_API_KEY, CONF_LLM_HASS_API, CONF_MODEL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

from . import get_subentry_id, setup_integration
from ._fixtures import (
    make_mock_config_entry,
    mock_config_entry as mock_config_entry_fx,
    mock_open_router_client as mock_open_router_client_fx,
    mock_openai_client as mock_openai_client_fx,
    mock_setup_entry as mock_setup_entry_fx,
    mock_zeroconf,
    setup_ha,
)


@fixture
def _trigger_executor(
    _net: None = Depends(mock_network),
    _zeroconf: object = Depends(mock_zeroconf),
    _setup_ha: None = Depends(setup_ha),
) -> None:
    """Wire autouse fixtures for every test."""


@test
async def full_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_open_router_client: AsyncMock = Depends(mock_open_router_client_fx),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test the full config flow."""
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
async def second_account(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_open_router_client: AsyncMock = Depends(mock_open_router_client_fx),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test that a second account with a different API key can be added."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_KEY: "different_key"},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Test account")
    expect(result["data"]).to_equal({CONF_API_KEY: "different_key"})


@test.cases(
    test.case("connect_error", OpenRouterError("exception"), "cannot_connect"),
    test.case("unknown_error", Exception, "unknown"),
)
async def form_errors(
    exception: type[Exception] | Exception,
    error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_open_router_client: AsyncMock = Depends(mock_open_router_client_fx),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test we handle errors from the OpenRouter API."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    mock_open_router_client.get_key_data.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_KEY: "bla"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error})

    mock_open_router_client.get_key_data.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_KEY: "bla"},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def duplicate_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_open_router_client: AsyncMock = Depends(mock_open_router_client_fx),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test aborting the flow if an entry already exists."""
    mock_config_entry.add_to_hass(hass)

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


@test
async def create_conversation_agent(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_open_router_client: AsyncMock = Depends(mock_open_router_client_fx),
    mock_openai_client: AsyncMock = Depends(mock_openai_client_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test creating a conversation agent."""
    await setup_integration(hass, mock_config_entry)

    result = await hass.config_entries.subentries.async_init(
        (mock_config_entry.entry_id, "conversation"),
        context={"source": SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(bool(result["errors"])).to_be(False)
    expect(result["step_id"]).to_equal("init")

    expect(result["data_schema"].schema["model"].config["options"]).to_equal(
        [
            {"value": "openai/gpt-3.5-turbo", "label": "OpenAI: GPT-3.5 Turbo"},
            {"value": "openai/gpt-4", "label": "OpenAI: GPT-4"},
        ]
    )

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            CONF_MODEL: "openai/gpt-3.5-turbo",
            CONF_PROMPT: "you are an assistant",
            CONF_LLM_HASS_API: ["assist"],
            CONF_WEB_SEARCH: False,
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(
        {
            CONF_MODEL: "openai/gpt-3.5-turbo",
            CONF_PROMPT: "you are an assistant",
            CONF_LLM_HASS_API: ["assist"],
            CONF_WEB_SEARCH: False,
        }
    )


@test
async def create_conversation_agent_no_control(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_open_router_client: AsyncMock = Depends(mock_open_router_client_fx),
    mock_openai_client: AsyncMock = Depends(mock_openai_client_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test creating a conversation agent without control over the LLM API."""
    await setup_integration(hass, mock_config_entry)

    result = await hass.config_entries.subentries.async_init(
        (mock_config_entry.entry_id, "conversation"),
        context={"source": SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(bool(result["errors"])).to_be(False)
    expect(result["step_id"]).to_equal("init")

    expect(result["data_schema"].schema["model"].config["options"]).to_equal(
        [
            {"value": "openai/gpt-3.5-turbo", "label": "OpenAI: GPT-3.5 Turbo"},
            {"value": "openai/gpt-4", "label": "OpenAI: GPT-4"},
        ]
    )

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            CONF_MODEL: "openai/gpt-3.5-turbo",
            CONF_PROMPT: "you are an assistant",
            CONF_LLM_HASS_API: [],
            CONF_WEB_SEARCH: False,
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(
        {
            CONF_MODEL: "openai/gpt-3.5-turbo",
            CONF_PROMPT: "you are an assistant",
            CONF_WEB_SEARCH: False,
        }
    )


@test
async def create_ai_task(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_open_router_client: AsyncMock = Depends(mock_open_router_client_fx),
    mock_openai_client: AsyncMock = Depends(mock_openai_client_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test creating an AI Task."""
    await setup_integration(hass, mock_config_entry)

    result = await hass.config_entries.subentries.async_init(
        (mock_config_entry.entry_id, "ai_task_data"),
        context={"source": SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(bool(result["errors"])).to_be(False)
    expect(result["step_id"]).to_equal("init")

    expect(result["data_schema"].schema["model"].config["options"]).to_equal(
        [{"value": "openai/gpt-4", "label": "OpenAI: GPT-4"}]
    )

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {CONF_MODEL: "openai/gpt-4"},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal({CONF_MODEL: "openai/gpt-4"})


@test.cases(
    test.case(
        "conversation_connect_error",
        "conversation",
        OpenRouterError("exception"),
        "cannot_connect",
    ),
    test.case("conversation_unknown_error", "conversation", Exception, "unknown"),
    test.case(
        "ai_task_connect_error",
        "ai_task_data",
        OpenRouterError("exception"),
        "cannot_connect",
    ),
    test.case("ai_task_unknown_error", "ai_task_data", Exception, "unknown"),
)
async def subentry_exceptions(
    subentry_type: str,
    exception: type[Exception] | Exception,
    reason: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_open_router_client: AsyncMock = Depends(mock_open_router_client_fx),
    mock_openai_client: AsyncMock = Depends(mock_openai_client_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test subentry flow exceptions."""
    await setup_integration(hass, mock_config_entry)

    mock_open_router_client.get_models.side_effect = exception

    result = await hass.config_entries.subentries.async_init(
        (mock_config_entry.entry_id, subentry_type),
        context={"source": SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal(reason)


@test
async def reconfigure_conversation_agent(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_open_router_client: AsyncMock = Depends(mock_open_router_client_fx),
    mock_openai_client: AsyncMock = Depends(mock_openai_client_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test reconfiguring a conversation agent."""
    await setup_integration(hass, mock_config_entry)

    subentry_id = get_subentry_id(mock_config_entry, "conversation")

    result = await mock_config_entry.start_subentry_reconfigure_flow(hass, subentry_id)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            CONF_MODEL: "openai/gpt-4",
            CONF_PROMPT: "updated prompt",
            CONF_LLM_HASS_API: ["assist"],
            CONF_WEB_SEARCH: True,
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")

    subentry = mock_config_entry.subentries[subentry_id]
    expect(subentry.data[CONF_MODEL]).to_equal("openai/gpt-4")
    expect(subentry.data[CONF_PROMPT]).to_equal("updated prompt")
    expect(subentry.data[CONF_LLM_HASS_API]).to_equal(["assist"])
    expect(subentry.data[CONF_WEB_SEARCH]).to_be(True)


@test
async def reconfigure_ai_task(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_open_router_client: AsyncMock = Depends(mock_open_router_client_fx),
    mock_openai_client: AsyncMock = Depends(mock_openai_client_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test reconfiguring an AI task."""
    await setup_integration(hass, mock_config_entry)

    subentry_id = get_subentry_id(mock_config_entry, "ai_task_data")

    result = await mock_config_entry.start_subentry_reconfigure_flow(hass, subentry_id)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {CONF_MODEL: "openai/gpt-4"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")


@test.cases(
    test.case("conversation", "conversation"),
    test.case("ai_task_data", "ai_task_data"),
)
async def reconfigure_entry_not_loaded(
    subentry_type: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_open_router_client: AsyncMock = Depends(mock_open_router_client_fx),
    mock_openai_client: AsyncMock = Depends(mock_openai_client_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test attempting subentry flow when the entry is not loaded."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.subentries.async_init(
        (mock_config_entry.entry_id, subentry_type),
        context={"source": SOURCE_USER},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("entry_not_loaded")


@test.cases(
    test.case("connect_error", OpenRouterError("exception"), "cannot_connect"),
    test.case("unknown_error", Exception, "unknown"),
)
async def reconfigure_conversation_agent_abort(
    exception: type[Exception] | Exception,
    reason: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_open_router_client: AsyncMock = Depends(mock_open_router_client_fx),
    mock_openai_client: AsyncMock = Depends(mock_openai_client_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test reconfiguring a conversation agent with error and recovery."""
    await setup_integration(hass, mock_config_entry)

    subentry_id = get_subentry_id(mock_config_entry, "conversation")

    mock_open_router_client.get_models.side_effect = exception

    result = await mock_config_entry.start_subentry_reconfigure_flow(hass, subentry_id)
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal(reason)


@test.cases(
    test.case("connect_error", OpenRouterError("exception"), "cannot_connect"),
    test.case("unknown_error", Exception, "unknown"),
)
async def reconfigure_ai_task_abort(
    exception: type[Exception] | Exception,
    reason: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_open_router_client: AsyncMock = Depends(mock_open_router_client_fx),
    mock_openai_client: AsyncMock = Depends(mock_openai_client_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test reconfiguring an AI task with error and recovery."""
    await setup_integration(hass, mock_config_entry)

    subentry_id = get_subentry_id(mock_config_entry, "ai_task_data")

    mock_open_router_client.get_models.side_effect = exception

    result = await mock_config_entry.start_subentry_reconfigure_flow(hass, subentry_id)
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal(reason)


@test.cases(
    test.case("web_search_true", True, True),
    test.case("web_search_false", False, False),
)
async def create_conversation_agent_web_search(
    web_search: bool,
    expected_web_search: bool,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_open_router_client: AsyncMock = Depends(mock_open_router_client_fx),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test creating a conversation agent with web search enabled/disabled."""
    mock_config_entry = make_mock_config_entry(web_search=web_search)
    await setup_integration(hass, mock_config_entry)

    result = await hass.config_entries.subentries.async_init(
        (mock_config_entry.entry_id, "conversation"),
        context={"source": SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    schema = result["data_schema"].schema
    key = next(k for k in schema if k == CONF_WEB_SEARCH)
    expect(key.default()).to_be(False)

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            CONF_MODEL: "openai/gpt-3.5-turbo",
            CONF_PROMPT: "you are an assistant",
            CONF_LLM_HASS_API: ["assist"],
            CONF_WEB_SEARCH: expected_web_search,
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"][CONF_WEB_SEARCH]).to_be(expected_web_search)


@test.cases(
    test.case("current_true", True, True),
    test.case("current_false", False, False),
)
async def reconfigure_conversation_subentry_web_search_default(
    current_web_search: bool,
    expected_default: bool,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_open_router_client: AsyncMock = Depends(mock_open_router_client_fx),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test web_search field default reflects existing value when reconfiguring."""
    await setup_integration(hass, mock_config_entry)

    subentry = next(iter(mock_config_entry.subentries.values()))
    hass.config_entries.async_update_subentry(
        mock_config_entry,
        subentry,
        data={**subentry.data, CONF_WEB_SEARCH: current_web_search},
    )
    await hass.async_block_till_done()

    result = await mock_config_entry.start_subentry_reconfigure_flow(
        hass, subentry.subentry_id
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    schema = result["data_schema"].schema
    key = next(k for k in schema if k == CONF_WEB_SEARCH)
    expect(key.default()).to_be(expected_default)


@test.cases(
    test.case("valid_assist", ["assist"], ["assist"], ["assist"]),
    test.case("invalid_only", ["non-existent"], [], ["assist"]),
    test.case(
        "valid_and_invalid", ["assist", "non-existent"], ["assist"], ["assist"]
    ),
)
async def reconfigure_conversation_subentry_llm_api_schema(
    current_llm_apis: list[str],
    suggested_llm_apis: list[str],
    expected_options: list[str],
    hass: HomeAssistant = Depends(hass_fixture),
    mock_open_router_client: AsyncMock = Depends(mock_open_router_client_fx),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test llm_hass_api field values when reconfiguring a conversation subentry."""
    await setup_integration(hass, mock_config_entry)

    subentry = next(iter(mock_config_entry.subentries.values()))
    hass.config_entries.async_update_subentry(
        mock_config_entry,
        subentry,
        data={**subentry.data, CONF_LLM_HASS_API: current_llm_apis},
    )
    await hass.async_block_till_done()

    result = await mock_config_entry.start_subentry_reconfigure_flow(
        hass, subentry.subentry_id
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    schema = result["data_schema"].schema
    key = next(k for k in schema if k == CONF_LLM_HASS_API)

    expect(key.default()).to_equal(suggested_llm_apis)

    field_schema = schema[key]
    expect(bool(field_schema.config)).to_be(True)
    expect(
        [opt["value"] for opt in field_schema.config.get("options")]
    ).to_equal(expected_options)
