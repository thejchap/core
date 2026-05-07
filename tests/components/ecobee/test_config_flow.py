"""Tryke ports of the Ecobee config flow tests."""

from unittest.mock import AsyncMock, patch

from pyecobee import ECOBEE_PASSWORD, ECOBEE_USERNAME
import requests_mock as rm_lib
from tryke import Depends, expect, fixture, test

from homeassistant.components.ecobee.const import CONF_REFRESH_TOKEN, DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_API_KEY, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_setup_entry, requests_mock_fixture

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _rm: rm_lib.Mocker = Depends(requests_mock_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Module-local fixture-resolution anchor that primes autouse fixtures."""


@test
async def abort_if_already_setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we abort if ecobee is already setup."""
    MockConfigEntry(domain=DOMAIN).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("single_instance_allowed")


@test
async def user_step_without_user_input(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test expected result if user step is called."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")


@test
async def pin_request_succeeds(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test expected result if pin request succeeds."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    with patch("homeassistant.components.ecobee.config_flow.Ecobee") as mock_ecobee:
        mock_ecobee = mock_ecobee.return_value
        mock_ecobee.request_pin.return_value = True
        mock_ecobee.pin = "test-pin"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_API_KEY: "api-key"}
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("authorize")
    expect(result["description_placeholders"]).to_equal(
        {
            "pin": "test-pin",
            "auth_url": "https://www.ecobee.com/consumerportal/index.html",
        }
    )


@test
async def pin_request_fails(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test expected result if pin request fails."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    with patch("homeassistant.components.ecobee.config_flow.Ecobee") as mock_ecobee:
        mock_ecobee = mock_ecobee.return_value
        mock_ecobee.request_pin.return_value = False

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_API_KEY: "api-key"}
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]["base"]).to_equal("pin_request_failed")


@test
async def token_request_succeeds(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test expected result if token request succeeds."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    with patch(
        "homeassistant.components.ecobee.config_flow.Ecobee"
    ) as mock_flow_ecobee:
        flow_instance = mock_flow_ecobee.return_value
        flow_instance.request_pin.return_value = True
        flow_instance.pin = "test-pin"
        flow_instance.request_tokens.return_value = True
        flow_instance.api_key = "test-api-key"
        flow_instance.refresh_token = "test-token"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_API_KEY: "api-key"}
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("authorize")

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(DOMAIN)
    expect(result["data"]).to_equal(
        {CONF_API_KEY: "test-api-key", CONF_REFRESH_TOKEN: "test-token"}
    )


@test
async def token_request_fails(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test expected result if token request fails."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    with patch(
        "homeassistant.components.ecobee.config_flow.Ecobee"
    ) as mock_flow_ecobee:
        flow_instance = mock_flow_ecobee.return_value
        flow_instance.request_pin.return_value = True
        flow_instance.pin = "test-pin"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_API_KEY: "api-key"}
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("authorize")

        flow_instance.request_tokens.return_value = False

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("authorize")
    expect(result["errors"]["base"]).to_equal("token_request_failed")
    expect(result["description_placeholders"]).to_equal(
        {
            "pin": "test-pin",
            "auth_url": "https://www.ecobee.com/consumerportal/index.html",
        }
    )


@test
async def password_login_succeeds(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test credential authentication succeeds."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    with patch(
        "homeassistant.components.ecobee.config_flow.Ecobee"
    ) as mock_flow_ecobee:
        flow_instance = mock_flow_ecobee.return_value
        flow_instance.refresh_tokens.return_value = True
        flow_instance.refresh_token = "test-token"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_USERNAME: "test-username@example.com",
                CONF_PASSWORD: "test-password",
            },
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(DOMAIN)
    expect(result["data"]).to_equal(
        {
            CONF_USERNAME: "test-username@example.com",
            CONF_PASSWORD: "test-password",
            CONF_REFRESH_TOKEN: "test-token",
        }
    )
    mock_flow_ecobee.assert_called_once_with(
        config={
            ECOBEE_USERNAME: "test-username@example.com",
            ECOBEE_PASSWORD: "test-password",
        }
    )
    flow_instance.refresh_tokens.assert_called_once_with()


@test.cases(
    test.case(
        "no_api_key",
        first_user_input={
            CONF_USERNAME: "test-username@example.com",
            CONF_PASSWORD: "test-password",
        },
        expected_error="login_failed",
    ),
    test.case(
        "with_api_key",
        first_user_input={
            CONF_API_KEY: "test-api-key",
            CONF_USERNAME: "test-username@example.com",
            CONF_PASSWORD: "test-password",
        },
        expected_error="invalid_auth",
    ),
)
async def password_login_error_recovers(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    first_user_input: dict,
    expected_error: str,
) -> None:
    """Test that authentication errors keep the user on the form and recover on retry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    with patch(
        "homeassistant.components.ecobee.config_flow.Ecobee"
    ) as mock_flow_ecobee:
        mock_flow_ecobee.return_value.refresh_tokens.return_value = False

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=first_user_input
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]["base"]).to_equal(expected_error)

    with patch(
        "homeassistant.components.ecobee.config_flow.Ecobee"
    ) as mock_flow_ecobee:
        flow_instance = mock_flow_ecobee.return_value
        flow_instance.refresh_tokens.return_value = True
        flow_instance.refresh_token = "test-token"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_USERNAME: "test-username@example.com",
                CONF_PASSWORD: "test-password",
            },
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(DOMAIN)
    expect(result["data"]).to_equal(
        {
            CONF_USERNAME: "test-username@example.com",
            CONF_PASSWORD: "test-password",
            CONF_REFRESH_TOKEN: "test-token",
        }
    )
