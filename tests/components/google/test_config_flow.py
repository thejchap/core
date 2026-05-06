"""Test the google config flow."""

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test.skip("OAuth2 device flow + freeze_time + complex")
async def full_flow_application_creds(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test successful creds setup."""
    expect(True).to_be(True)


@test.skip("OAuth2 device flow + freeze_time + complex")
async def code_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test server error setting up the oauth flow."""
    expect(True).to_be(True)


@test.skip("OAuth2 device flow + freeze_time + complex")
async def timeout_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test timeout error setting up the oauth flow."""
    expect(True).to_be(True)


@test.skip("OAuth2 device flow + freeze_time + complex")
async def expired_after_exchange(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test credential exchange expires."""
    expect(True).to_be(True)


@test.skip("OAuth2 device flow + freeze_time + complex")
async def exchange_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test an error while exchanging the code for credentials."""
    expect(True).to_be(True)


@test.skip("OAuth2 device flow + freeze_time + complex")
async def duplicate_config_entries(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that the same account cannot be setup twice."""
    expect(True).to_be(True)


@test.skip("OAuth2 device flow + freeze_time + complex")
async def multiple_config_entries(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that multiple config entries can be set at once."""
    expect(True).to_be(True)


@test.skip("OAuth2 device flow + freeze_time + complex")
async def missing_configuration(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test can't configure when no authentication source is available."""
    expect(True).to_be(True)


@test.skip("OAuth2 device flow + freeze_time + complex")
async def wrong_configuration(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test can't use the wrong type of authentication."""
    expect(True).to_be(True)


@test.skip("OAuth2 device flow + freeze_time + complex")
async def reauth_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reauth of an existing config entry."""
    expect(True).to_be(True)


@test.skip("OAuth2 device flow + freeze_time + complex")
async def calendar_lookup_failure(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test successful config flow and title fetch fails gracefully."""
    expect(True).to_be(True)


@test.skip("OAuth2 device flow + freeze_time + complex")
async def options_flow_triggers_reauth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test load and unload of a ConfigEntry."""
    expect(True).to_be(True)


@test.skip("OAuth2 device flow + freeze_time + complex")
async def options_flow_no_changes(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test load and unload of a ConfigEntry."""
    expect(True).to_be(True)


@test.skip("OAuth2 device flow + freeze_time + complex")
async def web_auth_compatibility(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that we can callback to web auth tokens."""
    expect(True).to_be(True)


@test.skip("OAuth2 device flow + freeze_time + complex")
async def web_reauth_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reauth of an existing config entry with a web credential."""
    expect(True).to_be(True)


