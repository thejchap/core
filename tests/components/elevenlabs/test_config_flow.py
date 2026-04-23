"""Test the ElevenLabs text-to-speech config flow."""

from unittest.mock import AsyncMock, MagicMock, patch

from elevenlabs.types import GetVoicesResponse
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

from tests.common import MockConfigEntry
from tests.components.elevenlabs._fixtures import (
    mock_async_client,
    mock_async_client_api_error,
    mock_async_client_models_error,
    mock_async_client_voices_error,
    mock_entry,
    mock_setup_entry,
    mock_zeroconf,
)
from tests.components.elevenlabs.const import MOCK_MODELS, MOCK_VOICES
from tests.hass_fixtures import hass, mock_network


def _success_client() -> AsyncMock:
    client_mock = AsyncMock()
    client_mock.voices.get_all.return_value = GetVoicesResponse(voices=MOCK_VOICES)
    client_mock.models.list.return_value = MOCK_MODELS
    return client_mock


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def user_step(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_async_client: AsyncMock = Depends(mock_async_client),
) -> None:
    """Test user step create entry result."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(bool(result["errors"])).to_be(False)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_KEY: "api_key"},
    )
    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
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

    mock_setup_entry.assert_called_once()


@test
async def invalid_api_key(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_async_client_api_error: AsyncMock = Depends(mock_async_client_api_error),
) -> None:
    """Test user step with invalid api key."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(bool(result["errors"])).to_be(False)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_KEY: "api_key"},
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_equal({"base": "invalid_api_key"})

    mock_setup_entry.assert_not_called()

    # Swap to a working client by layering a new patch over the error fixture's patch.
    with (
        patch(
            "homeassistant.components.elevenlabs.AsyncElevenLabs",
            return_value=_success_client(),
        ),
        patch(
            "homeassistant.components.elevenlabs.config_flow.AsyncElevenLabs",
            return_value=_success_client(),
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: "api_key"},
        )
    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
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

    mock_setup_entry.assert_called_once()


@test
async def voices_error(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_async_client_voices_error: AsyncMock = Depends(mock_async_client_voices_error),
) -> None:
    """Test user step with voices unauthorized error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(bool(result["errors"])).to_be(False)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_KEY: "api_key"},
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_equal({"base": "unknown"})

    mock_setup_entry.assert_not_called()

    with (
        patch(
            "homeassistant.components.elevenlabs.AsyncElevenLabs",
            return_value=_success_client(),
        ),
        patch(
            "homeassistant.components.elevenlabs.config_flow.AsyncElevenLabs",
            return_value=_success_client(),
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: "api_key"},
        )
    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
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

    mock_setup_entry.assert_called_once()


@test
async def models_error(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_async_client_models_error: AsyncMock = Depends(mock_async_client_models_error),
) -> None:
    """Test user step with models unauthorized error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(bool(result["errors"])).to_be(False)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_KEY: "api_key"},
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_equal({"base": "unknown"})

    mock_setup_entry.assert_not_called()

    with (
        patch(
            "homeassistant.components.elevenlabs.AsyncElevenLabs",
            return_value=_success_client(),
        ),
        patch(
            "homeassistant.components.elevenlabs.config_flow.AsyncElevenLabs",
            return_value=_success_client(),
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: "api_key"},
        )
    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
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

    mock_setup_entry.assert_called_once()


@test
async def options_flow_init(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_async_client: AsyncMock = Depends(mock_async_client),
    mock_entry: MockConfigEntry = Depends(mock_entry),
) -> None:
    """Test options flow init."""
    mock_entry.add_to_hass(hass)
    expect(await hass.config_entries.async_setup(mock_entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(mock_entry.entry_id)

    expect(result["type"] is FlowResultType.FORM).to_be(True)
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

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(mock_entry.options).to_equal(
        {
            CONF_MODEL: "model1",
            CONF_VOICE: "voice1",
            CONF_STT_MODEL: "scribe_v1_experimental",
            CONF_STT_AUTO_LANGUAGE: True,
        }
    )

    mock_setup_entry.assert_called_once()


@test
async def options_flow_voice_settings_default(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_async_client: AsyncMock = Depends(mock_async_client),
    mock_entry: MockConfigEntry = Depends(mock_entry),
) -> None:
    """Test options flow voice settings."""
    mock_entry.add_to_hass(hass)
    expect(await hass.config_entries.async_setup(mock_entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(mock_entry.entry_id)
    expect(result["type"] is FlowResultType.FORM).to_be(True)
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

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("voice_settings")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={},
    )
    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(mock_entry.options).to_equal(
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
