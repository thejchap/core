"""Tests for the Orvibo config flow.

The orvibo library binds a global UDP socket at import time which conflicts
with parallel test runs. We patch ``socket.socket.bind`` before importing
anything from the orvibo lib.
"""

from unittest.mock import patch

# The orvibo library executes a global UDP socket bind on import.
with patch("socket.socket.bind"):
    import orvibo.s20  # noqa: F401

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.orvibo.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Force tryke to fully resolve hass before each test."""


@test
async def user_menu_display(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Initial step displays the user menu correctly."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.MENU)
    expect(result["step_id"]).to_equal("user")
    expect(set(result["menu_options"])).to_equal({"start_discovery", "edit"})


@test.skip("orvibo S20 mocking + indirect parametrize - port deferred")
async def edit_flow_success() -> None:
    """Stub for test_edit_flow_success."""


@test.skip("orvibo S20 mocking + indirect parametrize - port deferred")
async def edit_flow_errors() -> None:
    """Stub for test_edit_flow_errors."""


@test.skip("orvibo discovery flow - SHOW_PROGRESS interaction not yet shimmed")
async def discovery_success() -> None:
    """Stub for test_discovery_success."""


@test.skip("orvibo discovery flow - SHOW_PROGRESS interaction not yet shimmed")
async def discovery_no_devices() -> None:
    """Stub for test_discovery_no_devices."""


@test.skip("orvibo S20 mocking - port deferred")
async def import_flow_success() -> None:
    """Stub for test_import_flow_success."""


@test.skip("orvibo S20 mocking - port deferred")
async def import_flow_errors() -> None:
    """Stub for test_import_flow_errors."""


@test.skip("orvibo S20 mocking + indirect parametrize - port deferred")
async def discover_skips_existing_and_invalid_mac() -> None:
    """Stub for test_discover_skips_existing_and_invalid_mac."""


@test.skip("orvibo SHOW_PROGRESS interaction - port deferred")
async def start_discovery_shows_progress() -> None:
    """Stub for test_start_discovery_shows_progress."""


@test.skip("orvibo discovery exception path - port deferred")
async def discovery_flow_task_exception() -> None:
    """Stub for test_discovery_flow_task_exception."""
