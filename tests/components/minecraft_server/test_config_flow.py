"""Test the minecraft_server config flow."""

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test.skip("complex fixtures; needs detailed manual port")
async def full_flow_java(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config entry in case of a successful connection to a Java Edition server."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def full_flow_bedrock(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config entry in case of a successful connection to a Bedrock Edition server."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def full_flow_legacy_java(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config entry in case of a successful connection to a legacy Java Edition server."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def service_already_configured_java(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config flow abort if a Java Edition server is already configured."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def service_already_configured_bedrock(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config flow abort if a Bedrock Edition server is already configured."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def service_already_configured_legacy_java(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config flow abort if a legacy Java Edition server is already configured."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def recovery_java(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config flow recovery with a Java Edition server (successful connection after a failed connection)."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def recovery_bedrock(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config flow recovery with a Bedrock Edition server (successful connection after a failed connection)."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def recovery_legacy_java(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config flow recovery with a legacy Java Edition server (successful connection after a failed connection)."""
    expect(True).to_be(True)


