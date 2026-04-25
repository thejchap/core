"""Test the Apple WeatherKit config flow."""

from unittest.mock import AsyncMock, patch

from apple_weatherkit import DataSetType
from apple_weatherkit.client import (
    WeatherKitApiClientAuthenticationError,
    WeatherKitApiClientCommunicationError,
    WeatherKitApiClientError,
)
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.weatherkit.config_flow import (
    WeatherKitUnsupportedLocationError,
)
from homeassistant.components.weatherkit.const import (
    CONF_KEY_ID,
    CONF_KEY_PEM,
    CONF_SERVICE_ID,
    CONF_TEAM_ID,
    DOMAIN,
)
from homeassistant.const import CONF_LATITUDE, CONF_LOCATION, CONF_LONGITUDE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import EXAMPLE_CONFIG_DATA
from ._fixtures import mock_setup_entry

from tests.hass_fixtures import hass as hass_fixture, mock_network


EXAMPLE_USER_INPUT = {
    CONF_LOCATION: {
        CONF_LATITUDE: 35.4690101707532,
        CONF_LONGITUDE: 135.74817234593166,
    },
    CONF_KEY_ID: "QABCDEFG123",
    CONF_SERVICE_ID: "io.home-assistant.testing",
    CONF_TEAM_ID: "ABCD123456",
    CONF_KEY_PEM: "-----BEGIN PRIVATE KEY-----\nwhateverkey\n-----END PRIVATE KEY-----",
}


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we get the form and create an entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.weatherkit.WeatherKitApiClient.get_availability",
        return_value=[DataSetType.CURRENT_WEATHER],
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            EXAMPLE_USER_INPUT,
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)

    location = EXAMPLE_USER_INPUT[CONF_LOCATION]
    expect(result["title"]).to_equal(
        f"{location[CONF_LATITUDE]}, {location[CONF_LONGITUDE]}"
    )

    expect(result["data"]).to_equal(EXAMPLE_CONFIG_DATA)
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case(
        "auth",
        exception=WeatherKitApiClientAuthenticationError,
        expected_error="invalid_auth",
    ),
    test.case(
        "comms",
        exception=WeatherKitApiClientCommunicationError,
        expected_error="cannot_connect",
    ),
    test.case(
        "unsupported",
        exception=WeatherKitUnsupportedLocationError,
        expected_error="unsupported_location",
    ),
    test.case(
        "unknown", exception=WeatherKitApiClientError, expected_error="unknown"
    ),
)
async def error_handling(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    exception: type[Exception],
    expected_error: str,
) -> None:
    """Test that we handle various exceptions and generate appropriate errors."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.weatherkit.WeatherKitApiClient.get_availability",
        side_effect=exception,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            EXAMPLE_USER_INPUT,
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": expected_error})


@test
async def form_unsupported_location(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle when WeatherKit does not support the location."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.weatherkit.WeatherKitApiClient.get_availability",
        return_value=[],
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            EXAMPLE_USER_INPUT,
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "unsupported_location"})

    with patch(
        "homeassistant.components.weatherkit.WeatherKitApiClient.get_availability",
        return_value=[DataSetType.CURRENT_WEATHER],
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            EXAMPLE_USER_INPUT,
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test.cases(
    test.case("correct_header_correct_footer", input_header="-----BEGIN PRIVATE KEY-----\n", input_footer="\n-----END PRIVATE KEY-----"),
    test.case("correct_header_no_footer", input_header="-----BEGIN PRIVATE KEY-----\n", input_footer=""),
    test.case("correct_header_trailing_chars", input_header="-----BEGIN PRIVATE KEY-----\n", input_footer="\n-----END PRIVATE KEY-----\n\n  "),
    test.case("correct_header_em_dash_footer", input_header="-----BEGIN PRIVATE KEY-----\n", input_footer="\n—---END PRIVATE KEY-----"),
    test.case("no_header_correct_footer", input_header="", input_footer="\n-----END PRIVATE KEY-----"),
    test.case("no_header_no_footer", input_header="", input_footer=""),
    test.case("no_header_trailing_chars", input_header="", input_footer="\n-----END PRIVATE KEY-----\n\n  "),
    test.case("no_header_em_dash_footer", input_header="", input_footer="\n—---END PRIVATE KEY-----"),
    test.case("leading_chars_correct_footer", input_header="  \n\n-----BEGIN PRIVATE KEY-----\n", input_footer="\n-----END PRIVATE KEY-----"),
    test.case("leading_chars_no_footer", input_header="  \n\n-----BEGIN PRIVATE KEY-----\n", input_footer=""),
    test.case("leading_chars_trailing_chars", input_header="  \n\n-----BEGIN PRIVATE KEY-----\n", input_footer="\n-----END PRIVATE KEY-----\n\n  "),
    test.case("leading_chars_em_dash_footer", input_header="  \n\n-----BEGIN PRIVATE KEY-----\n", input_footer="\n—---END PRIVATE KEY-----"),
    test.case("em_dash_header_correct_footer", input_header="—---BEGIN PRIVATE KEY-----\n", input_footer="\n-----END PRIVATE KEY-----"),
    test.case("em_dash_header_no_footer", input_header="—---BEGIN PRIVATE KEY-----\n", input_footer=""),
    test.case("em_dash_header_trailing_chars", input_header="—---BEGIN PRIVATE KEY-----\n", input_footer="\n-----END PRIVATE KEY-----\n\n  "),
    test.case("em_dash_header_em_dash_footer", input_header="—---BEGIN PRIVATE KEY-----\n", input_footer="\n—---END PRIVATE KEY-----"),
)
async def auto_fix_key_input(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    input_header: str,
    input_footer: str,
) -> None:
    """Test that we fix common user errors in key input."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.weatherkit.WeatherKitApiClient.get_availability",
        return_value=[DataSetType.CURRENT_WEATHER],
    ):
        user_input = EXAMPLE_USER_INPUT.copy()
        user_input[CONF_KEY_PEM] = f"{input_header}whateverkey{input_footer}"
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input,
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)

    expect(result["data"][CONF_KEY_PEM]).to_equal(EXAMPLE_CONFIG_DATA[CONF_KEY_PEM])
