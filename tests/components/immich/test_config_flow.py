"""Test the Immich config flow."""

from unittest.mock import AsyncMock, Mock

from aiohttp import ClientError
from aioimmich.exceptions import ImmichUnauthorizedError
from tryke import Depends, expect, fixture, test

from homeassistant.components.immich.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import (
    CONF_API_KEY,
    CONF_HOST,
    CONF_PORT,
    CONF_SSL,
    CONF_URL,
    CONF_VERIFY_SSL,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_config_entry, mock_immich, mock_setup_entry
from .const import MOCK_CONFIG_ENTRY_DATA, MOCK_USER_DATA

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


_UNAUTHORIZED_EXC = ImmichUnauthorizedError(
    {
        "message": "Invalid API key",
        "error": "Unauthenticated",
        "statusCode": 401,
        "correlationId": "abcdefg",
    }
)


@test
async def step_user(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    _immich: Mock = Depends(mock_immich),
) -> None:
    """Test a user initiated config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_USER_DATA,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("user")
    expect(result["data"]).to_equal(MOCK_CONFIG_ENTRY_DATA)
    expect(result["result"].unique_id).to_equal("e7ef5713-9dab-4bd4-b899-715b0ca4379e")
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("invalid_auth", exception=_UNAUTHORIZED_EXC, error="invalid_auth"),
    test.case("cannot_connect", exception=ClientError, error="cannot_connect"),
    test.case("unknown", exception=Exception, error="unknown"),
)
async def step_user_error_handling(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    immich: Mock = Depends(mock_immich),
    *,
    exception: Exception,
    error: str,
) -> None:
    """Test a user initiated config flow with errors."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    immich.users.async_get_my_user.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_USER_DATA,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": error})

    immich.users.async_get_my_user.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_USER_DATA,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def step_user_invalid_url(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    _immich: Mock = Depends(mock_immich),
) -> None:
    """Test a user initiated config flow with errors."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {**MOCK_USER_DATA, CONF_URL: "hts://invalid"},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({CONF_URL: "invalid_url"})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_USER_DATA,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def user_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _immich: Mock = Depends(mock_immich),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test starting a flow by user when already configured."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_USER_DATA,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def reauth_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    _immich: Mock = Depends(mock_immich),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reauthentication flow."""
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_API_KEY: "other_fake_api_key",
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(config_entry.data[CONF_API_KEY]).to_equal("other_fake_api_key")


@test.cases(
    test.case("invalid_auth", exception=_UNAUTHORIZED_EXC, error="invalid_auth"),
    test.case("cannot_connect", exception=ClientError, error="cannot_connect"),
    test.case("unknown", exception=Exception, error="unknown"),
)
async def reauth_flow_error_handling(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    immich: Mock = Depends(mock_immich),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    *,
    exception: Exception,
    error: str,
) -> None:
    """Test reauthentication flow with errors."""
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    immich.users.async_get_my_user.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_API_KEY: "other_fake_api_key",
        },
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["errors"]).to_equal({"base": error})

    immich.users.async_get_my_user.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_API_KEY: "other_fake_api_key",
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(config_entry.data[CONF_API_KEY]).to_equal("other_fake_api_key")
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def reauth_flow_mismatch(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    immich: Mock = Depends(mock_immich),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reauthentication flow with mis-matching unique id."""
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    immich.users.async_get_my_user.return_value.user_id = "other_user_id"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_API_KEY: "other_fake_api_key",
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unique_id_mismatch")


@test
async def reconfigure_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    _immich: Mock = Depends(mock_immich),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reconfigure flow."""
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_URL: "https://localhost:8443", CONF_VERIFY_SSL: True},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(config_entry.data[CONF_HOST]).to_equal("localhost")
    expect(config_entry.data[CONF_PORT]).to_equal(8443)
    expect(config_entry.data[CONF_SSL]).to_be(True)
    expect(config_entry.data[CONF_VERIFY_SSL]).to_be(True)


@test.cases(
    test.case("invalid_auth", exception=_UNAUTHORIZED_EXC, error="invalid_auth"),
    test.case("cannot_connect", exception=ClientError, error="cannot_connect"),
    test.case("unknown", exception=Exception, error="unknown"),
)
async def step_reconfigure_error_handling(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    immich: Mock = Depends(mock_immich),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    *,
    exception: Exception,
    error: str,
) -> None:
    """Test a user initiated config flow with errors."""
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    immich.users.async_get_my_user.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_URL: "https://localhost:8443", CONF_VERIFY_SSL: True},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")
    expect(result["errors"]).to_equal({"base": error})

    immich.users.async_get_my_user.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_URL: "https://localhost:8443", CONF_VERIFY_SSL: True},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")


@test
async def step_reconfigure_invalid_url(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    _immich: Mock = Depends(mock_immich),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test a user initiated config flow with errors."""
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_URL: "hts://invalid"},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")
    expect(result["errors"]).to_equal({CONF_URL: "invalid_url"})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_URL: "https://localhost:8443", CONF_VERIFY_SSL: True},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
