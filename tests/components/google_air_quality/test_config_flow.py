"""Test the Google Air Quality config flow."""

from unittest.mock import AsyncMock

from google_air_quality_api.exceptions import GoogleAirQualityApiError
from tryke import Depends, expect, fixture, test

from homeassistant.components.google_air_quality.const import (
    CONF_REFERRER,
    DOMAIN,
    SECTION_API_KEY_OPTIONS,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import (
    CONF_API_KEY,
    CONF_LATITUDE,
    CONF_LOCATION,
    CONF_LONGITUDE,
    CONF_NAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_api, mock_config_entry, mock_setup_entry

from tests.common import MockConfigEntry, get_schema_suggested_value
from tests.hass_fixtures import hass as hass_fixture, mock_network


def _assert_create_entry_result(
    result: dict, expected_referrer: str | None = None
) -> None:
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Google Air Quality")
    expect(result["data"]).to_equal(
        {CONF_API_KEY: "test-api-key", CONF_REFERRER: expected_referrer}
    )
    expect(len(result["subentries"])).to_equal(1)
    subentry = result["subentries"][0]
    expect(subentry["subentry_type"]).to_equal("location")
    expect(subentry["title"]).to_equal("test-name")
    expect(subentry["data"]).to_equal({CONF_LATITUDE: 10.1, CONF_LONGITUDE: 20.1})


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Apply autouse-equivalent fixtures via this trigger."""


@test
async def create_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    api: AsyncMock = Depends(mock_api),
) -> None:
    """Test creating a config entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "test-name",
            CONF_API_KEY: "test-api-key",
            CONF_LOCATION: {CONF_LATITUDE: 10.1, CONF_LONGITUDE: 20.1},
        },
    )

    api.async_get_current_conditions.assert_called_once_with(lat=10.1, lon=20.1)

    _assert_create_entry_result(result)
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def form_with_referrer(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    api: AsyncMock = Depends(mock_api),
) -> None:
    """Test we get the form and optional referrer is specified."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "test-name",
            CONF_API_KEY: "test-api-key",
            SECTION_API_KEY_OPTIONS: {CONF_REFERRER: "test-referrer"},
            CONF_LOCATION: {CONF_LATITUDE: 10.1, CONF_LONGITUDE: 20.1},
        },
    )

    api.async_get_current_conditions.assert_called_once_with(lat=10.1, lon=20.1)

    _assert_create_entry_result(result, expected_referrer="test-referrer")
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case(
        "cannot_connect",
        api_exception=GoogleAirQualityApiError(),
        expected_error="cannot_connect",
    ),
    test.case("unknown", api_exception=ValueError(), expected_error="unknown"),
)
async def form_exceptions(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    api: AsyncMock = Depends(mock_api),
    *,
    api_exception: Exception,
    expected_error: str,
) -> None:
    """Test we handle exceptions."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    api.async_get_current_conditions.side_effect = api_exception
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "test-name",
            CONF_API_KEY: "test-api-key",
            CONF_LOCATION: {CONF_LATITUDE: 10.1, CONF_LONGITUDE: 20.1},
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": expected_error})
    data_schema = result["data_schema"].schema
    expect(get_schema_suggested_value(data_schema, CONF_NAME)).to_equal("test-name")
    expect(get_schema_suggested_value(data_schema, CONF_API_KEY)).to_equal(
        "test-api-key"
    )
    expect(get_schema_suggested_value(data_schema, CONF_LOCATION)).to_equal(
        {CONF_LATITUDE: 10.1, CONF_LONGITUDE: 20.1}
    )

    api.async_get_current_conditions.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "test-name",
            CONF_API_KEY: "test-api-key",
            CONF_LOCATION: {CONF_LATITUDE: 10.1, CONF_LONGITUDE: 20.1},
        },
    )

    _assert_create_entry_result(result)
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def form_api_key_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    api: AsyncMock = Depends(mock_api),
) -> None:
    """Test user input for config_entry with API key that already exists."""
    config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "test-name",
            CONF_API_KEY: "test-api-key",
            CONF_LOCATION: {CONF_LATITUDE: 10.2, CONF_LONGITUDE: 20.2},
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    expect(api.async_get_current_conditions.call_count).to_equal(0)


@test
async def form_location_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    api: AsyncMock = Depends(mock_api),
) -> None:
    """Test user input for a location that already exists."""
    config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "test-name",
            CONF_API_KEY: "another-api-key",
            CONF_LOCATION: {CONF_LATITUDE: 10.1001, CONF_LONGITUDE: 20.0999},
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    expect(api.async_get_current_conditions.call_count).to_equal(0)


@test
async def form_not_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    api: AsyncMock = Depends(mock_api),
) -> None:
    """Test user input for config_entry different than the existing one."""
    config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "new-test-name",
            CONF_API_KEY: "new-test-api-key",
            CONF_LOCATION: {CONF_LATITUDE: 10.1002, CONF_LONGITUDE: 20.0998},
        },
    )

    api.async_get_current_conditions.assert_called_once_with(lat=10.1002, lon=20.0998)

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Google Air Quality")
    expect(result["data"]).to_equal(
        {CONF_API_KEY: "new-test-api-key", CONF_REFERRER: None}
    )
    expect(len(result["subentries"])).to_equal(1)
    subentry = result["subentries"][0]
    expect(subentry["subentry_type"]).to_equal("location")
    expect(subentry["title"]).to_equal("new-test-name")
    expect(subentry["data"]).to_equal({CONF_LATITUDE: 10.1002, CONF_LONGITUDE: 20.0998})
    expect(len(setup_entry.mock_calls)).to_equal(2)


@test
async def subentry_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    api: AsyncMock = Depends(mock_api),
) -> None:
    """Test creating a location subentry."""
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(api.async_get_current_conditions.call_count).to_equal(1)

    result = await hass.config_entries.subentries.async_init(
        (config_entry.entry_id, "location"),
        context={"source": "user"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("location")

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "Work",
            CONF_LOCATION: {CONF_LATITUDE: 30.1, CONF_LONGITUDE: 40.1},
        },
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Work")
    expect(result["data"]).to_equal({CONF_LATITUDE: 30.1, CONF_LONGITUDE: 40.1})

    expect(api.async_get_current_conditions.call_count).to_equal(1 + 1 + 2)

    entry = hass.config_entries.async_get_entry(config_entry.entry_id)
    expect(len(entry.subentries)).to_equal(2)


@test
async def subentry_flow_location_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _api: AsyncMock = Depends(mock_api),
) -> None:
    """Test user input for a location that already exists."""
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)

    result = await hass.config_entries.subentries.async_init(
        (config_entry.entry_id, "location"),
        context={"source": "user"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("location")

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "Work",
            CONF_LOCATION: {CONF_LATITUDE: 10.1, CONF_LONGITUDE: 20.1},
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]["base"]).to_equal("location_already_configured")

    entry = hass.config_entries.async_get_entry(config_entry.entry_id)
    expect(len(entry.subentries)).to_equal(1)


@test
async def subentry_flow_location_name_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _api: AsyncMock = Depends(mock_api),
) -> None:
    """Test user input for a location name that already exists."""
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)

    result = await hass.config_entries.subentries.async_init(
        (config_entry.entry_id, "location"),
        context={"source": "user"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("location")

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "Home",
            CONF_LOCATION: {CONF_LATITUDE: 30.1, CONF_LONGITUDE: 40.1},
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]["base"]).to_equal("location_name_already_configured")

    entry = hass.config_entries.async_get_entry(config_entry.entry_id)
    expect(len(entry.subentries)).to_equal(1)


@test
async def subentry_flow_entry_not_loaded(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test creating a location subentry when the parent entry is not loaded."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.subentries.async_init(
        (config_entry.entry_id, "location"),
        context={"source": SOURCE_USER},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("entry_not_loaded")
