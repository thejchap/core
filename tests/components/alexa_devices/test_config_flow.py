"""Tests for the Alexa Devices config flow."""

from unittest.mock import AsyncMock, MagicMock

from aioamazondevices.exceptions import (
    CannotAuthenticate,
    CannotConnect,
    CannotRetrieveData,
)
from tryke import Depends, expect, fixture, test

from homeassistant.components.alexa_devices.const import (
    CONF_LOGIN_DATA,
    CONF_SITE,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_CODE, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from .const import TEST_CODE, TEST_PASSWORD, TEST_USERNAME

from tests.common import MockConfigEntry
from tests.components.alexa_devices._fixtures import (
    mock_amazon_devices_client,
    mock_config_entry,
    mock_setup_entry,
    mock_zeroconf,
)
from tests.hass_fixtures import hass, mock_network


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def full_flow(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    mock_amazon_devices_client: AsyncMock = Depends(mock_amazon_devices_client),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test full flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
            CONF_CODE: TEST_CODE,
        },
    )
    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal(TEST_USERNAME)
    expect(result["data"]).to_equal(
        {
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
            CONF_LOGIN_DATA: {
                "customer_info": {"user_id": TEST_USERNAME},
                CONF_SITE: "https://www.amazon.com",
            },
        }
    )
    expect(result["result"].unique_id).to_equal(TEST_USERNAME)
    mock_amazon_devices_client.login.login_mode_interactive.assert_called_once_with(
        "023123"
    )


@test.cases(
    test.case("cannot_connect", CannotConnect, "cannot_connect"),
    test.case("invalid_auth", CannotAuthenticate, "invalid_auth"),
    test.case("cannot_retrieve_data", CannotRetrieveData, "cannot_retrieve_data"),
)
async def flow_errors(
    exception: type[Exception],
    error: str,
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    mock_amazon_devices_client: AsyncMock = Depends(mock_amazon_devices_client),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test flow errors."""
    mock_amazon_devices_client.login.login_mode_interactive.side_effect = exception

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
            CONF_CODE: TEST_CODE,
        },
    )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_equal({"base": error})

    mock_amazon_devices_client.login.login_mode_interactive.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
            CONF_CODE: TEST_CODE,
        },
    )
    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)


@test
async def already_configured(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    _mock_amazon_devices_client: AsyncMock = Depends(mock_amazon_devices_client),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test duplicate flow."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
            CONF_CODE: TEST_CODE,
        },
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("already_configured")


@test
async def reauth_successful(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    _mock_amazon_devices_client: AsyncMock = Depends(mock_amazon_devices_client),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test starting a reauthentication flow."""
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reauth_flow(hass)
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_PASSWORD: "other_fake_password",
            CONF_CODE: "000000",
        },
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("reauth_successful")

    expect(mock_config_entry.data).to_equal(
        {
            CONF_CODE: "000000",
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: "other_fake_password",
            CONF_LOGIN_DATA: {
                "customer_info": {"user_id": TEST_USERNAME},
                CONF_SITE: "https://www.amazon.com",
            },
        }
    )


@test.cases(
    test.case("cannot_connect", CannotConnect, "cannot_connect"),
    test.case("invalid_auth", CannotAuthenticate, "invalid_auth"),
    test.case("cannot_retrieve_data", CannotRetrieveData, "cannot_retrieve_data"),
)
async def reauth_not_successful(
    side_effect: type[Exception],
    error: str,
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    mock_amazon_devices_client: AsyncMock = Depends(mock_amazon_devices_client),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test starting a reauthentication flow but no connection found."""
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reauth_flow(hass)
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("reauth_confirm")

    mock_amazon_devices_client.login.login_mode_interactive.side_effect = side_effect
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_PASSWORD: "other_fake_password",
            CONF_CODE: "000000",
        },
    )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["errors"]).to_equal({"base": error})

    mock_amazon_devices_client.login.login_mode_interactive.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_PASSWORD: "fake_password",
            CONF_CODE: "111111",
        },
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(mock_config_entry.data).to_equal(
        {
            CONF_CODE: "111111",
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: "fake_password",
            CONF_LOGIN_DATA: {
                "customer_info": {"user_id": TEST_USERNAME},
                CONF_SITE: "https://www.amazon.com",
            },
        }
    )


@test
async def reconfigure_successful(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    _mock_amazon_devices_client: AsyncMock = Depends(mock_amazon_devices_client),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test that the entry can be reconfigured."""
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reconfigure_flow(hass)

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("reconfigure")

    expect(mock_config_entry.data[CONF_USERNAME]).to_equal(TEST_USERNAME)

    new_password = "new_fake_password"

    reconfigure_result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_PASSWORD: new_password,
            CONF_CODE: TEST_CODE,
        },
    )

    expect(reconfigure_result["type"] is FlowResultType.ABORT).to_be(True)
    expect(reconfigure_result["reason"]).to_equal("reconfigure_successful")

    expect(mock_config_entry.data).to_equal(
        {
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: new_password,
            CONF_LOGIN_DATA: {
                "customer_info": {"user_id": TEST_USERNAME},
                CONF_SITE: "https://www.amazon.com",
            },
        }
    )


@test.cases(
    test.case("cannot_connect", CannotConnect, "cannot_connect"),
    test.case("invalid_auth", CannotAuthenticate, "invalid_auth"),
    test.case("cannot_retrieve_data", CannotRetrieveData, "cannot_retrieve_data"),
)
async def reconfigure_fails(
    side_effect: type[Exception],
    error: str,
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    mock_amazon_devices_client: AsyncMock = Depends(mock_amazon_devices_client),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test that the host can be reconfigured."""
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reconfigure_flow(hass)

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("reconfigure")

    mock_amazon_devices_client.login.login_mode_interactive.side_effect = side_effect

    reconfigure_result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_PASSWORD: TEST_PASSWORD,
            CONF_CODE: TEST_CODE,
        },
    )

    expect(reconfigure_result["type"] is FlowResultType.FORM).to_be(True)
    expect(reconfigure_result["step_id"]).to_equal("reconfigure")
    expect(reconfigure_result["errors"]).to_equal({"base": error})

    mock_amazon_devices_client.login.login_mode_interactive.side_effect = None

    reconfigure_result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_PASSWORD: TEST_PASSWORD,
            CONF_CODE: TEST_CODE,
        },
    )

    expect(reconfigure_result["type"] is FlowResultType.ABORT).to_be(True)
    expect(reconfigure_result["reason"]).to_equal("reconfigure_successful")
    expect(mock_config_entry.data).to_equal(
        {
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
            CONF_LOGIN_DATA: {
                "customer_info": {"user_id": TEST_USERNAME},
                CONF_SITE: "https://www.amazon.com",
            },
        }
    )
