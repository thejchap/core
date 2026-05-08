"""Test the Google Weather config flow."""

from unittest.mock import AsyncMock

from google_weather_api import GoogleWeatherApiError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.google_weather.const import (
    CONF_REFERRER,
    DOMAIN,
    SECTION_API_KEY_OPTIONS,
)
from homeassistant.const import (
    CONF_API_KEY,
    CONF_LATITUDE,
    CONF_LOCATION,
    CONF_LONGITUDE,
    CONF_NAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    mock_config_entry,
    mock_google_weather_api,
    mock_setup_entry,
)

from tests.common import MockConfigEntry, get_schema_suggested_value
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
    _network: None = Depends(mock_network),
) -> HomeAssistant:
    """Anchor fixture so tryke fully resolves hass."""
    return hass


def _assert_create_entry_result(
    result: dict, expected_referrer: str | None = None
) -> None:
    """Assert that the result is a create entry result."""
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Google Weather")
    expect(result["data"]).to_equal(
        {
            CONF_API_KEY: "test-api-key",
            CONF_REFERRER: expected_referrer,
        }
    )
    expect(len(result["subentries"])).to_equal(1)
    subentry = result["subentries"][0]
    expect(subentry["subentry_type"]).to_equal("location")
    expect(subentry["title"]).to_equal("test-name")
    expect(subentry["data"]).to_equal(
        {
            CONF_LATITUDE: 10.1,
            CONF_LONGITUDE: 20.1,
        }
    )


@test
async def create_entry(
    _trigger: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup: AsyncMock = Depends(mock_setup_entry),
    api: AsyncMock = Depends(mock_google_weather_api),
) -> None:
    """Test creating a config entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "test-name",
            CONF_API_KEY: "test-api-key",
            CONF_LOCATION: {
                CONF_LATITUDE: 10.1,
                CONF_LONGITUDE: 20.1,
            },
        },
    )

    api.async_get_current_conditions.assert_called_once_with(
        latitude=10.1, longitude=20.1
    )

    _assert_create_entry_result(result)
    expect(len(setup.mock_calls)).to_equal(1)


@test
async def form_with_referrer(
    _trigger: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup: AsyncMock = Depends(mock_setup_entry),
    api: AsyncMock = Depends(mock_google_weather_api),
) -> None:
    """Test we get the form and optional referrer is specified."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "test-name",
            CONF_API_KEY: "test-api-key",
            SECTION_API_KEY_OPTIONS: {
                CONF_REFERRER: "test-referrer",
            },
            CONF_LOCATION: {
                CONF_LATITUDE: 10.1,
                CONF_LONGITUDE: 20.1,
            },
        },
    )

    api.async_get_current_conditions.assert_called_once_with(
        latitude=10.1, longitude=20.1
    )

    _assert_create_entry_result(result, expected_referrer="test-referrer")
    expect(len(setup.mock_calls)).to_equal(1)


@test.cases(
    test.case(
        "cannot_connect",
        api_exception=GoogleWeatherApiError(),
        expected_error="cannot_connect",
    ),
    test.case(
        "unknown",
        api_exception=ValueError(),
        expected_error="unknown",
    ),
)
async def form_exceptions(
    *,
    api_exception: Exception,
    expected_error: str,
    _trigger: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup: AsyncMock = Depends(mock_setup_entry),
    api: AsyncMock = Depends(mock_google_weather_api),
) -> None:
    """Test we handle exceptions."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    api.async_get_current_conditions.side_effect = api_exception
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "test-name",
            CONF_API_KEY: "test-api-key",
            CONF_LOCATION: {
                CONF_LATITUDE: 10.1,
                CONF_LONGITUDE: 20.1,
            },
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
        {
            CONF_LATITUDE: 10.1,
            CONF_LONGITUDE: 20.1,
        }
    )

    api.async_get_current_conditions.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "test-name",
            CONF_API_KEY: "test-api-key",
            CONF_LOCATION: {
                CONF_LATITUDE: 10.1,
                CONF_LONGITUDE: 20.1,
            },
        },
    )

    _assert_create_entry_result(result)
    expect(len(setup.mock_calls)).to_equal(1)


@test
async def form_api_key_already_configured(
    _trigger: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _api: AsyncMock = Depends(mock_google_weather_api),
) -> None:
    """Test user input for config_entry with API key that already exists."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "test-name",
            CONF_API_KEY: "test-api-key",
            CONF_LOCATION: {
                CONF_LATITUDE: 10.2,
                CONF_LONGITUDE: 20.2,
            },
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)


@test.skip("not yet ported - subentry/reauth flows")
async def form_location_already_configured(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test location already exists."""


@test.skip("not yet ported - subentry/reauth flows")
async def form_not_already_configured(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test different config entry."""


@test.skip("not yet ported - subentry/reauth flows")
async def subentry_flow(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test subentry flow."""


@test.skip("not yet ported - subentry/reauth flows")
async def subentry_flow_location_already_configured(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test subentry flow with already configured location."""


@test.skip("not yet ported - subentry/reauth flows")
async def reauth(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test reauth flow."""


@test.skip("not yet ported - subentry/reauth flows")
async def reauth_exceptions(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test reauth flow with exceptions."""


@test.skip("not yet ported - subentry/reauth flows")
async def reauth_same_api_key_different_referrer(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test reauth flow with same API key but different referrer."""


@test.skip("not yet ported - subentry/reauth flows")
async def reconfigure(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test reconfigure flow."""


@test.skip("not yet ported - subentry/reauth flows")
async def reconfigure_exceptions(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test reconfigure flow with exceptions."""


@test.skip("not yet ported - subentry/reauth flows")
async def reconfigure_no_subentries(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test reconfigure flow without subentries."""


@test.skip("not yet ported - subentry/reauth flows")
async def subentry_reconfigure(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test subentry reconfigure flow."""


@test.skip("not yet ported - subentry/reauth flows")
async def subentry_flow_entry_not_loaded(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test subentry flow when parent entry isn't loaded."""
