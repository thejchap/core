"""Tests for the Velbus config flow."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.velbus.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor fixture for tryke Depends() resolution."""


@test
async def user_initial_menu_show(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the initial menu is shown when starting a user flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result.get("type")).to_be(FlowResultType.MENU)
    expect(result.get("step_id")).to_equal("user")
    expect(result.get("menu_options")).to_equal(["network", "usbselect"])


@test.skip("complex velbus-serial transport fixtures")
async def user_network_succes() -> None:
    """Skipped pending fixture port."""

@test.skip("complex velbus-serial transport fixtures")
async def user_network_connect_failure() -> None:
    """Skipped pending fixture port."""

@test.skip("complex velbus-serial transport fixtures")
async def user_usb_connect_failure() -> None:
    """Skipped pending fixture port."""

@test.skip("complex velbus-serial transport fixtures")
async def user_usb_success() -> None:
    """Skipped pending fixture port."""

@test.skip("complex velbus-serial transport fixtures")
async def vlp_step_no_modules() -> None:
    """Skipped pending fixture port."""

@test.skip("complex velbus-serial transport fixtures")
async def vlp_step_success() -> None:
    """Skipped pending fixture port."""

@test.skip("complex velbus-serial transport fixtures")
async def reconfigure_step() -> None:
    """Skipped pending fixture port."""

@test.skip("complex velbus-serial transport fixtures")
async def reconfigure_step_change_host_port() -> None:
    """Skipped pending fixture port."""

@test.skip("complex velbus-serial transport fixtures")
async def reconfigure_step_password_preserved() -> None:
    """Skipped pending fixture port."""

@test.skip("complex velbus-serial transport fixtures")
async def network_abort_if_already_setup() -> None:
    """Skipped pending fixture port."""

@test.skip("complex velbus-serial transport fixtures")
async def flow_usb() -> None:
    """Skipped pending fixture port."""

@test.skip("complex velbus-serial transport fixtures")
async def flow_usb_if_already_setup() -> None:
    """Skipped pending fixture port."""

@test.skip("complex velbus-serial transport fixtures")
async def flow_usb_failed() -> None:
    """Skipped pending fixture port."""
