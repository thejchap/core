"""Test the Google Cloud config flow."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components import tts
from homeassistant.components.google_cloud.config_flow import UPLOADED_KEY_FILE
from homeassistant.components.google_cloud.const import (
    CONF_KEY_FILE,
    CONF_SERVICE_ACCOUNT_INFO,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_PLATFORM
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.setup import async_setup_component

from ._fixtures import (
    VALID_SERVICE_ACCOUNT_INFO,
    create_google_credentials_json,
    create_invalid_google_credentials_json,
    mock_api_tts_from_service_account_file,
    mock_api_tts_from_service_account_info,
    mock_config_entry,
    mock_process_uploaded_file,
    mock_setup_entry,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def user_flow_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    process_uploaded_file: MagicMock = Depends(mock_process_uploaded_file),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test user flow creates entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(bool(result["errors"])).to_be(False)

    uploaded_file = str(uuid4())
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {UPLOADED_KEY_FILE: uploaded_file},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Google Cloud")
    expect(result["data"]).to_equal(
        {CONF_SERVICE_ACCOUNT_INFO: VALID_SERVICE_ACCOUNT_INFO}
    )
    process_uploaded_file.assert_called_with(hass, uploaded_file)
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def user_flow_missing_file(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test user flow when uploaded file is missing."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {UPLOADED_KEY_FILE: str(uuid4())},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "invalid_file"})
    expect(len(setup_entry.mock_calls)).to_equal(0)


@test
async def user_flow_invalid_file(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _invalid_creds: str = Depends(create_invalid_google_credentials_json),
    process_uploaded_file: MagicMock = Depends(mock_process_uploaded_file),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test user flow when uploaded file is invalid."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    uploaded_file = str(uuid4())
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {UPLOADED_KEY_FILE: uploaded_file},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "invalid_file"})
    process_uploaded_file.assert_called_with(hass, uploaded_file)
    expect(len(setup_entry.mock_calls)).to_equal(0)


@test
async def import_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    creds_json: str = Depends(create_google_credentials_json),
    _from_file: AsyncMock = Depends(mock_api_tts_from_service_account_file),
    _from_info: AsyncMock = Depends(mock_api_tts_from_service_account_info),
) -> None:
    """Test the import flow."""
    expect(bool(hass.config_entries.async_entries(DOMAIN))).to_be(False)
    expect(
        await async_setup_component(
            hass,
            tts.DOMAIN,
            {tts.DOMAIN: {CONF_PLATFORM: DOMAIN} | {CONF_KEY_FILE: creds_json}},
        )
    ).to_be(True)
    await hass.async_block_till_done()
    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    config_entry = hass.config_entries.async_entries(DOMAIN)[0]
    expect(config_entry.state).to_be(config_entries.ConfigEntryState.LOADED)


@test
async def import_flow_invalid_file(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    invalid_creds: str = Depends(create_invalid_google_credentials_json),
    api_tts_from_file: AsyncMock = Depends(mock_api_tts_from_service_account_file),
) -> None:
    """Test the import flow when the key file is invalid."""
    expect(bool(hass.config_entries.async_entries(DOMAIN))).to_be(False)
    expect(
        await async_setup_component(
            hass,
            tts.DOMAIN,
            {tts.DOMAIN: {CONF_PLATFORM: DOMAIN} | {CONF_KEY_FILE: invalid_creds}},
        )
    ).to_be(True)
    await hass.async_block_till_done()
    expect(bool(hass.config_entries.async_entries(DOMAIN))).to_be(False)
    expect(api_tts_from_file.list_voices.call_count).to_equal(1)


@test
async def options_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    api_tts_from_info: AsyncMock = Depends(mock_api_tts_from_service_account_info),
) -> None:
    """Test options flow."""
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    expect(api_tts_from_info.list_voices.call_count).to_equal(1)

    expect(config_entry.options).to_equal({})

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")
    data_schema = result["data_schema"].schema
    expect(set(data_schema)).to_equal(
        {
            "language",
            "gender",
            "voice",
            "encoding",
            "speed",
            "pitch",
            "gain",
            "profiles",
            "text_type",
            "stt_model",
        }
    )
    expect(api_tts_from_info.list_voices.call_count).to_equal(2)

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"language": "el-GR"},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(config_entry.options).to_equal(
        {
            "language": "el-GR",
            "gender": "NEUTRAL",
            "voice": "",
            "encoding": "MP3",
            "speed": 1.0,
            "pitch": 0.0,
            "gain": 0.0,
            "profiles": [],
            "text_type": "text",
            "stt_model": "latest_short",
        }
    )
    expect(api_tts_from_info.list_voices.call_count).to_equal(3)
