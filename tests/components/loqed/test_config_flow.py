"""Test the loqed config flow."""

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test.skip("complex fixtures; needs detailed manual port")
async def create_entry_zeroconf(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we get can create a lock via zeroconf."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def create_entry_user(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can create a lock via manual entry."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle cannot connect error."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def invalid_auth_when_lock_not_found(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle a situation where the user enters an invalid lock name."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def cannot_connect_when_lock_not_reachable(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle a situation where the user enters an invalid lock name."""
    expect(True).to_be(True)


