"""Test the Anthropic config flow.

NOTE: this is a partial port. The complex parametrized subentry-options
switching and snapshot-based ``test_model_list`` are skipped pending support
for indirect parametrization and a syrupy fixture in the tryke shim.
"""

from unittest.mock import AsyncMock, patch

from anthropic import (
    APIConnectionError,
    APIResponseValidationError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    InternalServerError,
)
from httpx import URL, Request, Response
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.anthropic.config_flow import (
    DEFAULT_AI_TASK_OPTIONS,
    DEFAULT_CONVERSATION_OPTIONS,
)
from homeassistant.components.anthropic.const import (
    CONF_PROMPT,
    DEFAULT_AI_TASK_NAME,
    DEFAULT_CONVERSATION_NAME,
    DOMAIN,
)
from homeassistant.const import CONF_API_KEY, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    mock_config_entry,
    mock_init_component,
    mock_setup_entry,
    setup_ha,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup_ha: None = Depends(setup_ha),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    with patch(
        "homeassistant.components.anthropic.config_flow.anthropic.resources.models.AsyncModels.list",
        new_callable=AsyncMock,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "api_key": "bla",
            },
        )

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["data"]).to_equal({"api_key": "bla"})
    expect(result2["options"]).to_equal({})
    expect(result2["subentries"]).to_equal(
        [
            {
                "subentry_type": "conversation",
                "data": DEFAULT_CONVERSATION_OPTIONS,
                "title": DEFAULT_CONVERSATION_NAME,
                "unique_id": None,
            },
            {
                "subentry_type": "ai_task_data",
                "data": DEFAULT_AI_TASK_OPTIONS,
                "title": DEFAULT_AI_TASK_NAME,
                "unique_id": None,
            },
        ]
    )
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def duplicate_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test we abort on duplicate config entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be_falsy()

    with patch(
        "homeassistant.components.anthropic.config_flow.anthropic.resources.models.AsyncModels.list",
        new_callable=AsyncMock,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_API_KEY: config_entry.data[CONF_API_KEY],
            },
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def creating_conversation_subentry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _init: None = Depends(mock_init_component),
) -> None:
    """Test creating a conversation subentry."""
    result = await hass.config_entries.subentries.async_init(
        (config_entry.entry_id, "conversation"),
        context={"source": config_entries.SOURCE_USER},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")
    expect(result["errors"]).to_be_falsy()

    result2 = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {CONF_NAME: "Mock name", **DEFAULT_CONVERSATION_OPTIONS},
    )

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("Mock name")

    processed_options = DEFAULT_CONVERSATION_OPTIONS.copy()
    processed_options[CONF_PROMPT] = processed_options[CONF_PROMPT].strip()

    expect(result2["data"]).to_equal(processed_options)


@test
async def creating_conversation_subentry_not_loaded(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _init: None = Depends(mock_init_component),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test creating a conversation subentry when entry is not loaded."""
    await hass.config_entries.async_unload(config_entry.entry_id)
    with patch(
        "anthropic.resources.models.AsyncModels.list",
        return_value=[],
    ):
        result = await hass.config_entries.subentries.async_init(
            (config_entry.entry_id, "conversation"),
            context={"source": config_entries.SOURCE_USER},
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("entry_not_loaded")


@test.cases(
    test.case(
        "cannot_connect",
        side_effect=APIConnectionError(request=None),
        error="cannot_connect",
    ),
    test.case(
        "timeout_connect",
        side_effect=APITimeoutError(request=None),
        error="timeout_connect",
    ),
    test.case(
        "bad_request_unknown",
        side_effect=BadRequestError(
            message="Your credit balance is too low to access the Claude API. Please go to Plans & Billing to upgrade or purchase credits.",
            response=Response(
                status_code=400,
                request=Request(method="POST", url=URL()),
            ),
            body={"type": "error", "error": {"type": "invalid_request_error"}},
        ),
        error="unknown",
    ),
    test.case(
        "authentication_error",
        side_effect=AuthenticationError(
            message="invalid x-api-key",
            response=Response(
                status_code=401,
                request=Request(method="POST", url=URL()),
            ),
            body={"type": "error", "error": {"type": "authentication_error"}},
        ),
        error="authentication_error",
    ),
    test.case(
        "internal_server_unknown",
        side_effect=InternalServerError(
            message=None,
            response=Response(
                status_code=500,
                request=Request(method="POST", url=URL()),
            ),
            body=None,
        ),
        error="unknown",
    ),
    test.case(
        "validation_unknown",
        side_effect=APIResponseValidationError(
            response=Response(
                status_code=200,
                request=Request(method="POST", url=URL()),
            ),
            body=None,
        ),
        error="unknown",
    ),
)
async def api_error(
    side_effect: Exception,
    error: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test that we handle API errors."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.anthropic.config_flow.anthropic.resources.models.AsyncModels.list",
        new_callable=AsyncMock,
        side_effect=side_effect,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "api_key": "bla",
            },
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error})

    with patch(
        "homeassistant.components.anthropic.config_flow.anthropic.resources.models.AsyncModels.list",
        new_callable=AsyncMock,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "api_key": "blabla",
            },
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal({"api_key": "blabla"})


@test
async def reauth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we can reauthenticate."""
    hass.config.components.add("anthropic")
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        state=config_entries.ConfigEntryState.LOADED,
    )

    config_entry.add_to_hass(hass)
    result = await config_entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    with patch(
        "homeassistant.components.anthropic.config_flow.anthropic.resources.models.AsyncModels.list",
        new_callable=AsyncMock,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_API_KEY: "new_api_key",
            },
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(config_entry.data[CONF_API_KEY]).to_equal("new_api_key")


@test.skip("subentry switching uses indirect parametrization with multi-step new_options - not portable to tryke 0.0.27")
async def subentry_options_switching() -> None:
    """Skipped: complex parametrize chain not supported in tryke 0.0.27."""


@test.skip("snapshot fixture not available in tryke shim")
async def model_list() -> None:
    """Skipped: requires syrupy SnapshotAssertion fixture."""
