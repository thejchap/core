"""Test the AirPatrol config flow."""

from unittest.mock import patch

from airpatrol.api import AirPatrolAPI, AirPatrolAuthenticationError, AirPatrolError
from tryke import Depends, expect, fixture, test

from homeassistant.components.airpatrol.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.components.airpatrol._fixtures import get_client, mock_config_entry
from tests.hass_fixtures import hass, mock_network

TEST_USER_INPUT = {
    CONF_EMAIL: "test@example.com",
    CONF_PASSWORD: "test_password",
}


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def user_flow_success(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _get_client: AirPatrolAPI = Depends(get_client),
) -> None:
    """Test successful user flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=TEST_USER_INPUT
    )

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal(TEST_USER_INPUT[CONF_EMAIL])
    expect(result["data"]).to_equal(
        {
            **TEST_USER_INPUT,
            CONF_ACCESS_TOKEN: "test_access_token",
        }
    )
    expect(result["result"].unique_id).to_equal("test_user_id")


@test
async def async_step_reauth_confirm_success(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    _get_client: AirPatrolAPI = Depends(get_client),
) -> None:
    """Test successful reauthentication via async_step_reauth_confirm."""
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reauth_flow(hass)

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=TEST_USER_INPUT
    )
    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("reauth_successful")

    expect(mock_config_entry.data[CONF_PASSWORD]).to_equal("test_password")
    expect(mock_config_entry.data[CONF_ACCESS_TOKEN]).to_equal("test_access_token")


@test
async def async_step_reauth_confirm_invalid_auth(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    _get_client: AirPatrolAPI = Depends(get_client),
) -> None:
    """Test reauthentication failure due to invalid credentials."""
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reauth_flow(hass)
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("reauth_confirm")

    with patch(
        "homeassistant.components.airpatrol.config_flow.AirPatrolAPI.authenticate",
        side_effect=AirPatrolAuthenticationError("fail"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=TEST_USER_INPUT
        )
        expect(result["type"] is FlowResultType.FORM).to_be(True)
        expect(result["step_id"]).to_equal("reauth_confirm")
        expect(result["errors"]).to_equal({"base": "invalid_auth"})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=TEST_USER_INPUT,
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(mock_config_entry.data[CONF_PASSWORD]).to_equal("test_password")
    expect(mock_config_entry.data[CONF_ACCESS_TOKEN]).to_equal("test_access_token")


@test
async def async_step_reauth_confirm_another_account_failure(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    get_client: AirPatrolAPI = Depends(get_client),
) -> None:
    """Test reauthentication failure due to another account."""
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reauth_flow(hass)
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("reauth_confirm")

    get_client.get_unique_id.return_value = "different_user_id"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_EMAIL: "test2@example.com", CONF_PASSWORD: "test_password2"},
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("unique_id_mismatch")


@test.cases(
    test.case("cannot_connect", AirPatrolError("fail"), "cannot_connect"),
    test.case("invalid_auth", AirPatrolAuthenticationError("fail"), "invalid_auth"),
)
async def user_flow_error(
    side_effect: Exception,
    expected_error: str,
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _get_client: AirPatrolAPI = Depends(get_client),
) -> None:
    """Test user flow with invalid authentication."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")

    with patch(
        "homeassistant.components.airpatrol.config_flow.AirPatrolAPI.authenticate",
        side_effect=side_effect,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=TEST_USER_INPUT
        )

        expect(result["type"] is FlowResultType.FORM).to_be(True)
        expect(result["errors"]).to_equal({"base": expected_error})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=TEST_USER_INPUT
    )

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal(TEST_USER_INPUT[CONF_EMAIL])
    expect(result["data"]).to_equal(
        {
            **TEST_USER_INPUT,
            CONF_ACCESS_TOKEN: "test_access_token",
        }
    )
    expect(result["result"].unique_id).to_equal("test_user_id")


@test
async def user_flow_already_configured(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _get_client: AirPatrolAPI = Depends(get_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test user flow when already configured."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=TEST_USER_INPUT
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("already_configured")
