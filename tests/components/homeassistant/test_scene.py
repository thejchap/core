"""Test Home Assistant scenes."""

from unittest.mock import patch

import voluptuous as vol

from tryke import Depends, expect, fixture, test

from homeassistant.components.homeassistant import scene as ha_scene
from homeassistant.components.homeassistant.scene import EVENT_SCENE_RELOADED
from homeassistant.const import STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.setup import async_setup_component

from tests.common import async_capture_events, async_mock_service
from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fixture,
    hass as hass_fixture,
    mock_network,
)
from tests.hass_tryke_helpers import expect_raises_async


@fixture
def _trigger_executor(_network=Depends(mock_network)) -> int:
    return 0


@test
async def reload_config_service(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the reload config service."""
    expect(await async_setup_component(hass, "scene", {})).to_be_truthy()
    await hass.async_block_till_done()

    test_reloaded_event = async_capture_events(hass, EVENT_SCENE_RELOADED)

    with patch(
        "homeassistant.config.load_yaml_config_file",
        autospec=True,
        return_value={"scene": {"name": "Hallo", "entities": {"light.kitchen": "on"}}},
    ):
        await hass.services.async_call("scene", "reload", blocking=True)
        await hass.async_block_till_done()

    expect(hass.states.get("scene.hallo")).not_.to_be(None)
    expect(len(test_reloaded_event)).to_be(1)

    with patch(
        "homeassistant.config.load_yaml_config_file",
        autospec=True,
        return_value={"scene": {"name": "Bye", "entities": {"light.kitchen": "on"}}},
    ):
        await hass.services.async_call("scene", "reload", blocking=True)
        await hass.async_block_till_done()

    expect(len(test_reloaded_event)).to_be(2)
    expect(hass.states.get("scene.hallo")).to_be(None)
    expect(hass.states.get("scene.bye")).not_.to_be(None)


@test
async def apply_service(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the apply service."""
    expect(await async_setup_component(hass, "scene", {})).to_be_truthy()
    expect(
        await async_setup_component(hass, "light", {"light": {"platform": "demo"}})
    ).to_be_truthy()
    await hass.async_block_till_done()

    await hass.services.async_call(
        "scene", "apply", {"entities": {"light.bed_light": "off"}}, blocking=True
    )

    expect(hass.states.get("light.bed_light").state).to_equal("off")

    await hass.services.async_call(
        "scene",
        "apply",
        {"entities": {"light.bed_light": {"state": "on", "brightness": 50}}},
        blocking=True,
    )

    state = hass.states.get("light.bed_light")
    expect(state.state).to_equal("on")
    expect(state.attributes["brightness"]).to_equal(50)

    turn_on_calls = async_mock_service(hass, "light", "turn_on")
    await hass.services.async_call(
        "scene",
        "apply",
        {
            "transition": 42,
            "entities": {"light.bed_light": {"state": "on", "brightness": 50}},
        },
        blocking=True,
    )

    expect(len(turn_on_calls)).to_be(1)
    expect(turn_on_calls[0].domain).to_equal("light")
    expect(turn_on_calls[0].service).to_equal("turn_on")
    expect(turn_on_calls[0].data.get("transition")).to_equal(42)
    expect(turn_on_calls[0].data.get("entity_id")).to_equal("light.bed_light")
    expect(turn_on_calls[0].data.get("brightness")).to_equal(50)


@test
async def create_service(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test the create service."""
    expect(
        await async_setup_component(
            hass,
            "scene",
            {"scene": {"name": "hallo_2", "entities": {"light.kitchen": "on"}}},
        )
    ).to_be_truthy()
    await hass.async_block_till_done()
    expect(hass.states.get("scene.hallo")).to_be(None)
    expect(hass.states.get("scene.hallo_2")).not_.to_be(None)

    await hass.services.async_call(
        "scene",
        "create",
        {"scene_id": "hallo", "entities": {}, "snapshot_entities": []},
        blocking=True,
    )
    await hass.async_block_till_done()
    expect("Empty scenes are not allowed" in caplog.text).to_be(True)
    expect(hass.states.get("scene.hallo")).to_be(None)

    await hass.services.async_call(
        "scene",
        "create",
        {
            "scene_id": "hallo",
            "entities": {"light.bed_light": {"state": "on", "brightness": 50}},
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    scene = hass.states.get("scene.hallo")
    expect(scene).not_.to_be(None)
    expect(scene.domain).to_equal("scene")
    expect(scene.name).to_equal("hallo")
    expect(scene.state).to_equal(STATE_UNKNOWN)
    expect(scene.attributes.get("entity_id")).to_equal(["light.bed_light"])

    await hass.services.async_call(
        "scene",
        "create",
        {
            "scene_id": "hallo",
            "entities": {"light.kitchen_light": {"state": "on", "brightness": 100}},
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    scene = hass.states.get("scene.hallo")
    expect(scene).not_.to_be(None)
    expect(scene.domain).to_equal("scene")
    expect(scene.name).to_equal("hallo")
    expect(scene.state).to_equal(STATE_UNKNOWN)
    expect(scene.attributes.get("entity_id")).to_equal(["light.kitchen_light"])

    await hass.services.async_call(
        "scene",
        "create",
        {
            "scene_id": "hallo_2",
            "entities": {"light.bed_light": {"state": "on", "brightness": 50}},
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    expect("The scene scene.hallo_2 already exists" in caplog.text).to_be(True)
    scene = hass.states.get("scene.hallo_2")
    expect(scene).not_.to_be(None)
    expect(scene.domain).to_equal("scene")
    expect(scene.name).to_equal("hallo_2")
    expect(scene.state).to_equal(STATE_UNKNOWN)
    expect(scene.attributes.get("entity_id")).to_equal(["light.kitchen"])


@test
async def delete_service(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test the delete service."""
    expect(
        await async_setup_component(
            hass,
            "scene",
            {"scene": {"name": "hallo_2", "entities": {"light.kitchen": "on"}}},
        )
    ).to_be_truthy()
    await hass.async_block_till_done()

    await hass.services.async_call(
        "scene",
        "create",
        {
            "scene_id": "hallo",
            "entities": {"light.bed_light": {"state": "on", "brightness": 50}},
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    async with expect_raises_async(ServiceValidationError):
        await hass.services.async_call(
            "scene",
            "delete",
            {
                "entity_id": "scene.hallo_3",
            },
            blocking=True,
        )

    async with expect_raises_async(ServiceValidationError):
        await hass.services.async_call(
            "scene",
            "delete",
            {
                "entity_id": "scene.hallo_2",
            },
            blocking=True,
        )
    expect(hass.states.get("scene.hallo_2")).not_.to_be(None)

    expect(hass.states.get("scene.hallo")).not_.to_be(None)

    await hass.services.async_call(
        "scene",
        "delete",
        {
            "entity_id": "scene.hallo",
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    expect(hass.states.get("state.hallo")).to_be(None)


@test
async def snapshot_service(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test the snapshot option."""
    expect(await async_setup_component(hass, "scene", {"scene": {}})).to_be_truthy()
    await hass.async_block_till_done()
    hass.states.async_set("light.my_light", "on", {"hs_color": (345, 75)})
    expect(hass.states.get("scene.hallo")).to_be(None)

    await hass.services.async_call(
        "scene",
        "create",
        {"scene_id": "hallo", "snapshot_entities": ["light.my_light"]},
        blocking=True,
    )
    await hass.async_block_till_done()
    scene = hass.states.get("scene.hallo")
    expect(scene).not_.to_be(None)
    expect(scene.attributes.get("entity_id")).to_equal(["light.my_light"])

    hass.states.async_set("light.my_light", "off", {"hs_color": (123, 45)})
    turn_on_calls = async_mock_service(hass, "light", "turn_on")
    await hass.services.async_call(
        "scene", "turn_on", {"entity_id": "scene.hallo"}, blocking=True
    )
    await hass.async_block_till_done()
    expect(len(turn_on_calls)).to_be(1)
    expect(turn_on_calls[0].data.get("entity_id")).to_equal("light.my_light")
    expect(turn_on_calls[0].data.get("hs_color")).to_equal((345, 75))

    await hass.services.async_call(
        "scene",
        "create",
        {"scene_id": "hallo_2", "snapshot_entities": ["light.not_existent"]},
        blocking=True,
    )
    await hass.async_block_till_done()
    expect(hass.states.get("scene.hallo_2")).to_be(None)
    expect(
        "Entity light.not_existent does not exist and therefore cannot be snapshotted"
        in caplog.text
    ).to_be(True)

    await hass.services.async_call(
        "scene",
        "create",
        {
            "scene_id": "hallo_3",
            "entities": {"light.bed_light": {"state": "on", "brightness": 50}},
            "snapshot_entities": ["light.my_light"],
        },
        blocking=True,
    )
    await hass.async_block_till_done()
    scene = hass.states.get("scene.hallo_3")
    expect(scene).not_.to_be(None)
    expect("light.my_light" in scene.attributes.get("entity_id")).to_be(True)
    expect("light.bed_light" in scene.attributes.get("entity_id")).to_be(True)


@test
async def ensure_no_intersection(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that entities and snapshot_entities do not overlap."""
    expect(await async_setup_component(hass, "scene", {"scene": {}})).to_be_truthy()
    await hass.async_block_till_done()

    async with expect_raises_async(
        vol.MultipleInvalid,
        match="entities and snapshot_entities must not overlap",
    ):
        await hass.services.async_call(
            "scene",
            "create",
            {
                "scene_id": "hallo",
                "entities": {"light.my_light": {"state": "on", "brightness": 50}},
                "snapshot_entities": ["light.my_light"],
            },
            blocking=True,
        )
    expect(hass.states.get("scene.hallo")).to_be(None)


@test
async def scenes_with_entity(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test finding scenes with a specific entity."""
    expect(
        await async_setup_component(
            hass,
            "scene",
            {
                "scene": [
                    {"name": "scene_1", "entities": {"light.kitchen": "on"}},
                    {"name": "scene_2", "entities": {"light.living_room": "off"}},
                    {
                        "name": "scene_3",
                        "entities": {
                            "light.kitchen": "on",
                            "light.living_room": "off",
                        },
                    },
                ]
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()

    expect(sorted(ha_scene.scenes_with_entity(hass, "light.kitchen"))).to_equal(
        ["scene.scene_1", "scene.scene_3"]
    )


@test
async def entities_in_scene(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test finding entities in a scene."""
    expect(
        await async_setup_component(
            hass,
            "scene",
            {
                "scene": [
                    {"name": "scene_1", "entities": {"light.kitchen": "on"}},
                    {"name": "scene_2", "entities": {"light.living_room": "off"}},
                    {
                        "name": "scene_3",
                        "entities": {
                            "light.kitchen": "on",
                            "light.living_room": "off",
                        },
                    },
                ]
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()

    for scene_id, entities in (
        ("scene.scene_1", ["light.kitchen"]),
        ("scene.scene_2", ["light.living_room"]),
        ("scene.scene_3", ["light.kitchen", "light.living_room"]),
    ):
        expect(ha_scene.entities_in_scene(hass, scene_id)).to_equal(entities)


@test
async def config(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test passing config in YAML."""
    expect(
        await async_setup_component(
            hass,
            "scene",
            {
                "scene": [
                    {
                        "id": "scene_id",
                        "name": "Scene Icon",
                        "icon": "mdi:party",
                        "entities": {"light.kitchen": "on"},
                    },
                    {
                        "name": "Scene No Icon",
                        "entities": {"light.kitchen": {"state": "on"}},
                    },
                ]
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()

    icon = hass.states.get("scene.scene_icon")
    expect(icon).not_.to_be(None)
    expect(icon.attributes["icon"]).to_equal("mdi:party")

    no_icon = hass.states.get("scene.scene_no_icon")
    expect(no_icon).not_.to_be(None)
    expect("icon" not in no_icon.attributes).to_be(True)


@test
def validator() -> None:
    """Test validators."""
    parsed = ha_scene.STATES_SCHEMA({"light.Test": {"state": "on"}})
    expect(len(parsed)).to_be(1)
    expect("light.test" in parsed).to_be(True)
    expect(parsed["light.test"].entity_id).to_equal("light.test")
    expect(parsed["light.test"].state).to_equal("on")
