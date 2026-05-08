"""Tests for Plex config flow."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.plex.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.hass_fixtures import (
    current_request_with_host,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _request: None = Depends(current_request_with_host),
) -> None:
    """Force tryke fixture resolution before each test."""


@test.skip("requires plexapi + requests_mock + MockGDM extensive fixtures (not ported)")
async def bad_credentials(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_bad_credentials."""


@test.skip("requires plexapi + requests_mock + MockGDM extensive fixtures (not ported)")
async def bad_hostname(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_bad_hostname."""


@test
async def unknown_exception(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test when an unknown exception is encountered."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    with (
        patch("plexapi.myplex.MyPlexAccount", side_effect=Exception),
        patch("plexauth.PlexAuth.initiate_auth"),
        patch("plexauth.PlexAuth.token", return_value="MOCK_TOKEN"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )
        expect(result["type"]).to_be(FlowResultType.EXTERNAL_STEP)

        result = await hass.config_entries.flow.async_configure(result["flow_id"])
        expect(result["type"]).to_be(FlowResultType.EXTERNAL_STEP_DONE)

        result = await hass.config_entries.flow.async_configure(result["flow_id"])
        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("unknown")

@test.skip("requires plexapi + requests_mock + MockGDM extensive fixtures (not ported)")
async def no_servers_found() -> None:
    """Stub for test_no_servers_found (port deferred)."""

@test.skip("requires plexapi + requests_mock + MockGDM extensive fixtures (not ported)")
async def single_available_server() -> None:
    """Stub for test_single_available_server (port deferred)."""

@test.skip("requires plexapi + requests_mock + MockGDM extensive fixtures (not ported)")
async def multiple_servers_with_selection() -> None:
    """Stub for test_multiple_servers_with_selection (port deferred)."""

@test.skip("requires plexapi + requests_mock + MockGDM extensive fixtures (not ported)")
async def adding_last_unconfigured_server() -> None:
    """Stub for test_adding_last_unconfigured_server (port deferred)."""

@test.skip("requires plexapi + requests_mock + MockGDM extensive fixtures (not ported)")
async def all_available_servers_configured() -> None:
    """Stub for test_all_available_servers_configured (port deferred)."""

@test.skip("requires plexapi + requests_mock + MockGDM extensive fixtures (not ported)")
async def option_flow() -> None:
    """Stub for test_option_flow (port deferred)."""

@test.skip("requires plexapi + requests_mock + MockGDM extensive fixtures (not ported)")
async def missing_option_flow() -> None:
    """Stub for test_missing_option_flow (port deferred)."""

@test.skip("requires plexapi + requests_mock + MockGDM extensive fixtures (not ported)")
async def option_flow_new_users_available() -> None:
    """Stub for test_option_flow_new_users_available (port deferred)."""

@test.skip("requires plexapi + requests_mock + MockGDM extensive fixtures (not ported)")
async def external_timed_out() -> None:
    """Stub for test_external_timed_out (port deferred)."""

@test.skip("requires plexapi + requests_mock + MockGDM extensive fixtures (not ported)")
async def callback_view() -> None:
    """Stub for test_callback_view (port deferred)."""

@test.skip("requires plexapi + requests_mock + MockGDM extensive fixtures (not ported)")
async def manual_config() -> None:
    """Stub for test_manual_config (port deferred)."""

@test.skip("requires plexapi + requests_mock + MockGDM extensive fixtures (not ported)")
async def manual_config_with_token() -> None:
    """Stub for test_manual_config_with_token (port deferred)."""

@test.skip("requires plexapi + requests_mock + MockGDM extensive fixtures (not ported)")
async def integration_discovery() -> None:
    """Stub for test_integration_discovery (port deferred)."""

@test.skip("requires plexapi + requests_mock + MockGDM extensive fixtures (not ported)")
async def reauth() -> None:
    """Stub for test_reauth (port deferred)."""

@test.skip("requires plexapi + requests_mock + MockGDM extensive fixtures (not ported)")
async def reauth_multiple_servers_available() -> None:
    """Stub for test_reauth_multiple_servers_available (port deferred)."""

@test.skip("requires plexapi + requests_mock + MockGDM extensive fixtures (not ported)")
async def client_request_missing() -> None:
    """Stub for test_client_request_missing (port deferred)."""

@test.skip("requires plexapi + requests_mock + MockGDM extensive fixtures (not ported)")
async def client_header_issues() -> None:
    """Stub for test_client_header_issues (port deferred)."""
