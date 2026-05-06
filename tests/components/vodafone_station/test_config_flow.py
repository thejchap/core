"""Tests for Vodafone Station config flow."""

from unittest.mock import AsyncMock

from aiovodafone.exceptions import (
    AlreadyLogged,
    CannotAuthenticate,
    CannotConnect,
    ModelNotSupported,
)
from tryke import Depends, expect, fixture, test

from homeassistant.components.device_tracker import CONF_CONSIDER_HOME
from homeassistant.components.vodafone_station.const import (
    CONF_DEVICE_DETAILS,
    DEVICE_TYPE,
    DEVICE_URL,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    mock_config_entry,
    mock_setup_entry,
    mock_vodafone_station_router,
)
from .const import TEST_HOST, TEST_PASSWORD, TEST_TYPE, TEST_URL, TEST_USERNAME

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def user(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _router: AsyncMock = Depends(mock_vodafone_station_router),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test starting a flow by user."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: TEST_HOST,
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
        },
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(
        {
            CONF_HOST: TEST_HOST,
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
            CONF_DEVICE_DETAILS: {
                DEVICE_TYPE: TEST_TYPE,
                DEVICE_URL: TEST_URL,
            },
        }
    )
    expect(bool(result["result"].unique_id)).to_be(False)

    expect(setup_entry.called).to_be(True)


@test.cases(
    test.case("cannot_connect", side_effect=CannotConnect, error="cannot_connect"),
    test.case("invalid_auth", side_effect=CannotAuthenticate, error="invalid_auth"),
    test.case("already_logged", side_effect=AlreadyLogged, error="already_logged"),
    test.case(
        "model_not_supported",
        side_effect=ModelNotSupported,
        error="model_not_supported",
    ),
    test.case("unknown", side_effect=ConnectionResetError, error="unknown"),
)
async def exception_connection(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    router: AsyncMock = Depends(mock_vodafone_station_router),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    *,
    side_effect: type[Exception],
    error: str,
) -> None:
    """Test starting a flow by user with a connection error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")

    router.login.side_effect = side_effect

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: TEST_HOST,
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": error})

    router.login.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: TEST_HOST,
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(TEST_HOST)
    expect(result["data"]).to_equal(
        {
            CONF_HOST: TEST_HOST,
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
            CONF_DEVICE_DETAILS: {
                DEVICE_TYPE: TEST_TYPE,
                DEVICE_URL: TEST_URL,
            },
        }
    )


@test
async def duplicate_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _router: AsyncMock = Depends(mock_vodafone_station_router),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test starting a flow by user with a duplicate entry."""
    config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: TEST_HOST,
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
        },
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def reauth_successful(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _router: AsyncMock = Depends(mock_vodafone_station_router),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test starting a reauthentication flow."""
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_PASSWORD: "other_fake_password",
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")


@test.cases(
    test.case("cannot_connect", side_effect=CannotConnect, error="cannot_connect"),
    test.case("invalid_auth", side_effect=CannotAuthenticate, error="invalid_auth"),
    test.case("already_logged", side_effect=AlreadyLogged, error="already_logged"),
    test.case("unknown", side_effect=ConnectionResetError, error="unknown"),
)
async def reauth_not_successful(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    router: AsyncMock = Depends(mock_vodafone_station_router),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    *,
    side_effect: type[Exception],
    error: str,
) -> None:
    """Test starting a reauthentication flow but no connection found."""
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    router.login.side_effect = side_effect
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_PASSWORD: "other_fake_password",
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["errors"]).to_equal({"base": error})

    router.login.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_PASSWORD: TEST_PASSWORD,
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(config_entry.data[CONF_PASSWORD]).to_equal(TEST_PASSWORD)


@test
async def options_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _router: AsyncMock = Depends(mock_vodafone_station_router),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test options flow."""
    config_entry.add_to_hass(hass)
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_CONSIDER_HOME: 37,
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal({CONF_CONSIDER_HOME: 37})


@test
async def reconfigure_successful(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _router: AsyncMock = Depends(mock_vodafone_station_router),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test that the host can be reconfigured."""
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    # Original entry.
    expect(config_entry.data[CONF_HOST]).to_equal(TEST_HOST)

    new_host = "192.168.100.60"

    reconfigure_result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: new_host,
            CONF_PASSWORD: TEST_PASSWORD,
            CONF_USERNAME: TEST_USERNAME,
        },
    )

    expect(reconfigure_result["type"]).to_be(FlowResultType.ABORT)
    expect(reconfigure_result["reason"]).to_equal("reconfigure_successful")

    # Changed entry.
    expect(config_entry.data[CONF_HOST]).to_equal(new_host)


@test.cases(
    test.case("cannot_connect", side_effect=CannotConnect, error="cannot_connect"),
    test.case("invalid_auth", side_effect=CannotAuthenticate, error="invalid_auth"),
    test.case("already_logged", side_effect=AlreadyLogged, error="already_logged"),
    test.case("unknown", side_effect=ConnectionResetError, error="unknown"),
)
async def reconfigure_fails(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    router: AsyncMock = Depends(mock_vodafone_station_router),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    *,
    side_effect: type[Exception],
    error: str,
) -> None:
    """Test that the host can be reconfigured."""
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    router.login.side_effect = side_effect

    reconfigure_result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: "192.168.100.60",
            CONF_PASSWORD: TEST_PASSWORD,
            CONF_USERNAME: TEST_USERNAME,
        },
    )

    expect(reconfigure_result["type"]).to_be(FlowResultType.FORM)
    expect(reconfigure_result["step_id"]).to_equal("reconfigure")
    expect(reconfigure_result["errors"]).to_equal({"base": error})

    router.login.side_effect = None

    reconfigure_result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: "192.168.100.61",
            CONF_PASSWORD: TEST_PASSWORD,
            CONF_USERNAME: TEST_USERNAME,
        },
    )

    expect(reconfigure_result["type"]).to_be(FlowResultType.ABORT)
    expect(reconfigure_result["reason"]).to_equal("reconfigure_successful")
    expect(config_entry.data).to_equal(
        {
            CONF_HOST: "192.168.100.61",
            CONF_PASSWORD: TEST_PASSWORD,
            CONF_USERNAME: TEST_USERNAME,
            CONF_DEVICE_DETAILS: {
                DEVICE_TYPE: TEST_TYPE,
                DEVICE_URL: TEST_URL,
            },
        }
    )
