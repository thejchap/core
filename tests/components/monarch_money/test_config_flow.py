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
    _mn: None = Depends(mock_network),
    _mse: AsyncMock = Depends(mock_setup_entry),
    _mca: AsyncMock = Depends(mock_config_api),
) -> None:
    """Trigger the hook executor path."""
    return None


@test
async def form_simple(
    hass: HomeAssistant = Depends(hass_fixture),
    mse: AsyncMock = Depends(mock_setup_entry),
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
    expect(len(mse.mock_calls)).to_equal(1)


@test
async def add_duplicate_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test a duplicate error config flow."""
    entry.add_to_hass(hass)

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
    hass: HomeAssistant = Depends(hass_fixture),
    mse: AsyncMock = Depends(mock_setup_entry),
    mca: AsyncMock = Depends(mock_config_api),
) -> None:
    """Test config flow with a login error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    mca.return_value.login.side_effect = LoginFailedException("Invalid Auth")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: "test-username",
            CONF_PASSWORD: "test-password",
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "invalid_auth"})

    mca.return_value.login.side_effect = None
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
    expect(len(mse.mock_calls)).to_equal(1)


@test
async def form_mfa(
    hass: HomeAssistant = Depends(hass_fixture),
    mse: AsyncMock = Depends(mock_setup_entry),
    mca: AsyncMock = Depends(mock_config_api),
) -> None:
    """Test MFA enabled on account configuration."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    mca.return_value.login.side_effect = RequireMFAException("mfa_required")

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

    mca.return_value.multi_factor_authenticate.side_effect = KeyError
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_MFA_CODE: "123456"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "bad_mfa"})
    expect(result["step_id"]).to_equal("user")

    mca.return_value.multi_factor_authenticate.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_MFA_CODE: "123456"},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Monarch Money")
    expect(result["data"]).to_equal({CONF_TOKEN: "mocked_token"})
    expect(result["result"].unique_id).to_equal("222260252323873333")
    expect(len(mse.mock_calls)).to_equal(1)
