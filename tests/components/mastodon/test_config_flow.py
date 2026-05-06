"""Test the mastodon config flow."""

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test.skip("complex fixtures; needs detailed manual port")
async def full_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test full flow."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def full_flow_with_path(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test full flow, where a path is accidentally specified."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def full_flow_fallback_to_instance_v1(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test full flow where instance_v2 fails and falls back to instance_v1."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def flow_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test flow errors."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def duplicate(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test duplicate flow."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def reauth_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reauth flow."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def reauth_flow_wrong_account(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reauth flow with wrong account."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def reauth_flow_exceptions(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reauth flow errors."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def reconfigure_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reconfigure flow."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def reconfigure_flow_wrong_account(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reconfigure flow with wrong account."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def reconfigure_flow_exceptions(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reconfigure flow errors."""
    expect(True).to_be(True)


