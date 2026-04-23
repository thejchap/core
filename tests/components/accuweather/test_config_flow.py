"""Define tests for the AccuWeather config flow."""

from unittest.mock import AsyncMock

from accuweather import ApiError, InvalidApiKeyError, RequestsExceededError
from tryke import Depends, expect, fixture, test

from homeassistant.components.accuweather.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_API_KEY, CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.components.accuweather._fixtures import mock_accuweather_client
from tests.hass_fixtures import hass, mock_network

from . import init_integration


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


VALID_CONFIG = {
    CONF_NAME: "abcd",
    CONF_API_KEY: "32-character-string-1234567890qw",
    CONF_LATITUDE: 55.55,
    CONF_LONGITUDE: 122.12,
}


@test
async def show_form(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
) -> None:
    """Test that the form is served with no input."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")


@test
async def invalid_api_key(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_accuweather_client: AsyncMock = Depends(mock_accuweather_client),
) -> None:
    """Test that errors are shown when API key is invalid."""
    mock_accuweather_client.async_get_location.side_effect = InvalidApiKeyError(
        "Invalid API key"
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data=VALID_CONFIG,
    )

    expect(result["errors"]).to_equal({CONF_API_KEY: "invalid_api_key"})


@test
async def api_error(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_accuweather_client: AsyncMock = Depends(mock_accuweather_client),
) -> None:
    """Test API error."""
    mock_accuweather_client.async_get_location.side_effect = ApiError(
        "Invalid response from AccuWeather API"
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data=VALID_CONFIG,
    )

    expect(result["errors"]).to_equal({"base": "cannot_connect"})


@test
async def requests_exceeded_error(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_accuweather_client: AsyncMock = Depends(mock_accuweather_client),
) -> None:
    """Test requests exceeded error."""
    mock_accuweather_client.async_get_location.side_effect = RequestsExceededError(
        "The allowed number of requests has been exceeded"
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data=VALID_CONFIG,
    )

    expect(result["errors"]).to_equal({CONF_API_KEY: "requests_exceeded"})


@test
async def integration_already_exists(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_accuweather_client: AsyncMock = Depends(mock_accuweather_client),
) -> None:
    """Test we only allow a single config flow."""
    MockConfigEntry(
        domain=DOMAIN,
        unique_id="0123456",
        data=VALID_CONFIG,
    ).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data=VALID_CONFIG,
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("already_configured")


@test
async def create_entry(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_accuweather_client: AsyncMock = Depends(mock_accuweather_client),
) -> None:
    """Test that the user step works."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data=VALID_CONFIG,
    )

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal("abcd")
    expect(result["data"][CONF_NAME]).to_equal("abcd")
    expect(result["data"][CONF_LATITUDE]).to_equal(55.55)
    expect(result["data"][CONF_LONGITUDE]).to_equal(122.12)
    expect(result["data"][CONF_API_KEY]).to_equal("32-character-string-1234567890qw")


@test
async def reauth_successful(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_accuweather_client: AsyncMock = Depends(mock_accuweather_client),
) -> None:
    """Test starting a reauthentication flow."""
    mock_config_entry = await init_integration(hass)

    result = await mock_config_entry.start_reauth_flow(hass)
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_API_KEY: "new_api_key"},
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(mock_config_entry.data[CONF_API_KEY]).to_equal("new_api_key")


@test.cases(
    test.case("api_error", ApiError("API Error"), "cannot_connect"),
    test.case(
        "invalid_api_key", InvalidApiKeyError("Invalid API Key"), "invalid_api_key"
    ),
    test.case("timeout", TimeoutError(), "cannot_connect"),
    test.case(
        "requests_exceeded",
        RequestsExceededError("Requests Exceeded"),
        "requests_exceeded",
    ),
)
async def reauth_errors(
    exc: Exception,
    base_error: str,
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_accuweather_client: AsyncMock = Depends(mock_accuweather_client),
) -> None:
    """Test reauthentication flow with errors."""
    mock_config_entry = await init_integration(hass)

    result = await mock_config_entry.start_reauth_flow(hass)
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("reauth_confirm")

    mock_accuweather_client.async_get_location.side_effect = exc
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_API_KEY: "new_api_key"},
    )

    expect(result["errors"]).to_equal({"base": base_error})

    mock_accuweather_client.async_get_location.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_API_KEY: "new_api_key"},
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(mock_config_entry.data[CONF_API_KEY]).to_equal("new_api_key")
