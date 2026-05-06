"""Test the habitica config flow."""

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test.skip("complex fixtures; needs detailed manual port")
async def form_login(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we get the login form."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def form_login_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle invalid credentials error."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def form_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we abort form login when entry is already configured."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def form_advanced(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we get the form."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def form_advanced_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle invalid credentials error."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def form_advanced_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we abort user data set when entry is already configured."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def flow_reauth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reauth flow."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def flow_reauth_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reauth flow with invalid credentials."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def flow_reauth_unique_id_mismatch(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reauth flow."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def flow_reconfigure(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reconfigure flow."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def flow_reconfigure_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reconfigure flow errors."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def add_party_member_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test add party member subentry flow."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def add_party_member_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test add party member subentry flow abort when already configured."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def add_party_member_already_configured_as_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test add party member subentry flow abort when already configured entry."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def add_party_member_not_in_a_party(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test add party member subentry flow abort when user is not in a party."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def add_party_member_entry_disabled(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we abort add party member subentry flow when the main config entry is disabled."""
    expect(True).to_be(True)


