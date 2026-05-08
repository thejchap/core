"""Test the Fibaro cover platform."""

from unittest.mock import Mock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.cover import CoverEntityFeature
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from ._fixtures import (
    init_integration,
    mock_config_entry,
    mock_fibaro_client,
    mock_positionable_cover,
    mock_room,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor fixture for tryke fixture-injection."""


@test
async def positionable_cover_setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    client: Mock = Depends(mock_fibaro_client),
    entry: MockConfigEntry = Depends(mock_config_entry),
    cover: Mock = Depends(mock_positionable_cover),
    room: Mock = Depends(mock_room),
) -> None:
    """Test that the cover creates an entity."""
    client.read_rooms.return_value = [room]
    client.read_devices.return_value = [cover]

    with patch("homeassistant.components.fibaro.PLATFORMS", [Platform.COVER]):
        await init_integration(hass, entry)
        registry_entry = entity_registry.async_get(
            "cover.room_1_test_cover_2"
        )
        expect(registry_entry).not_.to_be(None)
        expect(registry_entry.supported_features).to_equal(
            CoverEntityFeature.OPEN
            | CoverEntityFeature.CLOSE
            | CoverEntityFeature.STOP
            | CoverEntityFeature.SET_POSITION
        )
        expect(registry_entry.unique_id).to_equal("hc2_111111.2")
        expect(registry_entry.original_name).to_equal("Room 1 Test cover")


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def cover_opening() -> None:
    """Stub for test_cover_opening."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def cover_opening_closing_none() -> None:
    """Stub for test_cover_opening_closing_none."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def cover_closing() -> None:
    """Stub for test_cover_closing."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def cover_setup() -> None:
    """Stub for test_cover_setup."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def cover_open_action() -> None:
    """Stub for test_cover_open_action."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def cover_close_action() -> None:
    """Stub for test_cover_close_action."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def cover_stop_action() -> None:
    """Stub for test_cover_stop_action."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def cover_open_slats_action() -> None:
    """Stub for test_cover_open_slats_action."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def cover_close_tilt_action() -> None:
    """Stub for test_cover_close_tilt_action."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def cover_stop_slats_action() -> None:
    """Stub for test_cover_stop_slats_action."""

