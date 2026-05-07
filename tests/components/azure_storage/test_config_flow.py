"""Tryke ports of the Azure Storage config flow tests."""

from unittest.mock import AsyncMock, MagicMock

from azure.core.exceptions import ClientAuthenticationError, ResourceNotFoundError
from tryke import Depends, expect, fixture, test

from homeassistant.components.azure_storage.const import (
    CONF_ACCOUNT_NAME,
    CONF_CONTAINER_NAME,
    CONF_STORAGE_ACCOUNT_KEY,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_USER, ConfigFlowResult
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import setup_integration
from ._fixtures import mock_client, mock_config_entry, mock_setup_entry
from .const import USER_INPUT

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Module-local fixture-resolution anchor."""


async def _async_start_flow(hass: HomeAssistant) -> ConfigFlowResult:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.FORM

    return await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )


@test
async def flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: MagicMock = Depends(mock_client),
    setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test config flow."""
    client.exists.return_value = False
    result = await _async_start_flow(hass)

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(
        f"{USER_INPUT[CONF_ACCOUNT_NAME]}/{USER_INPUT[CONF_CONTAINER_NAME]}"
    )
    expect(result["data"]).to_equal(
        {
            CONF_ACCOUNT_NAME: "account",
            CONF_CONTAINER_NAME: "container1",
            CONF_STORAGE_ACCOUNT_KEY: "test",
        }
    )


@test.cases(
    test.case(
        "resource_not_found",
        exception=ResourceNotFoundError,
        errors={"base": "cannot_connect"},
    ),
    test.case(
        "client_authentication",
        exception=ClientAuthenticationError,
        errors={CONF_STORAGE_ACCOUNT_KEY: "invalid_auth"},
    ),
    test.case(
        "unknown",
        exception=Exception,
        errors={"base": "unknown"},
    ),
)
async def flow_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: MagicMock = Depends(mock_client),
    setup: AsyncMock = Depends(mock_setup_entry),
    *,
    exception: type[Exception],
    errors: dict[str, str],
) -> None:
    """Test config flow errors."""
    client.exists.side_effect = exception

    result = await _async_start_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal(errors)

    client.exists.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(
        f"{USER_INPUT[CONF_ACCOUNT_NAME]}/{USER_INPUT[CONF_CONTAINER_NAME]}"
    )
    expect(result["data"]).to_equal(
        {
            CONF_ACCOUNT_NAME: "account",
            CONF_CONTAINER_NAME: "container1",
            CONF_STORAGE_ACCOUNT_KEY: "test",
        }
    )


@test
async def abort_if_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: MagicMock = Depends(mock_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test we abort if the account is already configured."""
    config_entry.add_to_hass(hass)

    result = await _async_start_flow(hass)

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def reauth_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: MagicMock = Depends(mock_client),
    setup: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test that the reauth flow works."""
    await setup_integration(hass, config_entry)

    result = await config_entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_STORAGE_ACCOUNT_KEY: "new_key"}
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(config_entry.data).to_equal(
        {
            **USER_INPUT,
            CONF_STORAGE_ACCOUNT_KEY: "new_key",
        }
    )


@test
async def reauth_flow_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: MagicMock = Depends(mock_client),
    setup: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test that the reauth flow works with an errors."""
    await setup_integration(hass, config_entry)

    client.exists.side_effect = Exception()

    result = await config_entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_STORAGE_ACCOUNT_KEY: "new_key"}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "unknown"})

    client.exists.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_STORAGE_ACCOUNT_KEY: "new_key"}
    )
    expect(result["reason"]).to_equal("reauth_successful")
    expect(config_entry.data).to_equal(
        {
            **USER_INPUT,
            CONF_STORAGE_ACCOUNT_KEY: "new_key",
        }
    )


@test
async def reconfigure_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: MagicMock = Depends(mock_client),
    setup: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test that the reconfigure flow works."""
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_CONTAINER_NAME: "new_container"}
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(config_entry.data).to_equal(
        {
            **USER_INPUT,
            CONF_CONTAINER_NAME: "new_container",
        }
    )
