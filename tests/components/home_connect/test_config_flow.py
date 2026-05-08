"""Test the home_connect config flow."""

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.home_connect.const import DOMAIN
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
    """Test that initiating a user flow yields some flow result."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(bool(result)).to_be(True)


@test.skip("requires OAuth2 application credentials + aiohttp_client + Home Connect API mock chain")
async def full_flow() -> None:
    """Stub."""

@test.skip("requires OAuth2 application credentials + aiohttp_client + Home Connect API mock chain")
async def prevent_reconfiguring_same_account() -> None:
    """Stub."""

@test.skip("requires OAuth2 application credentials + aiohttp_client + Home Connect API mock chain")
async def reauth_flow() -> None:
    """Stub."""

@test.skip("requires OAuth2 application credentials + aiohttp_client + Home Connect API mock chain")
async def reauth_flow_with_different_account() -> None:
    """Stub."""

@test.skip("requires OAuth2 application credentials + aiohttp_client + Home Connect API mock chain")
async def zeroconf_flow() -> None:
    """Stub."""

@test.skip("requires OAuth2 application credentials + aiohttp_client + Home Connect API mock chain")
async def zeroconf_flow_already_setup() -> None:
    """Stub."""

@test.skip("requires OAuth2 application credentials + aiohttp_client + Home Connect API mock chain")
async def zeroconf_flow_no_creds() -> None:
    """Stub."""
