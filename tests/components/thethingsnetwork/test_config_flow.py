"""Define tests for the The Things Network config flows."""

from unittest.mock import MagicMock

from tryke import Depends, expect, fixture, test
from ttn_client import TTNAuthError

from homeassistant.components.thethingsnetwork.const import CONF_APP_ID, DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_API_KEY, CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import init_integration
from ._fixtures import API_KEY, APP_ID, HOST, mock_config_entry, mock_ttnclient

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

USER_DATA = {CONF_HOST: HOST, CONF_APP_ID: APP_ID, CONF_API_KEY: API_KEY}


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def user(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _ttnclient: MagicMock = Depends(mock_ttnclient),
) -> None:
    """Test user config."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data=USER_DATA,
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(APP_ID)
    expect(result["data"][CONF_HOST]).to_equal(HOST)
    expect(result["data"][CONF_APP_ID]).to_equal(APP_ID)
    expect(result["data"][CONF_API_KEY]).to_equal(API_KEY)


@test.cases(
    test.case(
        "auth_error", fetch_data_exception=TTNAuthError, base_error="invalid_auth"
    ),
    test.case("unknown", fetch_data_exception=Exception, base_error="unknown"),
)
async def user_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ttnclient: MagicMock = Depends(mock_ttnclient),
    *,
    fetch_data_exception: type[Exception],
    base_error: str,
) -> None:
    """Test user config errors."""

    # Test error
    ttnclient.return_value.fetch_data.side_effect = fetch_data_exception
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data=USER_DATA,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(base_error in result["errors"]["base"]).to_be(True)

    # Recover
    ttnclient.return_value.fetch_data.side_effect = None
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data=USER_DATA,
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def duplicate_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _ttnclient: MagicMock = Depends(mock_ttnclient),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test that duplicate entries are caught."""

    await init_integration(hass, config_entry)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data=USER_DATA,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def step_reauth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _ttnclient: MagicMock = Depends(mock_ttnclient),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test that the reauth step works."""

    await init_integration(hass, config_entry)

    result = await config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(bool(result["errors"])).to_be(False)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(bool(result["errors"])).to_be(False)

    new_api_key = "1234"
    new_user_input = dict(USER_DATA)
    new_user_input[CONF_API_KEY] = new_api_key

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=new_user_input
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")

    expect(len(hass.config_entries.async_entries())).to_equal(1)
    expect(hass.config_entries.async_entries()[0].data[CONF_API_KEY]).to_equal(
        new_api_key
    )
