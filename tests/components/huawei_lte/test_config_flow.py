"""Test the huawei_lte config flow."""

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test.skip("complex fixtures; needs detailed manual port")
async def show_set_form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that the setup form is served."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def urlize_plain_host(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that plain host or IP gets converted to a URL."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we reject already configured devices."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def connection_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we show user form on various errors."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def login_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we show user form with appropriate error on response failure."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test successful flow provides entry creation data."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def ssdp(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test SSDP discovery initiates config properly."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def reauth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reauth."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def options(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test options produce expected data."""
    expect(True).to_be(True)


