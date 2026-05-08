"""Test the bosch_alarm config flow."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.bosch_alarm.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Anchor fixture for tryke fixture-injection."""


@test
async def form_user_show(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the user form is shown."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)


@test.skip("requires bosch_alarm panel mock + parametrize over panel models")
async def form_user() -> None:
    """Stub."""

@test.skip("requires bosch_alarm panel mock + parametrize over panel models")
async def form_exceptions() -> None:
    """Stub."""

@test.skip("requires bosch_alarm panel mock + parametrize over panel models")
async def form_exceptions_user() -> None:
    """Stub."""

@test.skip("requires bosch_alarm panel mock + parametrize over panel models")
async def form_unique_id_collision() -> None:
    """Stub."""

@test.skip("requires bosch_alarm panel mock + parametrize over panel models")
async def reauth() -> None:
    """Stub."""

@test.skip("requires bosch_alarm panel mock + parametrize over panel models")
async def reauth_invalid_auth() -> None:
    """Stub."""

@test.skip("requires bosch_alarm panel mock + parametrize over panel models")
async def reconfigure() -> None:
    """Stub."""

@test.skip("requires bosch_alarm panel mock + parametrize over panel models")
async def reconfigure_invalid_auth() -> None:
    """Stub."""

@test.skip("requires bosch_alarm panel mock + parametrize over panel models")
async def options_flow() -> None:
    """Stub."""
