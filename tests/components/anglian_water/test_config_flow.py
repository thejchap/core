"""Test the Anglian Water config flow."""

from unittest.mock import AsyncMock

from pyanglianwater.exceptions import (
    InvalidAccountIdError,
    SelfAssertedError,
    SmartMeterUnavailableError,
)
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.anglian_water.const import CONF_ACCOUNT_NUMBER, DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry, async_load_json_object_fixture
from tests.components.anglian_water._fixtures import (
    mock_anglian_water_authenticator,
    mock_anglian_water_client,
    mock_config_entry,
    mock_setup_entry,
)
from tests.hass_fixtures import hass, mock_network

from .const import ACCESS_TOKEN, ACCOUNT_NUMBER, PASSWORD, USERNAME


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def multiple_account_flow(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_anglian_water_authenticator: AsyncMock = Depends(
        mock_anglian_water_authenticator
    ),
    _mock_anglian_water_client: AsyncMock = Depends(mock_anglian_water_client),
) -> None:
    """Test the config flow when there are multiple accounts."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result is not None).to_be(True)
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD},
    )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("select_account")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_ACCOUNT_NUMBER: ACCOUNT_NUMBER},
    )

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal(ACCOUNT_NUMBER)
    expect(result["data"][CONF_USERNAME]).to_equal(USERNAME)
    expect(result["data"][CONF_PASSWORD]).to_equal(PASSWORD)
    expect(result["data"][CONF_ACCESS_TOKEN]).to_equal(ACCESS_TOKEN)
    expect(result["data"][CONF_ACCOUNT_NUMBER]).to_equal(ACCOUNT_NUMBER)
    expect(result["result"].unique_id).to_equal(ACCOUNT_NUMBER)


@test
async def single_account_flow(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_anglian_water_authenticator: AsyncMock = Depends(
        mock_anglian_water_authenticator
    ),
    mock_anglian_water_client: AsyncMock = Depends(mock_anglian_water_client),
) -> None:
    """Test the config flow when there is just a single account."""
    mock_anglian_water_client.api.get_associated_accounts.return_value = (
        await async_load_json_object_fixture(
            hass, "single_associated_accounts.json", DOMAIN
        )
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result is not None).to_be(True)
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD},
    )

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal(ACCOUNT_NUMBER)
    expect(result["data"][CONF_USERNAME]).to_equal(USERNAME)
    expect(result["data"][CONF_PASSWORD]).to_equal(PASSWORD)
    expect(result["data"][CONF_ACCESS_TOKEN]).to_equal(ACCESS_TOKEN)
    expect(result["data"][CONF_ACCOUNT_NUMBER]).to_equal(ACCOUNT_NUMBER)
    expect(result["result"].unique_id).to_equal(ACCOUNT_NUMBER)


@test
async def already_configured(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    _mock_anglian_water_authenticator: AsyncMock = Depends(
        mock_anglian_water_authenticator
    ),
    _mock_anglian_water_client: AsyncMock = Depends(mock_anglian_water_client),
) -> None:
    """Test that the flow aborts when the entry is already added."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result is not None).to_be(True)
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD},
    )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("select_account")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_ACCOUNT_NUMBER: ACCOUNT_NUMBER},
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("already_configured")


@test.cases(
    test.case("invalid_auth", SelfAssertedError, "invalid_auth"),
    test.case("unknown", ValueError, "unknown"),
)
async def auth_recover_exception(
    exception_type: type[Exception],
    expected_error: str,
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_anglian_water_authenticator: AsyncMock = Depends(
        mock_anglian_water_authenticator
    ),
    _mock_anglian_water_client: AsyncMock = Depends(mock_anglian_water_client),
) -> None:
    """Test that the flow can recover from an auth exception."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result is not None).to_be(True)
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")

    mock_anglian_water_authenticator.send_login_request.side_effect = exception_type

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD},
    )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": expected_error})

    mock_anglian_water_authenticator.send_login_request.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD},
    )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("select_account")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_ACCOUNT_NUMBER: ACCOUNT_NUMBER},
    )

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal(ACCOUNT_NUMBER)
    expect(result["data"][CONF_USERNAME]).to_equal(USERNAME)
    expect(result["data"][CONF_PASSWORD]).to_equal(PASSWORD)
    expect(result["data"][CONF_ACCESS_TOKEN]).to_equal(ACCESS_TOKEN)
    expect(result["data"][CONF_ACCOUNT_NUMBER]).to_equal(ACCOUNT_NUMBER)
    expect(result["result"].unique_id).to_equal(ACCOUNT_NUMBER)


@test.cases(
    test.case(
        "smart_meter_unavailable",
        SmartMeterUnavailableError,
        "smart_meter_unavailable",
    ),
    test.case(
        "invalid_account_id", InvalidAccountIdError, "smart_meter_unavailable"
    ),
)
async def account_recover_exception(
    exception_type: type[Exception],
    expected_error: str,
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_anglian_water_authenticator: AsyncMock = Depends(
        mock_anglian_water_authenticator
    ),
    mock_anglian_water_client: AsyncMock = Depends(mock_anglian_water_client),
) -> None:
    """Test that the flow can recover from an account related exception."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result is not None).to_be(True)
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD},
    )

    mock_anglian_water_client.validate_smart_meter.side_effect = exception_type

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("select_account")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_ACCOUNT_NUMBER: ACCOUNT_NUMBER},
    )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("select_account")
    expect(result["errors"]).to_equal({"base": expected_error})

    mock_anglian_water_client.validate_smart_meter.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_ACCOUNT_NUMBER: ACCOUNT_NUMBER},
    )

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal(ACCOUNT_NUMBER)
    expect(result["data"][CONF_USERNAME]).to_equal(USERNAME)
    expect(result["data"][CONF_PASSWORD]).to_equal(PASSWORD)
    expect(result["data"][CONF_ACCESS_TOKEN]).to_equal(ACCESS_TOKEN)
    expect(result["data"][CONF_ACCOUNT_NUMBER]).to_equal(ACCOUNT_NUMBER)
    expect(result["result"].unique_id).to_equal(ACCOUNT_NUMBER)
