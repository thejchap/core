"""The tests for the Scene component."""

import io
from collections.abc import Generator
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant import loader
from homeassistant.components import light, scene
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ENTITY_MATCH_ALL,
    SERVICE_TURN_ON,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import HomeAssistant, State
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util
from homeassistant.util.yaml import loader as yaml_loader

from tests.common import (
    async_mock_service,
    mock_restore_cache,
    setup_test_component_platform,
)
from tests.components.light.common import MockLight
from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fixture,
    hass as hass_fixture,
)


@fixture
def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Anchor fixture for the module."""
    return hass


@fixture
def mock_light_entities() -> list[MockLight]:
    """Return mocked light entities."""
    return [
        MockLight("Ceiling", "off"),
        MockLight("Wall", "off"),
    ]


@fixture
def entities(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_light_entities: list[MockLight] = Depends(mock_light_entities),
) -> list[MockLight]:
    """Initialize the test light."""
    entities = mock_light_entities[0:2]
    setup_test_component_platform(hass, light.DOMAIN, entities)
    return entities


@fixture
def enable_custom_integrations(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> Generator[None]:
    """Enable custom integrations defined in the test dir."""
    hass.data.pop(loader.DATA_CUSTOM_COMPONENTS, None)
    yield


async def activate(hass: HomeAssistant, entity_id: str = ENTITY_MATCH_ALL) -> None:
    """Activate a scene."""
    data = {}

    if entity_id:
        data[ATTR_ENTITY_ID] = entity_id

    await hass.services.async_call(scene.DOMAIN, SERVICE_TURN_ON, data, blocking=True)


async def setup_lights(
    hass: HomeAssistant, entities: list[MockLight]
) -> tuple[MockLight, MockLight]:
    """Set up the light component."""
    expect(
        await async_setup_component(
            hass, light.DOMAIN, {light.DOMAIN: {"platform": "test"}}
        )
    ).to_be_truthy()
    await hass.async_block_till_done()

    light_1, light_2 = entities
    light_1._attr_supported_color_modes = {"brightness"}
    light_2._attr_supported_color_modes = {"brightness"}
    light_1._attr_color_mode = "brightness"
    light_2._attr_color_mode = "brightness"

    await turn_off_lights(hass, [light_1.entity_id, light_2.entity_id])
    expect(light.is_on(hass, light_1.entity_id)).to_be(False)
    expect(light.is_on(hass, light_2.entity_id)).to_be(False)

    return light_1, light_2


async def turn_off_lights(hass: HomeAssistant, entity_ids: list[str]) -> None:
    """Turn lights off."""
    await hass.services.async_call(
        "light",
        "turn_off",
        {"entity_id": entity_ids},
        blocking=True,
    )
    await hass.async_block_till_done()


@test
async def config_yaml_alias_anchor(
    _enable: None = Depends(enable_custom_integrations),
    hass: HomeAssistant = Depends(_trigger_executor),
    entities: list[MockLight] = Depends(entities),
) -> None:
    """Test the usage of YAML aliases and anchors."""
    light_1, light_2 = await setup_lights(hass, entities)
    entity_state = {"state": "on", "brightness": 100}

    expect(
        await async_setup_component(
            hass,
            scene.DOMAIN,
            {
                "scene": [
                    {
                        "name": "test",
                        "entities": {
                            light_1.entity_id: entity_state,
                            light_2.entity_id: entity_state,
                        },
                    }
                ]
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()

    await activate(hass, "scene.test")

    expect(light.is_on(hass, light_1.entity_id)).to_be(True)
    expect(light.is_on(hass, light_2.entity_id)).to_be(True)
    expect(light_1.last_call("turn_on")[1].get("brightness")).to_equal(100)
    expect(light_2.last_call("turn_on")[1].get("brightness")).to_equal(100)


@test
async def config_yaml_bool(
    _enable: None = Depends(enable_custom_integrations),
    hass: HomeAssistant = Depends(_trigger_executor),
    entities: list[MockLight] = Depends(entities),
) -> None:
    """Test parsing of booleans in yaml config."""
    light_1, light_2 = await setup_lights(hass, entities)

    config = (
        "scene:\n"
        "  - name: test\n"
        "    entities:\n"
        f"      {light_1.entity_id}: on\n"
        f"      {light_2.entity_id}:\n"
        "        state: on\n"
        "        brightness: 100\n"
    )

    with io.StringIO(config) as file:
        doc = yaml_loader.yaml.safe_load(file)

    expect(await async_setup_component(hass, scene.DOMAIN, doc)).to_be_truthy()
    await hass.async_block_till_done()

    await activate(hass, "scene.test")

    expect(light.is_on(hass, light_1.entity_id)).to_be(True)
    expect(light.is_on(hass, light_2.entity_id)).to_be(True)
    expect(light_2.last_call("turn_on")[1].get("brightness")).to_equal(100)


@test
async def activate_scene(
    _enable: None = Depends(enable_custom_integrations),
    hass: HomeAssistant = Depends(_trigger_executor),
    entities: list[MockLight] = Depends(entities),
) -> None:
    """Test active scene."""
    light_1, light_2 = await setup_lights(hass, entities)

    expect(
        await async_setup_component(
            hass,
            scene.DOMAIN,
            {
                "scene": [
                    {
                        "name": "test",
                        "entities": {
                            light_1.entity_id: "on",
                            light_2.entity_id: {"state": "on", "brightness": 100},
                        },
                    }
                ]
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()

    expect(hass.states.get("scene.test").state).to_equal(STATE_UNKNOWN)

    now = dt_util.utcnow()
    with patch("homeassistant.core.dt_util.utcnow", return_value=now):
        await activate(hass, "scene.test")

    expect(hass.states.get("scene.test").state).to_equal(now.isoformat())

    expect(light.is_on(hass, light_1.entity_id)).to_be(True)
    expect(light.is_on(hass, light_2.entity_id)).to_be(True)
    expect(light_2.last_call("turn_on")[1].get("brightness")).to_equal(100)

    await turn_off_lights(hass, [light_2.entity_id])

    calls = async_mock_service(hass, "light", "turn_on")

    now = dt_util.utcnow()
    with patch("homeassistant.core.dt_util.utcnow", return_value=now):
        await hass.services.async_call(
            scene.DOMAIN, "turn_on", {"transition": 42, "entity_id": "scene.test"}
        )
        await hass.async_block_till_done()

    expect(hass.states.get("scene.test").state).to_equal(now.isoformat())

    expect(len(calls)).to_equal(1)
    expect(calls[0].domain).to_equal("light")
    expect(calls[0].service).to_equal("turn_on")
    expect(calls[0].data.get("transition")).to_equal(42)


@test
async def restore_state(
    _enable: None = Depends(enable_custom_integrations),
    hass: HomeAssistant = Depends(_trigger_executor),
    entities: list[MockLight] = Depends(entities),
) -> None:
    """Test we restore state integration."""
    mock_restore_cache(hass, (State("scene.test", "2021-01-01T23:59:59+00:00"),))

    light_1, light_2 = await setup_lights(hass, entities)

    expect(
        await async_setup_component(
            hass,
            scene.DOMAIN,
            {
                "scene": [
                    {
                        "name": "test",
                        "entities": {
                            light_1.entity_id: "on",
                            light_2.entity_id: "on",
                        },
                    }
                ]
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()

    expect(hass.states.get("scene.test").state).to_equal(
        "2021-01-01T23:59:59+00:00"
    )


@test
async def restore_state_does_not_restore_unavailable(
    _enable: None = Depends(enable_custom_integrations),
    hass: HomeAssistant = Depends(_trigger_executor),
    entities: list[MockLight] = Depends(entities),
) -> None:
    """Test we restore state integration but ignore unavailable."""
    mock_restore_cache(hass, (State("scene.test", STATE_UNAVAILABLE),))

    light_1, light_2 = await setup_lights(hass, entities)

    expect(
        await async_setup_component(
            hass,
            scene.DOMAIN,
            {
                "scene": [
                    {
                        "name": "test",
                        "entities": {
                            light_1.entity_id: "on",
                            light_2.entity_id: "on",
                        },
                    }
                ]
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()

    expect(hass.states.get("scene.test").state).to_equal(STATE_UNKNOWN)


@test
async def services_registered(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test we register services with empty config."""
    expect(await async_setup_component(hass, "scene", {})).to_be_truthy()
    await hass.async_block_till_done()
    expect(hass.services.has_service("scene", "reload")).to_be(True)
    expect(hass.services.has_service("scene", "turn_on")).to_be(True)
    expect(hass.services.has_service("scene", "apply")).to_be(True)


@test
async def invalid_platform(
    hass: HomeAssistant = Depends(_trigger_executor),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test invalid platform."""
    await async_setup_component(
        hass, scene.DOMAIN, {scene.DOMAIN: {"platform": "does_not_exist"}}
    )
    await hass.async_block_till_done()
    expect("Invalid platform specified" in caplog.text).to_be(True)
    expect("does_not_exist" in caplog.text).to_be(True)
