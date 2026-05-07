"""Tryke ports of the ElevenLabs config flow tests."""

from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.elevenlabs.const import (
    CONF_CONFIGURE_VOICE,
    CONF_MODEL,
    CONF_SIMILARITY,
    CONF_STABILITY,
    CONF_STT_AUTO_LANGUAGE,
    CONF_STT_MODEL,
    CONF_STYLE,
    CONF_USE_SPEAKER_BOOST,
    CONF_VOICE,
    DEFAULT_SIMILARITY,
    DEFAULT_STABILITY,
    DEFAULT_STT_MODEL,
    DEFAULT_STYLE,
    DEFAULT_TTS_MODEL,
    DEFAULT_USE_SPEAKER_BOOST,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    mock_async_client,
    mock_entry,
    mock_setup_entry,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Module-local fixture-resolution anchor."""


@test
async def user_step(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup: AsyncMock = Depends(mock_setup_entry),
    client: AsyncMock = Depends(mock_async_client),
) -> None:
    """Test user step create entry result."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(bool(result["errors"])).to_be(False)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_API_KEY: "api_key"}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("ElevenLabs")
    expect(result["data"]).to_equal({"api_key": "api_key"})
    expect(result["options"]).to_equal(
        {
            CONF_MODEL: DEFAULT_TTS_MODEL,
            CONF_VOICE: "voice1",
            CONF_STT_MODEL: DEFAULT_STT_MODEL,
            CONF_STT_AUTO_LANGUAGE: False,
        }
    )

    setup.assert_called_once()


@test.skip("uses request.getfixturevalue (pytest-only) for mid-test client swap")
async def invalid_api_key() -> None:
    """Stub for test_invalid_api_key (port deferred)."""


@test.skip("uses request.getfixturevalue (pytest-only) for mid-test client swap")
async def voices_error() -> None:
    """Stub for test_voices_error (port deferred)."""


@test.skip("uses request.getfixturevalue (pytest-only) for mid-test client swap")
async def models_error() -> None:
    """Stub for test_models_error (port deferred)."""


@test
async def options_flow_init(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup: AsyncMock = Depends(mock_setup_entry),
    client: AsyncMock = Depends(mock_async_client),
    entry: MockConfigEntry = Depends(mock_entry),
) -> None:
    """Test options flow init."""
    entry.add_to_hass(hass)
    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_MODEL: "model1",
            CONF_VOICE: "voice1",
            CONF_STT_MODEL: "scribe_v1_experimental",
            CONF_STT_AUTO_LANGUAGE: True,
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(entry.options).to_equal(
        {
            CONF_MODEL: "model1",
            CONF_VOICE: "voice1",
            CONF_STT_MODEL: "scribe_v1_experimental",
            CONF_STT_AUTO_LANGUAGE: True,
        }
    )

    setup.assert_called_once()


@test
async def options_flow_voice_settings_default(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup: AsyncMock = Depends(mock_setup_entry),
    client: AsyncMock = Depends(mock_async_client),
    entry: MockConfigEntry = Depends(mock_entry),
) -> None:
    """Test options flow voice settings."""
    entry.add_to_hass(hass)
    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_MODEL: "model1",
            CONF_VOICE: "voice1",
            CONF_STT_MODEL: "scribe_v1_experimental",
            CONF_STT_AUTO_LANGUAGE: False,
            CONF_CONFIGURE_VOICE: True,
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("voice_settings")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(entry.options).to_equal(
        {
            CONF_MODEL: "model1",
            CONF_VOICE: "voice1",
            CONF_STT_MODEL: "scribe_v1_experimental",
            CONF_STT_AUTO_LANGUAGE: False,
            CONF_SIMILARITY: DEFAULT_SIMILARITY,
            CONF_STABILITY: DEFAULT_STABILITY,
            CONF_STYLE: DEFAULT_STYLE,
            CONF_USE_SPEAKER_BOOST: DEFAULT_USE_SPEAKER_BOOST,
        }
    )
