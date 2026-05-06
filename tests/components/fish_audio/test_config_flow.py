"""Config flow tests for Fish Audio."""

from __future__ import annotations

from unittest.mock import AsyncMock

from fishaudio import AuthenticationError, FishAudioError
from tryke import Depends, expect, fixture, test

from homeassistant.components.fish_audio.const import (
    CONF_BACKEND,
    CONF_LANGUAGE,
    CONF_LATENCY,
    CONF_NAME,
    CONF_SELF_ONLY,
    CONF_SORT_BY,
    CONF_TITLE,
    CONF_USER_ID,
    CONF_VOICE_ID,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_config_entry, mock_fishaudio_client, mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def user_flow_happy_path(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: AsyncMock = Depends(mock_fishaudio_client),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test the full user flow happy path."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_API_KEY: "test-key"}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Fish Audio")
    expect(dict(result["data"])).to_equal(
        {CONF_API_KEY: "test-key", CONF_USER_ID: "test_user"}
    )
    expect(result["result"].unique_id).to_equal("test_user")


@test.cases(
    test.case(
        "cannot_connect",
        side_effect=FishAudioError("Connection error"),
        error_base="cannot_connect",
    ),
    test.case(
        "invalid_auth",
        side_effect=AuthenticationError(401, "Invalid API key"),
        error_base="invalid_auth",
    ),
    test.case(
        "unknown",
        side_effect=Exception("Unexpected error"),
        error_base="unknown",
    ),
)
async def user_flow_api_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_fishaudio_client),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    *,
    side_effect: Exception,
    error_base: str,
) -> None:
    """Test user flow with API errors during validation and recovery."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    client.account.get_credits.side_effect = side_effect

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_API_KEY: "bad-key"}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": error_base})

    expect(setup_entry.called).to_be(False)

    client.account.get_credits.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_API_KEY: "test-key"}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Fish Audio")
    expect(dict(result["data"])).to_equal(
        {CONF_API_KEY: "test-key", CONF_USER_ID: "test_user"}
    )
    expect(result["result"].unique_id).to_equal("test_user")

    expect(setup_entry.call_count).to_equal(1)


@test
async def user_flow_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _client: AsyncMock = Depends(mock_fishaudio_client),
) -> None:
    """Test that the user flow is aborted if already configured."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_API_KEY: "test-api-key"}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def subflow_happy_path(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: AsyncMock = Depends(mock_fishaudio_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test the full subflow happy path."""
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)

    result = await hass.config_entries.subentries.async_init(
        (config_entry.entry_id, "tts"),
        context={"source": SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        user_input={
            CONF_TITLE: "",
            CONF_LANGUAGE: "en",
            CONF_SORT_BY: "task_count",
            CONF_SELF_ONLY: False,
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("model")

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        user_input={
            CONF_VOICE_ID: "voice-alpha",
            CONF_BACKEND: "s1",
            CONF_LATENCY: "balanced",
            CONF_NAME: "My Custom Voice",
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("My Custom Voice")
    expect(result["data"][CONF_VOICE_ID]).to_equal("voice-alpha")
    expect(result["data"][CONF_BACKEND]).to_equal("s1")
    expect(result["data"][CONF_LATENCY]).to_equal("balanced")
    expect(result["unique_id"]).to_equal("voice-alpha-s1")

    entry = hass.config_entries.async_get_entry(config_entry.entry_id)
    expect(len(entry.subentries)).to_equal(3)


@test
async def subflow_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_fishaudio_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test the subflow when fetching models fails."""
    client.voices.list.side_effect = FishAudioError("API Error")

    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)

    result = await hass.config_entries.subentries.async_init(
        (config_entry.entry_id, "tts"),
        context={"source": SOURCE_USER},
    )

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        user_input={CONF_LANGUAGE: "en"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("cannot_connect")


@test
async def subflow_no_models_found(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_fishaudio_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test the subflow when no voices are found."""
    client.voices.list.return_value = AsyncMock(items=[])

    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)

    result = await hass.config_entries.subentries.async_init(
        (config_entry.entry_id, "tts"),
        context={"source": SOURCE_USER},
    )

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        user_input={CONF_LANGUAGE: "en"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_models_found")


@test
async def subflow_reconfigure(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: AsyncMock = Depends(mock_fishaudio_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reconfiguring an existing TTS subentry."""
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)

    subentry = list(config_entry.subentries.values())[0]

    result = await hass.config_entries.subentries.async_init(
        (config_entry.entry_id, "tts"),
        context={"source": "reconfigure", "subentry_id": subentry.subentry_id},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        user_input={
            CONF_TITLE: "",
            CONF_LANGUAGE: "es",
            CONF_SORT_BY: "task_count",
            CONF_SELF_ONLY: False,
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("model")

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        user_input={
            CONF_VOICE_ID: "voice-gamma",
            CONF_BACKEND: "s1",
            CONF_LATENCY: "normal",
            CONF_NAME: "Updated Voice",
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")


@test
async def subflow_reconfigure_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: AsyncMock = Depends(mock_fishaudio_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reconfiguring a TTS subentry to match an existing one."""
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)

    first_subentry = next(
        s for s in config_entry.subentries.values() if s.title == "Test Voice"
    )

    result = await hass.config_entries.subentries.async_init(
        (config_entry.entry_id, "tts"),
        context={"source": "reconfigure", "subentry_id": first_subentry.subentry_id},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        user_input={
            CONF_TITLE: "",
            CONF_LANGUAGE: "en",
            CONF_SORT_BY: "task_count",
            CONF_SELF_ONLY: False,
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("model")

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        user_input={
            CONF_VOICE_ID: "voice-beta",
            CONF_BACKEND: "s1",
            CONF_LATENCY: "normal",
            CONF_NAME: "Test Voice Updated",
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def subflow_entry_not_loaded(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test creating a TTS subentry when the parent entry is not loaded."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.subentries.async_init(
        (config_entry.entry_id, "tts"),
        context={"source": SOURCE_USER},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("entry_not_loaded")
