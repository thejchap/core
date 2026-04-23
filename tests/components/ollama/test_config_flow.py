"""Test the Ollama config flow."""

from __future__ import annotations

import asyncio
from unittest.mock import ANY, AsyncMock, patch

from httpx import ConnectError
from ollama import ResponseError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components import ollama
from homeassistant.components.ollama.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_API_KEY, CONF_LLM_HASS_API, CONF_NAME, CONF_URL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.components.ollama._fixtures import (
    mock_config_entry,
    mock_config_entry_with_assist_invalid_api,
    mock_init_component,
    setup_ha,
)
from tests.hass_fixtures import hass as hass_fixture, mock_network

TEST_MODEL = "test_model:latest"


@fixture
def _trigger_executor(
    _net: None = Depends(mock_network),
    _setup: None = Depends(setup_ha),
) -> None:
    """Wire mock_network + setup_ha (autouse) for every test."""


@test
async def form(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test flow when configuring URL only."""
    hass.config.components.add(DOMAIN)
    MockConfigEntry(
        domain=DOMAIN,
        state=config_entries.ConfigEntryState.LOADED,
    ).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    with (
        patch(
            "homeassistant.components.ollama.config_flow.ollama.AsyncClient.list",
            return_value={"models": [{"model": TEST_MODEL}]},
        ),
        patch(
            "homeassistant.components.ollama.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {ollama.CONF_URL: "http://localhost:11434"}
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["data"]).to_equal({ollama.CONF_URL: "http://localhost:11434"})
    expect(len(result2.get("subentries", []))).to_equal(0)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
    expect(CONF_API_KEY not in result2["data"]).to_equal(True)


@test
async def duplicate_entry(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we abort on duplicate config entry."""
    MockConfigEntry(
        domain=DOMAIN,
        data={
            ollama.CONF_URL: "http://localhost:11434",
            ollama.CONF_MODEL: "test_model",
        },
    ).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(bool(result["errors"])).to_equal(False)

    with patch(
        "homeassistant.components.ollama.config_flow.ollama.AsyncClient.list",
        return_value={"models": [{"model": "test_model"}]},
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                ollama.CONF_URL: "http://localhost:11434",
            },
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def subentry_options(
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    _init: None = Depends(mock_init_component),
) -> None:
    """Test the subentry options form."""
    subentry = next(iter(entry.subentries.values()))

    with patch(
        "ollama.AsyncClient.list",
        return_value={"models": [{"model": TEST_MODEL}]},
    ):
        options_flow = await entry.start_subentry_reconfigure_flow(
            hass, subentry.subentry_id
        )

        expect(options_flow["type"]).to_be(FlowResultType.FORM)
        expect(options_flow["step_id"]).to_equal("set_options")

        options = await hass.config_entries.subentries.async_configure(
            options_flow["flow_id"],
            {
                ollama.CONF_MODEL: TEST_MODEL,
                ollama.CONF_PROMPT: "test prompt",
                ollama.CONF_MAX_HISTORY: 100,
                ollama.CONF_NUM_CTX: 32768,
                ollama.CONF_THINK: True,
            },
        )
    await hass.async_block_till_done()

    expect(options["type"]).to_be(FlowResultType.ABORT)
    expect(options["reason"]).to_equal("reconfigure_successful")
    expect(subentry.data).to_equal(
        {
            ollama.CONF_MODEL: TEST_MODEL,
            ollama.CONF_PROMPT: "test prompt",
            ollama.CONF_MAX_HISTORY: 100.0,
            ollama.CONF_NUM_CTX: 32768.0,
            ollama.CONF_THINK: True,
        }
    )


@test
async def creating_new_conversation_subentry(
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    _init: None = Depends(mock_init_component),
) -> None:
    """Test creating a new conversation subentry includes name field."""
    with patch(
        "ollama.AsyncClient.list",
        return_value={"models": [{"model": TEST_MODEL}]},
    ):
        new_flow = await hass.config_entries.subentries.async_init(
            (entry.entry_id, "conversation"),
            context={"source": SOURCE_USER},
        )

        expect(new_flow["type"]).to_be(FlowResultType.FORM)
        expect(new_flow["step_id"]).to_equal("set_options")

        result = await hass.config_entries.subentries.async_configure(
            new_flow["flow_id"],
            {
                ollama.CONF_MODEL: TEST_MODEL,
                CONF_NAME: "New Test Conversation",
                ollama.CONF_PROMPT: "new test prompt",
                ollama.CONF_MAX_HISTORY: 50,
                ollama.CONF_NUM_CTX: 16384,
                ollama.CONF_THINK: False,
            },
        )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("New Test Conversation")
    expect(result["data"]).to_equal(
        {
            ollama.CONF_MODEL: TEST_MODEL,
            ollama.CONF_PROMPT: "new test prompt",
            ollama.CONF_MAX_HISTORY: 50.0,
            ollama.CONF_NUM_CTX: 16384.0,
            ollama.CONF_THINK: False,
        }
    )


@test
async def creating_conversation_subentry_not_loaded(
    hass: HomeAssistant = Depends(hass_fixture),
    _init: None = Depends(mock_init_component),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test creating a conversation subentry when entry is not loaded."""
    await hass.config_entries.async_unload(entry.entry_id)
    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, "conversation"),
        context={"source": SOURCE_USER},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("entry_not_loaded")


@test
async def subentry_need_download(
    hass: HomeAssistant = Depends(hass_fixture),
    _init: None = Depends(mock_init_component),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test subentry creation when model needs to be downloaded."""

    async def delayed_pull(self, model: str) -> None:
        assert model == "llama3.2:latest"
        await asyncio.sleep(0)

    with (
        patch(
            "ollama.AsyncClient.list",
            return_value={"models": [{"model": TEST_MODEL}]},
        ),
        patch("ollama.AsyncClient.pull", delayed_pull),
    ):
        new_flow = await hass.config_entries.subentries.async_init(
            (entry.entry_id, "conversation"),
            context={"source": SOURCE_USER},
        )

        expect(new_flow["type"]).to_be(FlowResultType.FORM)
        expect(new_flow["step_id"]).to_equal("set_options")

        result = await hass.config_entries.subentries.async_configure(
            new_flow["flow_id"],
            {
                ollama.CONF_MODEL: "llama3.2:latest",
                CONF_NAME: "New Test Conversation",
                ollama.CONF_PROMPT: "new test prompt",
                ollama.CONF_MAX_HISTORY: 50,
                ollama.CONF_NUM_CTX: 16384,
                ollama.CONF_THINK: False,
            },
        )

        expect(result["type"]).to_be(FlowResultType.SHOW_PROGRESS)
        expect(result["step_id"]).to_equal("download")
        expect(result["progress_action"]).to_equal("download")

        await hass.async_block_till_done()

        result = await hass.config_entries.subentries.async_configure(
            new_flow["flow_id"], {}
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("New Test Conversation")
    expect(result["data"]).to_equal(
        {
            ollama.CONF_MODEL: "llama3.2:latest",
            ollama.CONF_PROMPT: "new test prompt",
            ollama.CONF_MAX_HISTORY: 50.0,
            ollama.CONF_NUM_CTX: 16384.0,
            ollama.CONF_THINK: False,
        }
    )


@test
async def subentry_download_error(
    hass: HomeAssistant = Depends(hass_fixture),
    _init: None = Depends(mock_init_component),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test subentry creation when model download fails."""

    async def delayed_pull(self, model: str) -> None:
        await asyncio.sleep(0)
        raise RuntimeError("Download failed")

    with (
        patch(
            "ollama.AsyncClient.list",
            return_value={"models": [{"model": TEST_MODEL}]},
        ),
        patch("ollama.AsyncClient.pull", delayed_pull),
    ):
        new_flow = await hass.config_entries.subentries.async_init(
            (entry.entry_id, "conversation"),
            context={"source": SOURCE_USER},
        )

        expect(new_flow["type"]).to_be(FlowResultType.FORM)
        expect(new_flow["step_id"]).to_equal("set_options")

        result = await hass.config_entries.subentries.async_configure(
            new_flow["flow_id"],
            {
                ollama.CONF_MODEL: "llama3.2:latest",
                CONF_NAME: "New Test Conversation",
                ollama.CONF_PROMPT: "new test prompt",
                ollama.CONF_MAX_HISTORY: 50,
                ollama.CONF_NUM_CTX: 16384,
                ollama.CONF_THINK: False,
            },
        )

        expect(result["type"]).to_be(FlowResultType.SHOW_PROGRESS)
        expect(result["step_id"]).to_equal("download")
        expect(result["progress_action"]).to_equal("download")

        await hass.async_block_till_done()

        result = await hass.config_entries.subentries.async_configure(
            new_flow["flow_id"], {}
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("download_failed")


@test.cases(
    test.case(
        "update_api_key",
        {
            CONF_URL: "http://localhost:11434",
            CONF_API_KEY: "old-api-key",
        },
        {
            CONF_API_KEY: "new-api-key",
        },
        {
            CONF_URL: "http://localhost:11434",
            CONF_API_KEY: "new-api-key",
        },
    ),
    test.case(
        "remove_api_key",
        {
            CONF_URL: "http://localhost:11434",
            CONF_API_KEY: "old-api-key",
        },
        {},
        {
            CONF_URL: "http://localhost:11434",
        },
    ),
)
async def reauth_flow_success(
    init_data: dict,
    input_data: dict,
    expected_data: dict,
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test successful reauthentication flow."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=init_data,
        options={CONF_API_KEY: "stale-options-api-key"},
        version=3,
        minor_version=3,
    )
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    with patch(
        "homeassistant.components.ollama.config_flow.ollama.AsyncClient.list",
        return_value={"models": [{"model": TEST_MODEL}]},
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            input_data,
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(entry.data).to_equal(expected_data)
    expect(entry.options).to_equal({})


@test.cases(
    test.case(
        "invalid_auth",
        ResponseError(error="Unauthorized", status_code=401),
        "invalid_auth",
    ),
    test.case(
        "cannot_connect",
        ConnectError(message="Connection failed"),
        "cannot_connect",
    ),
)
async def reauth_flow_errors(
    side_effect: Exception,
    error: str,
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reauthentication flow when authentication fails."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_URL: "http://localhost:11434",
            CONF_API_KEY: "old-api-key",
        },
        version=3,
        minor_version=3,
    )
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    with patch(
        "homeassistant.components.ollama.config_flow.ollama.AsyncClient.list",
        side_effect=side_effect,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_API_KEY: "other-api-key",
            },
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["errors"]).to_equal({"base": error})

    with patch(
        "homeassistant.components.ollama.config_flow.ollama.AsyncClient.list",
        return_value={"models": [{"model": TEST_MODEL}]},
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_API_KEY: "new-api-key",
            },
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(entry.data).to_equal(
        {
            CONF_URL: "http://localhost:11434",
            CONF_API_KEY: "new-api-key",
        }
    )


@test.cases(
    test.case("cannot_connect", ConnectError(message=""), "cannot_connect"),
    test.case("unknown", RuntimeError(), "unknown"),
)
async def form_errors(
    side_effect: Exception,
    error: str,
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle errors."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    with patch(
        "homeassistant.components.ollama.config_flow.ollama.AsyncClient.list",
        side_effect=side_effect,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {ollama.CONF_URL: "http://localhost:11434"}
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": error})


@test.cases(
    test.case("cannot_connect", ConnectError(message=""), "cannot_connect"),
    test.case("unknown", RuntimeError(), "unknown"),
)
async def form_errors_recovery(
    side_effect: Exception,
    error: str,
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that the user flow recovers after an error and completes successfully."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    with patch(
        "homeassistant.components.ollama.config_flow.ollama.AsyncClient.list",
        side_effect=side_effect,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {ollama.CONF_URL: "http://localhost:11434"}
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error})

    with patch(
        "homeassistant.components.ollama.config_flow.ollama.AsyncClient.list",
        return_value={"models": [{"model": TEST_MODEL}]},
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {ollama.CONF_URL: "http://localhost:11434"},
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal({ollama.CONF_URL: "http://localhost:11434"})


@test
async def form_invalid_url(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we handle invalid URL."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], {ollama.CONF_URL: "not-a-valid-url"}
    )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "invalid_url"})


@test
async def subentry_connection_error(
    hass: HomeAssistant = Depends(hass_fixture),
    _init: None = Depends(mock_init_component),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test subentry creation when connection to Ollama server fails."""
    with patch(
        "ollama.AsyncClient.list",
        side_effect=ConnectError("Connection failed"),
    ):
        new_flow = await hass.config_entries.subentries.async_init(
            (entry.entry_id, "conversation"),
            context={"source": SOURCE_USER},
        )

    expect(new_flow["type"]).to_be(FlowResultType.ABORT)
    expect(new_flow["reason"]).to_equal("cannot_connect")


@test
async def subentry_model_check_exception(
    hass: HomeAssistant = Depends(hass_fixture),
    _init: None = Depends(mock_init_component),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test subentry creation when checking model availability throws exception."""
    with patch(
        "ollama.AsyncClient.list",
        side_effect=[
            {"models": [{"model": TEST_MODEL}]},
            RuntimeError("Failed to check models"),
        ],
    ):
        new_flow = await hass.config_entries.subentries.async_init(
            (entry.entry_id, "conversation"),
            context={"source": SOURCE_USER},
        )

        expect(new_flow["type"]).to_be(FlowResultType.FORM)
        expect(new_flow["step_id"]).to_equal("set_options")

        result = await hass.config_entries.subentries.async_configure(
            new_flow["flow_id"],
            {
                ollama.CONF_MODEL: "new_model:latest",
                CONF_NAME: "Test Conversation",
                ollama.CONF_PROMPT: "test prompt",
                ollama.CONF_MAX_HISTORY: 50,
                ollama.CONF_NUM_CTX: 16384,
                ollama.CONF_THINK: False,
            },
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("cannot_connect")


@test
async def subentry_reconfigure_with_download(
    hass: HomeAssistant = Depends(hass_fixture),
    _init: None = Depends(mock_init_component),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reconfiguring subentry when model needs to be downloaded."""
    subentry = next(iter(entry.subentries.values()))

    async def delayed_pull(self, model: str) -> None:
        assert model == "llama3.2:latest"
        await asyncio.sleep(0)

    with (
        patch(
            "ollama.AsyncClient.list",
            return_value={"models": [{"model": TEST_MODEL}]},
        ),
        patch("ollama.AsyncClient.pull", delayed_pull),
    ):
        reconfigure_flow = await entry.start_subentry_reconfigure_flow(
            hass, subentry.subentry_id
        )

        expect(reconfigure_flow["type"]).to_be(FlowResultType.FORM)
        expect(reconfigure_flow["step_id"]).to_equal("set_options")

        result = await hass.config_entries.subentries.async_configure(
            reconfigure_flow["flow_id"],
            {
                ollama.CONF_MODEL: "llama3.2:latest",
                ollama.CONF_PROMPT: "updated prompt",
                ollama.CONF_MAX_HISTORY: 75,
                ollama.CONF_NUM_CTX: 8192,
                ollama.CONF_THINK: True,
            },
        )

        expect(result["type"]).to_be(FlowResultType.SHOW_PROGRESS)
        expect(result["step_id"]).to_equal("download")

        await hass.async_block_till_done()

        result = await hass.config_entries.subentries.async_configure(
            reconfigure_flow["flow_id"], {}
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(subentry.data).to_equal(
        {
            ollama.CONF_MODEL: "llama3.2:latest",
            ollama.CONF_PROMPT: "updated prompt",
            ollama.CONF_MAX_HISTORY: 75.0,
            ollama.CONF_NUM_CTX: 8192.0,
            ollama.CONF_THINK: True,
        }
    )


@test
async def filter_invalid_llms(
    hass: HomeAssistant = Depends(hass_fixture),
    _init: None = Depends(mock_init_component),
    entry: MockConfigEntry = Depends(mock_config_entry_with_assist_invalid_api),
) -> None:
    """Test reconfiguring subentry when one of the configured LLM APIs has been removed."""
    subentry = next(iter(entry.subentries.values()))

    expect(len(subentry.data.get(CONF_LLM_HASS_API))).to_equal(2)
    expect("invalid_api" in subentry.data.get(CONF_LLM_HASS_API)).to_equal(True)
    expect("assist" in subentry.data.get(CONF_LLM_HASS_API)).to_equal(True)

    valid_apis = ollama.config_flow.filter_invalid_llm_apis(
        hass, subentry.data[CONF_LLM_HASS_API]
    )

    expect(len(valid_apis)).to_equal(1)
    expect("invalid_api" not in valid_apis).to_equal(True)
    expect("assist" in valid_apis).to_equal(True)


@test
async def creating_ai_task_subentry(
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    _init: None = Depends(mock_init_component),
) -> None:
    """Test creating an AI task subentry."""
    old_subentries = set(entry.subentries)
    expect(len(entry.subentries)).to_equal(2)

    with patch(
        "ollama.AsyncClient.list",
        return_value={"models": [{"model": "test_model:latest"}]},
    ):
        result = await hass.config_entries.subentries.async_init(
            (entry.entry_id, "ai_task_data"),
            context={"source": SOURCE_USER},
        )

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("set_options")
    expect(bool(result.get("errors"))).to_equal(False)

    with patch(
        "ollama.AsyncClient.list",
        return_value={"models": [{"model": "test_model:latest"}]},
    ):
        result2 = await hass.config_entries.subentries.async_configure(
            result["flow_id"],
            {
                "name": "Custom AI Task",
                ollama.CONF_MODEL: "test_model:latest",
                ollama.CONF_MAX_HISTORY: 5,
                ollama.CONF_NUM_CTX: 4096,
                ollama.CONF_KEEP_ALIVE: 30,
                ollama.CONF_THINK: False,
            },
        )
        await hass.async_block_till_done()

    expect(result2.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2.get("title")).to_equal("Custom AI Task")
    expect(result2.get("data")).to_equal(
        {
            ollama.CONF_MODEL: "test_model:latest",
            ollama.CONF_MAX_HISTORY: 5,
            ollama.CONF_NUM_CTX: 4096,
            ollama.CONF_KEEP_ALIVE: 30,
            ollama.CONF_THINK: False,
        }
    )

    expect(len(entry.subentries)).to_equal(3)

    new_subentry_id = list(set(entry.subentries) - old_subentries)[0]
    new_subentry = entry.subentries[new_subentry_id]
    expect(new_subentry.subentry_type).to_equal("ai_task_data")
    expect(new_subentry.title).to_equal("Custom AI Task")


@test
async def ai_task_subentry_not_loaded(
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test creating an AI task subentry when entry is not loaded."""
    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, "ai_task_data"),
        context={"source": SOURCE_USER},
    )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("entry_not_loaded")


@test.cases(
    test.case(
        "with_token",
        {CONF_URL: "http://localhost:11434", CONF_API_KEY: "my-secret-token"},
        {"Authorization": "Bearer my-secret-token"},
        {CONF_URL: "http://localhost:11434", CONF_API_KEY: "my-secret-token"},
    ),
    test.case(
        "empty_token",
        {CONF_URL: "http://localhost:11434", CONF_API_KEY: ""},
        None,
        {CONF_URL: "http://localhost:11434"},
    ),
    test.case(
        "whitespace_token",
        {CONF_URL: "http://localhost:11434", CONF_API_KEY: "          "},
        None,
        {CONF_URL: "http://localhost:11434"},
    ),
    test.case(
        "no_token",
        {CONF_URL: "http://localhost:11434"},
        None,
        {CONF_URL: "http://localhost:11434"},
    ),
)
async def user_step_async_client_headers(
    user_input: dict[str, str],
    expected_headers: dict[str, str] | None,
    expected_data: dict[str, str],
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test Authorization header passed to AsyncClient with/without api_key."""
    with patch(
        "homeassistant.components.ollama.config_flow.ollama.AsyncClient",
    ) as mock_async_client:
        mock_async_client.return_value.list = AsyncMock(return_value={"models": []})

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        expect(result["type"]).to_be(FlowResultType.FORM)

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=user_input,
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(expected_data)
    mock_async_client.assert_called_with(
        host="http://localhost:11434",
        headers=expected_headers,
        verify=ANY,
    )


@test.cases(
    test.case(
        "400_unknown",
        400,
        "unknown",
        "Bad Request",
        {
            CONF_URL: "http://localhost:11434",
            CONF_API_KEY: "my-secret-token",
        },
    ),
    test.case(
        "401_unauthorized",
        401,
        "invalid_auth",
        "Unauthorized",
        {
            CONF_URL: "http://localhost:11434",
            CONF_API_KEY: "my-secret-token",
        },
    ),
    test.case(
        "403_unauthorized",
        403,
        "invalid_auth",
        "Unauthorized",
        {
            CONF_URL: "http://localhost:11434",
            CONF_API_KEY: "my-secret-token",
        },
    ),
    test.case(
        "403_forbidden_no_key",
        403,
        "invalid_auth",
        "Forbidden",
        {
            CONF_URL: "http://localhost:11434",
        },
    ),
)
async def user_step_errors(
    status_code: int,
    error: str,
    error_message: str,
    user_input: dict[str, str],
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test error handling when ollama returns HTTP 4xx."""
    with patch(
        "homeassistant.components.ollama.config_flow.ollama.AsyncClient"
    ) as mock_async_client:
        mock_client_instance = AsyncMock()
        mock_async_client.return_value = mock_client_instance
        mock_client_instance.list.side_effect = ResponseError(
            error=error_message, status_code=status_code
        )

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        expect(result["type"]).to_be(FlowResultType.FORM)

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=user_input,
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result.get("errors")).to_equal({"base": error})


@test
async def user_step_trim_url(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test URL is trimmed before validation and persistence."""
    with patch(
        "homeassistant.components.ollama.config_flow.ollama.AsyncClient",
    ) as mock_async_client:
        mock_async_client.return_value.list = AsyncMock(return_value={"models": []})

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        expect(result["type"]).to_be(FlowResultType.FORM)

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_URL: "  http://localhost:11434  ",
            },
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal({CONF_URL: "http://localhost:11434"})
    mock_async_client.assert_called_with(
        host="http://localhost:11434",
        headers=None,
        verify=ANY,
    )
