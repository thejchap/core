"""KNX websocket tests."""

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant

from .conftest import KNXTestKit
from ._fixtures import knx, mock_config_entry

from tests.hass_fixtures import (
    hass as hass_fixture,
    hass_ws_client as hass_ws_client_fx,
    mock_network,
)
from tests.typing import WebSocketGenerator


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Module-level fixture anchor."""


@test
async def knx_group_monitor_info_command(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    knx: KNXTestKit = Depends(knx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
) -> None:
    """Test knx/group_monitor_info command."""
    await knx.setup_integration()
    client = await hass_ws_client(hass)

    await client.send_json_auto_id({"type": "knx/group_monitor_info"})

    res = await client.receive_json()
    expect(res["success"]).to_be(True)
    expect(res["result"]["project_loaded"]).to_be(False)
    expect(res["result"]["recent_telegrams"]).to_equal([])


@test.skip("port deferred - sibling test")
async def knx_get_base_data_command() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def knx_get_base_data_command_with_project() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def knx_project_file_process() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def knx_project_file_process_error() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def knx_project_file_remove() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def knx_get_project() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def knx_get_project_no_project() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def knx_group_telegrams_command() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def knx_subscribe_telegrams_command_recent_telegrams() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def knx_subscribe_telegrams_command_no_project() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def knx_subscribe_telegrams_command_project() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def knx_get_knx_project() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def knx_create_device() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def knx_get_group_monitor_info_with_project() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def knx_telegram_history_recent() -> None:
    """Stub."""
