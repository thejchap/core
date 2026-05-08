"""KNX config store tests."""

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
async def create_entity_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    knx: KNXTestKit = Depends(knx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
) -> None:
    """Test unsuccessful entity creation."""
    await knx.setup_integration()
    client = await hass_ws_client(hass)

    # invalid platform
    await client.send_json_auto_id(
        {
            "type": "knx/create_entity",
            "platform": "invalid_platform",
            "data": {
                "entity": {"name": "Test invalid platform"},
                "knx": {"ga_switch": {"write": "1/2/3"}},
            },
        }
    )
    res = await client.receive_json()
    expect(res["success"]).to_be(True)
    expect(bool(res["result"]["success"])).to_be(False)


@test.skip("port deferred - sibling test")
async def create_entity() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def update_entity() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def update_entity_error() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def delete_entity() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def delete_entity_error() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def get_entity_config() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def get_entity_config_error() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def validate_entity() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def update_expose_error() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def get_entity_entries() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def update_expose_remove_old_entity() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def get_supported_platforms() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def update_entity_replaces_old() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def reload() -> None:
    """Stub."""
