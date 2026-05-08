"""Tests for Tibber config flow."""

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.tibber.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import recorder_mock

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _recorder: object = Depends(recorder_mock),
) -> None:
    """Force tryke fixture resolution before each test."""


@test
async def data_api_requires_credentials(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Abort when OAuth credentials are missing."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("missing_credentials")


@test.skip("requires application_credentials + tibber_mock + indirect parametrize — port deferred")
async def oauth_create_entry_abort_exceptions(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_oauth_create_entry_abort_exceptions."""


@test.skip("requires application_credentials + tibber_mock + indirect parametrize — port deferred")
async def oauth_create_entry_connection_error_retry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_oauth_create_entry_connection_error_retry."""


@test.skip("requires application_credentials + OAuth flow — port deferred")
async def data_api_extra_authorize_scope(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_data_api_extra_authorize_scope."""


@test.skip("requires application_credentials + OAuth callback flow — port deferred")
async def full_flow_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_full_flow_success."""


@test.skip("requires application_credentials + OAuth callback flow — port deferred")
async def data_api_abort_when_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_data_api_abort_when_already_configured."""


@test.skip("requires reauth flow with OAuth — port deferred")
async def reauth_flow_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_reauth_flow_success."""


@test.skip("requires reauth flow with OAuth — port deferred")
async def reauth_flow_wrong_account(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_reauth_flow_wrong_account."""
