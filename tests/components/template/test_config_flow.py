"""Test the Switch config flow."""

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.template.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor fixture for tryke Depends() resolution."""


@test
async def user_menu_show(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the initial user menu is shown."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.MENU)


@test.skip("requires hass_ws_client fixture")
async def config_flow() -> None:
    """Skipped pending fixture port."""

@test.skip("requires hass_ws_client fixture")
async def config_flow_device() -> None:
    """Skipped pending fixture port."""

@test.skip("requires hass_ws_client fixture")
async def options() -> None:
    """Skipped pending fixture port."""

@test.skip("requires hass_ws_client fixture")
async def options_remove_device_class() -> None:
    """Skipped pending fixture port."""

@test.skip("requires hass_ws_client fixture")
async def config_flow_preview() -> None:
    """Skipped pending fixture port."""

@test.skip("requires hass_ws_client fixture")
async def config_flow_preview_bad_input() -> None:
    """Skipped pending fixture port."""

@test.skip("requires hass_ws_client fixture")
async def config_flow_preview_template_startup_error() -> None:
    """Skipped pending fixture port."""

@test.skip("requires hass_ws_client fixture")
async def config_flow_preview_template_error() -> None:
    """Skipped pending fixture port."""

@test.skip("requires hass_ws_client fixture")
async def config_flow_preview_bad_state() -> None:
    """Skipped pending fixture port."""

@test.skip("requires hass_ws_client fixture")
async def option_flow_preview() -> None:
    """Skipped pending fixture port."""

@test.skip("requires hass_ws_client fixture")
async def option_flow_sensor_preview_config_entry_removed() -> None:
    """Skipped pending fixture port."""

@test.skip("requires hass_ws_client fixture")
async def options_flow_change_device() -> None:
    """Skipped pending fixture port."""

@test.skip("requires hass_ws_client fixture")
async def preview_error() -> None:
    """Skipped pending fixture port."""

@test.skip("requires hass_ws_client fixture")
async def preview_this_variable_config_flow() -> None:
    """Skipped pending fixture port."""

@test.skip("requires hass_ws_client fixture")
async def preview_this_variable_options_flow() -> None:
    """Skipped pending fixture port."""
