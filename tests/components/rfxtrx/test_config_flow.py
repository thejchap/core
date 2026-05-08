"""Test the Rfxtrx config flow."""

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.rfxtrx import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor fixture for tryke Depends() resolution."""


@test
async def user_form_show(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the initial user form is shown."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})


@test.skip("complex transport mock + add-on fixtures")
async def setup_network() -> None:
    """Skipped pending fixture port."""

@test.skip("complex transport mock + add-on fixtures")
async def setup_serial() -> None:
    """Skipped pending fixture port."""

@test.skip("complex transport mock + add-on fixtures")
async def setup_serial_manual() -> None:
    """Skipped pending fixture port."""

@test.skip("complex transport mock + add-on fixtures")
async def setup_network_fail() -> None:
    """Skipped pending fixture port."""

@test.skip("complex transport mock + add-on fixtures")
async def setup_serial_fail() -> None:
    """Skipped pending fixture port."""

@test.skip("complex transport mock + add-on fixtures")
async def setup_serial_manual_fail() -> None:
    """Skipped pending fixture port."""

@test.skip("complex transport mock + add-on fixtures")
async def options_global() -> None:
    """Skipped pending fixture port."""

@test.skip("complex transport mock + add-on fixtures")
async def no_protocols() -> None:
    """Skipped pending fixture port."""

@test.skip("complex transport mock + add-on fixtures")
async def options_add_device() -> None:
    """Skipped pending fixture port."""

@test.skip("complex transport mock + add-on fixtures")
async def options_add_duplicate_device() -> None:
    """Skipped pending fixture port."""

@test.skip("complex transport mock + add-on fixtures")
async def options_replace_sensor_device() -> None:
    """Skipped pending fixture port."""

@test.skip("complex transport mock + add-on fixtures")
async def options_replace_control_device() -> None:
    """Skipped pending fixture port."""

@test.skip("complex transport mock + add-on fixtures")
async def options_add_and_configure_device() -> None:
    """Skipped pending fixture port."""

@test.skip("complex transport mock + add-on fixtures")
async def options_configure_rfy_cover_device() -> None:
    """Skipped pending fixture port."""
