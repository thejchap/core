"""Define tests for the OpenWeatherMap config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock

from pyopenweathermap import RequestError
from tryke import Depends, expect, fixture, test

from homeassistant.components.openweathermap.const import (
    DEFAULT_LANGUAGE,
    DEFAULT_NAME,
    DEFAULT_OWM_MODE,
    DOMAIN,
    OWM_MODE_V30,
)
from homeassistant.config_entries import SOURCE_USER, ConfigEntryState
from homeassistant.const import (
    CONF_API_KEY,
    CONF_LANGUAGE,
    CONF_LATITUDE,
    CONF_LOCATION,
    CONF_LONGITUDE,
    CONF_MODE,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

from ._fixtures import (
    LATITUDE,
    LONGITUDE,
    make_mock_config_entry,
    owm_client_mock as owm_client_mock_fx,
)

CONFIG = {
    CONF_API_KEY: "foo",
    CONF_LATITUDE: LATITUDE,
    CONF_LONGITUDE: LONGITUDE,
    CONF_LANGUAGE: DEFAULT_LANGUAGE,
    CONF_MODE: OWM_MODE_V30,
}

USER_INPUT = {
    CONF_API_KEY: "foo",
    CONF_LOCATION: {CONF_LATITUDE: LATITUDE, CONF_LONGITUDE: LONGITUDE},
    CONF_LANGUAGE: DEFAULT_LANGUAGE,
    CONF_MODE: OWM_MODE_V30,
}

VALID_YAML_CONFIG = {CONF_API_KEY: "foo"}


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Wire mock_network for every test."""


@test
async def successful_config_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    owm_client_mock: AsyncMock = Depends(owm_client_mock_fx),
) -> None:
    """Test that the form is served with valid input."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )
    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(DEFAULT_NAME)
    expect(result["data"][CONF_LATITUDE]).to_equal(
        USER_INPUT[CONF_LOCATION][CONF_LATITUDE]
    )
    expect(result["data"][CONF_LONGITUDE]).to_equal(
        USER_INPUT[CONF_LOCATION][CONF_LONGITUDE]
    )
    expect(result["data"][CONF_API_KEY]).to_equal(USER_INPUT[CONF_API_KEY])

    conf_entries = hass.config_entries.async_entries(DOMAIN)
    entry = conf_entries[0]
    expect(entry.state).to_be(ConfigEntryState.LOADED)

    await hass.config_entries.async_unload(conf_entries[0].entry_id)
    await hass.async_block_till_done()
    expect(entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test
async def abort_config_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    owm_client_mock: AsyncMock = Depends(owm_client_mock_fx),
) -> None:
    """Test that the form is served with same data."""
    mock_config_entry = make_mock_config_entry(OWM_MODE_V30)
    mock_config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)


@test
async def config_flow_options_change(
    hass: HomeAssistant = Depends(hass_fixture),
    owm_client_mock: AsyncMock = Depends(owm_client_mock_fx),
) -> None:
    """Test that the options form."""
    config_entry = MockConfigEntry(
        domain=DOMAIN, unique_id="openweathermap_unique_id", data=CONFIG
    )
    config_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.LOADED)

    result = await hass.config_entries.options.async_init(config_entry.entry_id)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    new_language = "es"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_MODE: DEFAULT_OWM_MODE, CONF_LANGUAGE: new_language},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(config_entry.options).to_equal(
        {
            CONF_LANGUAGE: new_language,
            CONF_MODE: DEFAULT_OWM_MODE,
        }
    )

    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.LOADED)

    result = await hass.config_entries.options.async_init(config_entry.entry_id)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    updated_language = "es"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={CONF_LANGUAGE: updated_language}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(config_entry.options).to_equal(
        {
            CONF_LANGUAGE: updated_language,
            CONF_MODE: DEFAULT_OWM_MODE,
        }
    )

    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.LOADED)


@test
async def form_invalid_api_key(
    hass: HomeAssistant = Depends(hass_fixture),
    owm_client_mock: AsyncMock = Depends(owm_client_mock_fx),
) -> None:
    """Test that the form is served with no input."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})
    owm_client_mock.validate_key.return_value = False
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "invalid_api_key"})
    owm_client_mock.validate_key.return_value = True
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def form_api_call_error(
    hass: HomeAssistant = Depends(hass_fixture),
    owm_client_mock: AsyncMock = Depends(owm_client_mock_fx),
) -> None:
    """Test setting up with api call error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})
    owm_client_mock.validate_key.side_effect = RequestError("oops")
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "cannot_connect"})
    owm_client_mock.validate_key.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
