"""Test the Fibaro scene platform."""

from unittest.mock import Mock

from tryke import Depends, expect, fixture, test

from homeassistant.components.scene import DOMAIN as SCENE_DOMAIN
from homeassistant.const import ATTR_ENTITY_ID, SERVICE_TURN_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from ._fixtures import (
    init_integration,
    mock_config_entry,
    mock_fibaro_client,
    mock_room,
    mock_scene,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    mock_network,
)


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Module-local anchor fixture."""
    return hass


@test
async def entity_attributes(
    hass: HomeAssistant = Depends(_trigger_executor),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    mock_fibaro_client: Mock = Depends(mock_fibaro_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_scene: Mock = Depends(mock_scene),
    mock_room: Mock = Depends(mock_room),
) -> None:
    """Test that the attributes of the entity are correct."""
    mock_fibaro_client.read_rooms.return_value = [mock_room]
    mock_fibaro_client.read_scenes.return_value = [mock_scene]
    await init_integration(hass, mock_config_entry)

    entry = entity_registry.async_get(
        "scene.my_fibaro_home_center_room_1_test_scene"
    )

    expect(entry is not None).to_be(True)
    expect(entry.unique_id).to_equal("hc2_111111.scene.1")
    expect(entry.original_name).to_equal("Room 1 Test scene")


@test
async def entity_attributes_without_room(
    hass: HomeAssistant = Depends(_trigger_executor),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    mock_fibaro_client: Mock = Depends(mock_fibaro_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_scene: Mock = Depends(mock_scene),
    mock_room: Mock = Depends(mock_room),
) -> None:
    """Test that the attributes of the entity are correct."""
    mock_room.name = None
    mock_fibaro_client.read_rooms.return_value = [mock_room]
    mock_fibaro_client.read_scenes.return_value = [mock_scene]
    await init_integration(hass, mock_config_entry)

    entry = entity_registry.async_get(
        "scene.my_fibaro_home_center_unknown_test_scene"
    )

    expect(entry is not None).to_be(True)
    expect(entry.unique_id).to_equal("hc2_111111.scene.1")


@test
async def activate_scene(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_fibaro_client: Mock = Depends(mock_fibaro_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_scene: Mock = Depends(mock_scene),
    mock_room: Mock = Depends(mock_room),
) -> None:
    """Test activate scene is called."""
    mock_fibaro_client.read_rooms.return_value = [mock_room]
    mock_fibaro_client.read_scenes.return_value = [mock_scene]
    await init_integration(hass, mock_config_entry)

    await hass.services.async_call(
        SCENE_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "scene.my_fibaro_home_center_room_1_test_scene"},
        blocking=True,
    )

    expect(mock_scene.start.call_count).to_equal(1)
