"""Tests for the ecobee config flow."""

from unittest.mock import AsyncMock, MagicMock, patch

from pyecobee import ECOBEE_PASSWORD, ECOBEE_USERNAME
from tryke import Depends, expect, fixture, test

from homeassistant.components.ecobee.const import CONF_REFRESH_TOKEN, DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_API_KEY, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.components.ecobee._fixtures import mock_setup_entry, mock_zeroconf
from tests.hass_fixtures import hass, mock_network


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def abort_if_already_setup(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we abort if ecobee is already setup."""
    MockConfigEntry(domain=DOMAIN).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("single_instance_allowed")


@test
async def user_step_without_user_input(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test expected result if user step is called."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")


@test
async def pin_request_succeeds(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
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

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("authorize")
    expect(result["description_placeholders"]).to_equal(
        {
            "pin": "test-pin",
            "auth_url": "https://www.ecobee.com/consumerportal/index.html",
        }
    )


@test
async def pin_request_fails(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
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

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]["base"]).to_equal("pin_request_failed")


@test
async def token_request_succeeds(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
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
        expect(result["type"] is FlowResultType.FORM).to_be(True)
        expect(result["step_id"]).to_equal("authorize")

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal(DOMAIN)
    expect(result["data"]).to_equal(
        {
            CONF_API_KEY: "test-api-key",
            CONF_REFRESH_TOKEN: "test-token",
        }
    )


@test
async def token_request_fails(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
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
        expect(result["type"] is FlowResultType.FORM).to_be(True)
        expect(result["step_id"]).to_equal("authorize")

        flow_instance.request_tokens.return_value = False

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
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
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
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

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
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
        "missing_api_key",
        {
            CONF_USERNAME: "test-username@example.com",
            CONF_PASSWORD: "test-password",
        },
        "login_failed",
    ),
    test.case(
        "with_api_key",
        {
            CONF_API_KEY: "test-api-key",
            CONF_USERNAME: "test-username@example.com",
            CONF_PASSWORD: "test-password",
        },
        "invalid_auth",
    ),
)
async def password_login_error_recovers(
    first_user_input: dict,
    expected_error: str,
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
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

    expect(result["type"] is FlowResultType.FORM).to_be(True)
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

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal(DOMAIN)
    expect(result["data"]).to_equal(
        {
            CONF_USERNAME: "test-username@example.com",
            CONF_PASSWORD: "test-password",
            CONF_REFRESH_TOKEN: "test-token",
        }
    )
