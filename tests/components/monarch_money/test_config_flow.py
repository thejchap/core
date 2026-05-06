"""Test the Monarch Money config flow."""

from unittest.mock import AsyncMock

from monarchmoney import LoginFailedException, RequireMFAException
from tryke import Depends, expect, fixture, test

from homeassistant.components.monarch_money.const import CONF_MFA_CODE, DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, CONF_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_config_api, mock_config_entry, mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def form_simple(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    config_api: AsyncMock = Depends(mock_config_api),
) -> None:
    """Test simple case (no MFA / no errors)."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: "test-username",
            CONF_PASSWORD: "test-password",
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Monarch Money")
    expect(result["data"]).to_equal({CONF_TOKEN: "mocked_token"})
    expect(result["result"].unique_id).to_equal("222260252323873333")
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def add_duplicate_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    config_api: AsyncMock = Depends(mock_config_api),
) -> None:
    """Test a duplicate error config flow."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: "test-username",
            CONF_PASSWORD: "test-password",
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def form_invalid_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    config_api: AsyncMock = Depends(mock_config_api),
) -> None:
    """Test config flow with a login error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    # Change the login mock to raise an MFA required error
    config_api.return_value.login.side_effect = LoginFailedException("Invalid Auth")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: "test-username",
            CONF_PASSWORD: "test-password",
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "invalid_auth"})

    config_api.return_value.login.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: "test-username",
            CONF_PASSWORD: "test-password",
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Monarch Money")
    expect(result["data"]).to_equal({CONF_TOKEN: "mocked_token"})
    expect(result["context"]["unique_id"]).to_equal("222260252323873333")
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def form_mfa(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    config_api: AsyncMock = Depends(mock_config_api),
) -> None:
    """Test MFA enabled on account configuration."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    # Change the login mock to raise an MFA required error
    config_api.return_value.login.side_effect = RequireMFAException("mfa_required")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: "test-username",
            CONF_PASSWORD: "test-password",
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "mfa_required"})
    expect(result["step_id"]).to_equal("user")

    # Add a bad MFA Code response
    config_api.return_value.multi_factor_authenticate.side_effect = KeyError
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_MFA_CODE: "123456",
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "bad_mfa"})
    expect(result["step_id"]).to_equal("user")

    # Use a good MFA Code - Clear mock
    config_api.return_value.multi_factor_authenticate.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_MFA_CODE: "123456",
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Monarch Money")
    expect(result["data"]).to_equal({CONF_TOKEN: "mocked_token"})
    expect(result["result"].unique_id).to_equal("222260252323873333")

    expect(len(setup_entry.mock_calls)).to_equal(1)
