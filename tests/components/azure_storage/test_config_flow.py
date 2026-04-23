"""Test the Azure storage config flow."""

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

from tests.common import MockConfigEntry
from tests.components.azure_storage._fixtures import (
    mock_client,
    mock_config_entry,
    mock_setup_entry,
)
from tests.hass_fixtures import hass, mock_network

from . import setup_integration
from .const import USER_INPUT


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


async def _start_flow(hass: HomeAssistant) -> ConfigFlowResult:
    """Initialize the config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    await hass.async_block_till_done()
    expect(result["type"] is FlowResultType.FORM).to_be(True)

    return await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )


@test
async def flow(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_client: MagicMock = Depends(mock_client),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test config flow."""
    mock_client.exists.return_value = False
    result = await _start_flow(hass)

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
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
    test.case("not_found", ResourceNotFoundError, {"base": "cannot_connect"}),
    test.case(
        "auth_error",
        ClientAuthenticationError,
        {CONF_STORAGE_ACCOUNT_KEY: "invalid_auth"},
    ),
    test.case("unknown", Exception, {"base": "unknown"}),
)
async def flow_errors(
    exception: type[Exception],
    errors: dict[str, str],
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_client: MagicMock = Depends(mock_client),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test config flow errors."""
    mock_client.exists.side_effect = exception

    result = await _start_flow(hass)

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_equal(errors)

    mock_client.exists.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )
    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
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
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_client: MagicMock = Depends(mock_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test we abort if the account is already configured."""
    mock_config_entry.add_to_hass(hass)

    result = await _start_flow(hass)

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("already_configured")


@test
async def reauth_flow(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_client: MagicMock = Depends(mock_client),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test that the reauth flow works."""
    await setup_integration(hass, mock_config_entry)

    result = await mock_config_entry.start_reauth_flow(hass)

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_STORAGE_ACCOUNT_KEY: "new_key"}
    )
    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(mock_config_entry.data).to_equal(
        {**USER_INPUT, CONF_STORAGE_ACCOUNT_KEY: "new_key"}
    )


@test
async def reauth_flow_errors(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_client: MagicMock = Depends(mock_client),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test that the reauth flow works with errors."""
    await setup_integration(hass, mock_config_entry)

    mock_client.exists.side_effect = Exception()

    result = await mock_config_entry.start_reauth_flow(hass)

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_STORAGE_ACCOUNT_KEY: "new_key"}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_equal({"base": "unknown"})

    mock_client.exists.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_STORAGE_ACCOUNT_KEY: "new_key"}
    )
    expect(result["reason"]).to_equal("reauth_successful")
    expect(mock_config_entry.data).to_equal(
        {**USER_INPUT, CONF_STORAGE_ACCOUNT_KEY: "new_key"}
    )


@test
async def reconfigure_flow(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_client: MagicMock = Depends(mock_client),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test that the reconfigure flow works."""
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reconfigure_flow(hass)

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("reconfigure")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_CONTAINER_NAME: "new_container"}
    )
    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(mock_config_entry.data).to_equal(
        {**USER_INPUT, CONF_CONTAINER_NAME: "new_container"}
    )
