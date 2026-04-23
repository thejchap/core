"""Test the configuration flow for MyNeomitis integration."""

from unittest.mock import AsyncMock

from aiohttp import ClientConnectionError, ClientError, ClientResponseError, RequestInfo
from tryke import Depends, expect, fixture, test
from yarl import URL

from homeassistant.components.myneomitis.const import CONF_USER_ID, DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_config_entry, mock_pyaxenco_client, mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "password123"


@fixture
def _trigger_executor(
    _mn: None = Depends(mock_network),
    _mpc: AsyncMock = Depends(mock_pyaxenco_client),
    _mse: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Trigger the hook executor path."""
    return None


def _make_client_response_error(status: int) -> ClientResponseError:
    """Create a mock ClientResponseError with the given status code."""
    request_info = RequestInfo(
        url=URL("https://api.fake"),
        method="POST",
        headers={},
        real_url=URL("https://api.fake"),
    )
    return ClientResponseError(
        request_info=request_info,
        history=(),
        status=status,
        message="error",
        headers=None,
    )


@test
async def user_flow_success(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test successful user flow for MyNeomitis integration."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_EMAIL: TEST_EMAIL, CONF_PASSWORD: TEST_PASSWORD},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(f"MyNeomitis ({TEST_EMAIL})")
    expect(result["data"]).to_equal(
        {
            CONF_EMAIL: TEST_EMAIL,
            CONF_PASSWORD: TEST_PASSWORD,
            CONF_USER_ID: "user-123",
        }
    )
    expect(result["result"].unique_id).to_equal("user-123")


@test.cases(
    test.case("cannot_connect", ClientConnectionError(), "cannot_connect"),
    test.case("invalid_auth", _make_client_response_error(401), "invalid_auth"),
    test.case("unknown_403", _make_client_response_error(403), "unknown"),
    test.case("cannot_connect_500", _make_client_response_error(500), "cannot_connect"),
    test.case("client_error", ClientError("Network error"), "unknown"),
    test.case("runtime_error", RuntimeError("boom"), "unknown"),
)
async def flow_errors(
    side_effect: Exception,
    expected_error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_pyaxenco_client: AsyncMock = Depends(mock_pyaxenco_client),
) -> None:
    """Test flow errors and recovery to CREATE_ENTRY."""
    mock_pyaxenco_client.login.side_effect = side_effect

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_EMAIL: TEST_EMAIL, CONF_PASSWORD: TEST_PASSWORD},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]["base"]).to_equal(expected_error)

    mock_pyaxenco_client.login.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_EMAIL: TEST_EMAIL, CONF_PASSWORD: TEST_PASSWORD},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def abort_if_already_configured(
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test abort when an entry for the same user_id already exists."""
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_EMAIL: TEST_EMAIL, CONF_PASSWORD: TEST_PASSWORD},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
