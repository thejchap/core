"""Test the Whirlpool Sixth Sense config flow."""

from unittest.mock import MagicMock

import aiohttp
from tryke import Depends, expect, fixture, test
from whirlpool.auth import AccountLockedError
from whirlpool.backendselector import Brand, Region

from homeassistant import config_entries
from homeassistant.components.whirlpool.const import CONF_BRAND, DOMAIN
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_PASSWORD, CONF_REGION, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    DEFAULT_BRAND,
    DEFAULT_REGION,
    mock_appliances_manager_api,
    mock_auth_api,
    mock_backend_selector_api,
    mock_whirlpool_setup_entry,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

CONFIG_INPUT = {
    CONF_USERNAME: "test-username",
    CONF_PASSWORD: "test-password",
}


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


def _assert_successful_user_flow(
    setup_entry_mock: MagicMock,
    result: ConfigFlowResult,
    region: str,
    brand: str,
) -> None:
    """Assert that the flow was successful."""
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("test-username")
    expect(result["data"]).to_equal(
        {
            CONF_USERNAME: CONFIG_INPUT[CONF_USERNAME],
            CONF_PASSWORD: CONFIG_INPUT[CONF_PASSWORD],
            CONF_REGION: region,
            CONF_BRAND: brand,
        }
    )
    expect(result["result"].unique_id).to_equal(CONFIG_INPUT[CONF_USERNAME])
    expect(len(setup_entry_mock.mock_calls)).to_equal(1)


def _assert_successful_reauth_flow(
    mock_entry: MockConfigEntry,
    result: ConfigFlowResult,
    region: tuple[str, Region],
    brand: tuple[str, Brand],
) -> None:
    """Assert that the reauth flow was successful."""
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(mock_entry.data).to_equal(
        {
            CONF_USERNAME: CONFIG_INPUT[CONF_USERNAME],
            CONF_PASSWORD: "new-password",
            CONF_REGION: region[0],
            CONF_BRAND: brand[0],
        }
    )


@test
async def user_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _auth: MagicMock = Depends(mock_auth_api),
    _appliances: MagicMock = Depends(mock_appliances_manager_api),
    backend_selector: MagicMock = Depends(mock_backend_selector_api),
    setup_entry: MagicMock = Depends(mock_whirlpool_setup_entry),
) -> None:
    """Test successful flow initialized by the user."""
    region = DEFAULT_REGION
    brand = DEFAULT_BRAND

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal(config_entries.SOURCE_USER)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], CONFIG_INPUT | {CONF_REGION: region[0], CONF_BRAND: brand[0]}
    )

    _assert_successful_user_flow(setup_entry, result, region[0], brand[0])
    backend_selector.assert_called_once_with(brand[1], region[1])


@test
async def user_flow_invalid_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    auth_api: MagicMock = Depends(mock_auth_api),
    _appliances: MagicMock = Depends(mock_appliances_manager_api),
    setup_entry: MagicMock = Depends(mock_whirlpool_setup_entry),
) -> None:
    """Test invalid authentication in the flow initialized by the user."""
    region = DEFAULT_REGION
    brand = DEFAULT_BRAND

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    auth_api.return_value.is_access_token_valid.return_value = False
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], CONFIG_INPUT | {CONF_REGION: region[0], CONF_BRAND: brand[0]}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "invalid_auth"})

    # Test that it succeeds if the authentication is valid.
    auth_api.return_value.is_access_token_valid.return_value = True
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], CONFIG_INPUT | {CONF_REGION: region[0], CONF_BRAND: brand[0]}
    )
    _assert_successful_user_flow(setup_entry, result, region[0], brand[0])


@test.cases(
    test.case(
        "account_locked", exception=AccountLockedError, expected_error="account_locked"
    ),
    test.case(
        "client_connection_error",
        exception=aiohttp.ClientConnectionError,
        expected_error="cannot_connect",
    ),
    test.case(
        "timeout_error", exception=TimeoutError, expected_error="cannot_connect"
    ),
    test.case("unknown", exception=Exception, expected_error="unknown"),
)
async def user_flow_auth_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    auth_api: MagicMock = Depends(mock_auth_api),
    _appliances: MagicMock = Depends(mock_appliances_manager_api),
    setup_entry: MagicMock = Depends(mock_whirlpool_setup_entry),
    *,
    exception: type[Exception],
    expected_error: str,
) -> None:
    """Test authentication exceptions in the flow initialized by the user."""
    region = DEFAULT_REGION
    brand = DEFAULT_BRAND

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    auth_api.return_value.do_auth.side_effect = exception
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        CONFIG_INPUT
        | {
            CONF_REGION: region[0],
            CONF_BRAND: brand[0],
        },
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": expected_error})

    # Test that it succeeds after the error is cleared.
    auth_api.return_value.do_auth.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], CONFIG_INPUT | {CONF_REGION: region[0], CONF_BRAND: brand[0]}
    )

    _assert_successful_user_flow(setup_entry, result, region[0], brand[0])


@test
async def already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _auth: MagicMock = Depends(mock_auth_api),
    _appliances: MagicMock = Depends(mock_appliances_manager_api),
) -> None:
    """Test that configuring the integration twice with the same data fails."""
    region = DEFAULT_REGION
    brand = DEFAULT_BRAND

    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        data=CONFIG_INPUT | {CONF_REGION: region[0], CONF_BRAND: brand[0]},
        unique_id="test-username",
    )
    mock_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal(config_entries.SOURCE_USER)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], CONFIG_INPUT | {CONF_REGION: region[0], CONF_BRAND: brand[0]}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test.cases(
    test.case("aircons", appliance_type="aircons"),
    test.case("washers", appliance_type="washers"),
    test.case("dryers", appliance_type="dryers"),
    test.case("ovens", appliance_type="ovens"),
    test.case("refrigerators", appliance_type="refrigerators"),
)
async def no_appliances_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _auth: MagicMock = Depends(mock_auth_api),
    appliances_manager: MagicMock = Depends(mock_appliances_manager_api),
    setup_entry: MagicMock = Depends(mock_whirlpool_setup_entry),
    *,
    appliance_type: str,
) -> None:
    """Test we get an error with no appliances."""
    region = DEFAULT_REGION
    brand = DEFAULT_BRAND

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal(config_entries.SOURCE_USER)

    original_appliances = getattr(appliances_manager.return_value, appliance_type)
    appliances_manager.return_value.aircons = []
    appliances_manager.return_value.washers = []
    appliances_manager.return_value.dryers = []
    appliances_manager.return_value.ovens = []
    appliances_manager.return_value.refrigerators = []
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], CONFIG_INPUT | {CONF_REGION: region[0], CONF_BRAND: brand[0]}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "no_appliances"})

    # Test that it succeeds if appliances are found.
    setattr(appliances_manager.return_value, appliance_type, original_appliances)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], CONFIG_INPUT | {CONF_REGION: region[0], CONF_BRAND: brand[0]}
    )

    _assert_successful_user_flow(setup_entry, result, region[0], brand[0])


@test
async def reauth_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _auth: MagicMock = Depends(mock_auth_api),
    _appliances: MagicMock = Depends(mock_appliances_manager_api),
    _setup_entry: MagicMock = Depends(mock_whirlpool_setup_entry),
) -> None:
    """Test a successful reauth flow."""
    region = DEFAULT_REGION
    brand = DEFAULT_BRAND

    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        data=CONFIG_INPUT | {CONF_REGION: region[0], CONF_BRAND: brand[0]},
        unique_id="test-username",
    )
    mock_entry.add_to_hass(hass)

    result = await mock_entry.start_reauth_flow(hass)

    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PASSWORD: "new-password", CONF_BRAND: brand[0]}
    )

    _assert_successful_reauth_flow(mock_entry, result, region, brand)


@test
async def reauth_flow_invalid_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _appliances: MagicMock = Depends(mock_appliances_manager_api),
    _setup_entry: MagicMock = Depends(mock_whirlpool_setup_entry),
    auth_api: MagicMock = Depends(mock_auth_api),
) -> None:
    """Test an authorization error reauth flow."""
    region = DEFAULT_REGION
    brand = DEFAULT_BRAND

    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        data=CONFIG_INPUT | {CONF_REGION: region[0], CONF_BRAND: brand[0]},
        unique_id="test-username",
    )
    mock_entry.add_to_hass(hass)

    result = await mock_entry.start_reauth_flow(hass)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    auth_api.return_value.is_access_token_valid.return_value = False
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PASSWORD: "new-password", CONF_BRAND: brand[0]},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "invalid_auth"})

    # Test that it succeeds if the credentials are valid.
    auth_api.return_value.is_access_token_valid.return_value = True
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PASSWORD: "new-password", CONF_BRAND: brand[0]}
    )

    _assert_successful_reauth_flow(mock_entry, result, region, brand)


@test.cases(
    test.case(
        "account_locked", exception=AccountLockedError, expected_error="account_locked"
    ),
    test.case(
        "client_connection_error",
        exception=aiohttp.ClientConnectionError,
        expected_error="cannot_connect",
    ),
    test.case(
        "timeout_error", exception=TimeoutError, expected_error="cannot_connect"
    ),
    test.case("unknown", exception=Exception, expected_error="unknown"),
)
async def reauth_flow_auth_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _appliances: MagicMock = Depends(mock_appliances_manager_api),
    _setup_entry: MagicMock = Depends(mock_whirlpool_setup_entry),
    auth_api: MagicMock = Depends(mock_auth_api),
    *,
    exception: type[Exception],
    expected_error: str,
) -> None:
    """Test a connection error reauth flow."""
    region = DEFAULT_REGION
    brand = DEFAULT_BRAND

    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        data=CONFIG_INPUT | {CONF_REGION: region[0], CONF_BRAND: brand[0]},
        unique_id="test-username",
    )
    mock_entry.add_to_hass(hass)

    result = await mock_entry.start_reauth_flow(hass)

    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    auth_api.return_value.do_auth.side_effect = exception
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PASSWORD: "new-password", CONF_BRAND: brand[0]}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": expected_error})

    # Test that it succeeds if the exception is cleared.
    auth_api.return_value.do_auth.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PASSWORD: "new-password", CONF_BRAND: brand[0]}
    )

    _assert_successful_reauth_flow(mock_entry, result, region, brand)
