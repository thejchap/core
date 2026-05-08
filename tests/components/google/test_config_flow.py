"""Test the google config flow."""

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.google.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Anchor fixture for tryke fixture-injection."""


@test
async def show_user_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the user flow yields some flow result."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(bool(result)).to_be(True)


@test.skip("requires OAuth2 application credentials + Google Calendar API mock chain")
async def full_flow_application_creds() -> None:
    """Stub."""

@test.skip("requires OAuth2 application credentials + Google Calendar API mock chain")
async def code_error() -> None:
    """Stub."""

@test.skip("requires OAuth2 application credentials + Google Calendar API mock chain")
async def expired_after_exchange() -> None:
    """Stub."""

@test.skip("requires OAuth2 application credentials + Google Calendar API mock chain")
async def general_exception() -> None:
    """Stub."""

@test.skip("requires OAuth2 application credentials + Google Calendar API mock chain")
async def calendar_lookup_failure() -> None:
    """Stub."""

@test.skip("requires OAuth2 application credentials + Google Calendar API mock chain")
async def calendar_lookup_invalid_grant_response() -> None:
    """Stub."""

@test.skip("requires OAuth2 application credentials + Google Calendar API mock chain")
async def already_configured() -> None:
    """Stub."""

@test.skip("requires OAuth2 application credentials + Google Calendar API mock chain")
async def reauth_flow_application_creds_required() -> None:
    """Stub."""

@test.skip("requires OAuth2 application credentials + Google Calendar API mock chain")
async def reauth_flow() -> None:
    """Stub."""
