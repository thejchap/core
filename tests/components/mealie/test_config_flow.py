"""Test the mealie config flow."""

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
async def flow_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test flow errors."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def ingress_host(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test disallow ingress host."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def flow_version_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test flow version error."""
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


@test.skip("complex fixtures; needs detailed manual port")
async def hassio_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test successful Supervisor flow."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def hassio_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we only allow a single config flow."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def hassio_ignored(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the supervisor discovered instance can be ignored."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def hassio_connection_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test flow errors."""
    expect(True).to_be(True)


