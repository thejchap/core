"""Test the Fibaro config flow."""

from unittest.mock import AsyncMock, Mock

from pyfibaro.fibaro_client import FibaroAuthenticationFailed, FibaroConnectFailed
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.fibaro import DOMAIN
from homeassistant.components.fibaro.config_flow import _normalize_url
from homeassistant.components.fibaro.const import CONF_IMPORT_PLUGINS
from homeassistant.const import CONF_PASSWORD, CONF_URL, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult, FlowResultType

from tests.common import MockConfigEntry
from tests.components.fibaro._fixtures import (
    TEST_NAME,
    TEST_PASSWORD,
    TEST_URL,
    TEST_USERNAME,
    mock_config_entry,
    mock_fibaro_client,
    mock_setup_entry,
)
from tests.hass_fixtures import hass as hass_fixture


@fixture
def _trigger_executor() -> None:
    """Trigger the hook executor path."""
    return None


async def _recovery_after_failure_works(
    hass: HomeAssistant, mock_fibaro_client: Mock, result: FlowResult
) -> None:
    mock_fibaro_client.connect_with_credentials.side_effect = None
    mock_fibaro_client.connect_with_credentials.return_value = (
        mock_fibaro_client.read_info()
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_URL: TEST_URL,
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(TEST_NAME)
    expect(result["data"]).to_equal(
        {
            CONF_URL: TEST_URL,
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
            CONF_IMPORT_PLUGINS: False,
        }
    )


async def _recovery_after_reauth_failure_works(
    hass: HomeAssistant, mock_fibaro_client: Mock, result: FlowResult
) -> None:
    mock_fibaro_client.connect_with_credentials.side_effect = None
    mock_fibaro_client.connect_with_credentials.return_value = (
        mock_fibaro_client.read_info()
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_PASSWORD: "other_fake_password"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")


@test
async def config_flow_user_initiated_success(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_fibaro_client: Mock = Depends(mock_fibaro_client),
) -> None:
    """Successful flow manually initialized by the user."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_URL: TEST_URL,
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(TEST_NAME)
    expect(result["data"]).to_equal(
        {
            CONF_URL: TEST_URL,
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
            CONF_IMPORT_PLUGINS: False,
        }
    )


@test
async def config_flow_user_initiated_auth_failure(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_fibaro_client: Mock = Depends(mock_fibaro_client),
) -> None:
    """Authentication failure in flow manually initialized by the user."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    mock_fibaro_client.connect_with_credentials.side_effect = (
        FibaroAuthenticationFailed()
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_URL: TEST_URL,
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "invalid_auth"})

    await _recovery_after_failure_works(hass, mock_fibaro_client, result)


@test
async def config_flow_user_initiated_connect_failure(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_fibaro_client: Mock = Depends(mock_fibaro_client),
) -> None:
    """Unknown failure in flow manually initialized by the user."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    mock_fibaro_client.connect_with_credentials.side_effect = FibaroConnectFailed()

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_URL: TEST_URL,
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "cannot_connect"})

    await _recovery_after_failure_works(hass, mock_fibaro_client, result)


@test
async def reauth_success(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_fibaro_client: Mock = Depends(mock_fibaro_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Successful reauth flow initialized by the user."""
    result = await mock_config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_PASSWORD: "other_fake_password"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")


@test
async def reauth_connect_failure(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_fibaro_client: Mock = Depends(mock_fibaro_client),
) -> None:
    """Reauth flow with connect failure."""
    result = await mock_config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["errors"]).to_equal({})

    mock_fibaro_client.connect_with_credentials.side_effect = FibaroConnectFailed()

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_PASSWORD: "other_fake_password"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["errors"]).to_equal({"base": "cannot_connect"})

    await _recovery_after_reauth_failure_works(hass, mock_fibaro_client, result)


@test
async def reauth_auth_failure(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_fibaro_client: Mock = Depends(mock_fibaro_client),
) -> None:
    """Reauth flow with auth failure."""
    result = await mock_config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["errors"]).to_equal({})

    mock_fibaro_client.connect_with_credentials.side_effect = (
        FibaroAuthenticationFailed()
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_PASSWORD: "other_fake_password"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["errors"]).to_equal({"base": "invalid_auth"})

    await _recovery_after_reauth_failure_works(hass, mock_fibaro_client, result)


@test.cases(
    test.case("api_slash", url_path="/api/"),
    test.case("api_no_slash", url_path="/api"),
    test.case("just_slash", url_path="/"),
    test.case("empty", url_path=""),
)
async def normalize_url(url_path: str) -> None:
    """Test that the url is normalized for different entered values."""
    expect(_normalize_url(f"http://192.168.1.1{url_path}")).to_equal(
        "http://192.168.1.1/api/"
    )
