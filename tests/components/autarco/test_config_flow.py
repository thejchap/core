"""Test the Autarco config flow."""

from unittest.mock import AsyncMock, patch

from autarco import AutarcoAuthenticationError, AutarcoConnectionError
from tryke import Depends, expect, fixture, test

from homeassistant.components.autarco.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.components.autarco._fixtures import (
    mock_autarco_client,
    mock_config_entry,
    mock_setup_entry,
)
from tests.hass_fixtures import hass, mock_network


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def full_user_flow(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_autarco_client: AsyncMock = Depends(mock_autarco_client),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test the full user configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result.get("type") is FlowResultType.FORM).to_be(True)
    expect(result.get("step_id")).to_equal("user")
    expect(not result.get("errors")).to_be(True)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_EMAIL: "test@autarco.com", CONF_PASSWORD: "test-password"},
    )

    expect(result.get("type") is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result.get("title")).to_equal("test@autarco.com")
    expect(result.get("data")).to_equal(
        {
            CONF_EMAIL: "test@autarco.com",
            CONF_PASSWORD: "test-password",
        }
    )
    expect(len(mock_autarco_client.get_account.mock_calls)).to_equal(1)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def duplicate_entry(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    _mock_autarco_client: AsyncMock = Depends(mock_autarco_client),
) -> None:
    """Test abort when setting up duplicate entry."""
    mock_config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result.get("type") is FlowResultType.FORM).to_be(True)
    expect(not result.get("errors")).to_be(True)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_EMAIL: "test@autarco.com", CONF_PASSWORD: "test-password"},
    )

    expect(result.get("type") is FlowResultType.ABORT).to_be(True)
    expect(result.get("reason")).to_equal("already_configured")


@test.cases(
    test.case("connection_error", AutarcoConnectionError, "cannot_connect"),
    test.case("auth_error", AutarcoAuthenticationError, "invalid_auth"),
)
async def exceptions(
    exception: type[Exception],
    error: str,
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_autarco_client: AsyncMock = Depends(mock_autarco_client),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test exceptions."""
    mock_autarco_client.get_account.side_effect = exception
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_EMAIL: "test@autarco.com", CONF_PASSWORD: "test-password"},
    )
    expect(result.get("type") is FlowResultType.FORM).to_be(True)
    expect(result.get("errors")).to_equal({"base": error})

    mock_autarco_client.get_account.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_EMAIL: "test@autarco.com", CONF_PASSWORD: "test-password"},
    )
    expect(result.get("type") is FlowResultType.CREATE_ENTRY).to_be(True)


@test
async def step_reauth(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test reauth flow."""
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reauth_flow(hass)

    expect(result.get("type") is FlowResultType.FORM).to_be(True)
    expect(result.get("step_id")).to_equal("reauth_confirm")

    with patch("homeassistant.components.autarco.config_flow.Autarco", autospec=True):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_PASSWORD: "new-password"},
        )

    expect(result.get("type") is FlowResultType.ABORT).to_be(True)
    expect(result.get("reason")).to_equal("reauth_successful")

    expect(len(hass.config_entries.async_entries())).to_equal(1)
    expect(mock_config_entry.data[CONF_PASSWORD]).to_equal("new-password")


@test.cases(
    test.case("connection_error", AutarcoConnectionError, "cannot_connect"),
    test.case("auth_error", AutarcoAuthenticationError, "invalid_auth"),
)
async def step_reauth_exceptions(
    exception: type[Exception],
    error: str,
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_autarco_client: AsyncMock = Depends(mock_autarco_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test exceptions in reauth flow."""
    mock_autarco_client.get_account.side_effect = exception
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reauth_flow(hass)

    expect(result.get("type") is FlowResultType.FORM).to_be(True)
    expect(result.get("step_id")).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_PASSWORD: "new-password"},
    )
    expect(result.get("type") is FlowResultType.FORM).to_be(True)
    expect(result.get("errors")).to_equal({"base": error})

    mock_autarco_client.get_account.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_PASSWORD: "new-password"},
    )
    expect(result.get("type") is FlowResultType.ABORT).to_be(True)
    expect(result.get("reason")).to_equal("reauth_successful")

    expect(len(hass.config_entries.async_entries())).to_equal(1)
    expect(mock_config_entry.data[CONF_PASSWORD]).to_equal("new-password")
