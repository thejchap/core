"""Test intent_script component."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant import config as hass_config
from homeassistant.components.intent_script import CONF_ACTION, DOMAIN
from homeassistant.const import ATTR_FRIENDLY_NAME, SERVICE_RELOAD
from homeassistant.core import HomeAssistant
from homeassistant.helpers import (
    area_registry as ar,
    entity_registry as er,
    floor_registry as fr,
    intent,
    script,
)
from homeassistant.setup import async_setup_component

from tests.common import async_mock_service, get_fixture_path
from tests.hass_fixtures import (
    LogCapture,
    area_registry as area_registry_fixture,
    caplog as caplog_fixture,
    entity_registry as entity_registry_fixture,
    floor_registry as floor_registry_fixture,
    hass as hass_fixture,
    mock_network,
)
from tests.hass_tryke_helpers import expect_raises_async


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def intent_script(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test intent scripts work."""
    calls = async_mock_service(hass, "test", "service")

    await async_setup_component(
        hass,
        "intent_script",
        {
            "intent_script": {
                "HelloWorld": {
                    "description": "Intent to control a test service.",
                    "platforms": ["switch"],
                    "action": {
                        "service": "test.service",
                        "data_template": {"hello": "{{ name }}"},
                    },
                    "card": {
                        "title": "Hello {{ name }}",
                        "content": "Content for {{ name }}",
                    },
                    "speech": {"text": "Good morning {{ name }}"},
                }
            }
        },
    )

    handlers = [
        intent_handler
        for intent_handler in intent.async_get(hass)
        if intent_handler.intent_type == "HelloWorld"
    ]

    expect(len(handlers)).to_equal(1)
    handler = handlers[0]
    expect(handler.description).to_equal("Intent to control a test service.")
    expect(handler.platforms).to_equal({"switch"})

    response = await intent.async_handle(
        hass, "test", "HelloWorld", {"name": {"value": "Paulus"}}
    )

    expect(len(calls)).to_equal(1)
    expect(calls[0].data["hello"]).to_equal("Paulus")

    expect(response.speech["plain"]["speech"]).to_equal("Good morning Paulus")

    expect(bool(response.reprompt)).to_be(False)

    expect(response.card["simple"]["title"]).to_equal("Hello Paulus")
    expect(response.card["simple"]["content"]).to_equal("Content for Paulus")


@test
async def intent_script_wait_response(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test intent scripts work."""
    calls = async_mock_service(hass, "test", "service")

    await async_setup_component(
        hass,
        "intent_script",
        {
            "intent_script": {
                "HelloWorldWaitResponse": {
                    "action": {
                        "service": "test.service",
                        "data_template": {"hello": "{{ name }}"},
                    },
                    "card": {
                        "title": "Hello {{ name }}",
                        "content": "Content for {{ name }}",
                    },
                    "speech": {"text": "Good morning {{ name }}"},
                    "reprompt": {
                        "text": "I didn't hear you, {{ name }}... I said good morning!"
                    },
                }
            }
        },
    )

    handlers = [
        intent_handler
        for intent_handler in intent.async_get(hass)
        if intent_handler.intent_type == "HelloWorldWaitResponse"
    ]

    expect(len(handlers)).to_equal(1)
    handler = handlers[0]
    expect(handler.platforms is None).to_be(True)

    response = await intent.async_handle(
        hass, "test", "HelloWorldWaitResponse", {"name": {"value": "Paulus"}}
    )

    expect(len(calls)).to_equal(1)
    expect(calls[0].data["hello"]).to_equal("Paulus")

    expect(response.speech["plain"]["speech"]).to_equal("Good morning Paulus")

    expect(response.reprompt["plain"]["reprompt"]).to_equal(
        "I didn't hear you, Paulus... I said good morning!"
    )

    expect(response.card["simple"]["title"]).to_equal("Hello Paulus")
    expect(response.card["simple"]["content"]).to_equal("Content for Paulus")


@test
async def intent_script_service_response(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test intent scripts work."""
    calls = async_mock_service(
        hass, "test", "service", response={"some_key": "some value"}
    )

    await async_setup_component(
        hass,
        "intent_script",
        {
            "intent_script": {
                "HelloWorldServiceResponse": {
                    "action": [
                        {"service": "test.service", "response_variable": "result"},
                        {"stop": "", "response_variable": "result"},
                    ],
                    "speech": {
                        "text": "The service returned {{ action_response.some_key }}"
                    },
                }
            }
        },
    )

    response = await intent.async_handle(hass, "test", "HelloWorldServiceResponse")

    expect(len(calls)).to_equal(1)
    expect(bool(calls[0].return_response)).to_be(True)

    expect(response.speech["plain"]["speech"]).to_equal("The service returned some value")


@test
async def intent_script_falsy_reprompt(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test intent scripts work."""
    calls = async_mock_service(hass, "test", "service")

    await async_setup_component(
        hass,
        "intent_script",
        {
            "intent_script": {
                "HelloWorld": {
                    "action": {
                        "service": "test.service",
                        "data_template": {"hello": "{{ name }}"},
                    },
                    "card": {
                        "title": "Hello {{ name }}",
                        "content": "Content for {{ name }}",
                    },
                    "speech": {
                        "type": "ssml",
                        "text": '<speak><amazon:effect name="whispered">Good morning {{ name }}</amazon:effect></speak>',
                    },
                    "reprompt": {"text": "{{ null }}"},
                }
            }
        },
    )

    response = await intent.async_handle(
        hass, "test", "HelloWorld", {"name": {"value": "Paulus"}}
    )

    expect(len(calls)).to_equal(1)
    expect(calls[0].data["hello"]).to_equal("Paulus")

    expect(response.speech["ssml"]["speech"]).to_equal(
        '<speak><amazon:effect name="whispered">Good morning Paulus</amazon:effect></speak>'
    )

    expect(bool(response.reprompt)).to_be(False)

    expect(response.card["simple"]["title"]).to_equal("Hello Paulus")
    expect(response.card["simple"]["content"]).to_equal("Content for Paulus")


@test
async def intent_script_targets(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    area_registry: ar.AreaRegistry = Depends(area_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    floor_registry: fr.FloorRegistry = Depends(floor_registry_fixture),
) -> None:
    """Test intent scripts work."""
    calls = async_mock_service(hass, "test", "service")

    await async_setup_component(
        hass,
        "intent_script",
        {
            "intent_script": {
                "Targets": {
                    "description": "Intent to control a test service.",
                    "action": {
                        "service": "test.service",
                        "data_template": {
                            "targets": "{{ targets if targets is defined }}",
                        },
                    },
                    "speech": {
                        "text": "{{ targets.entities[0] if targets is defined }}"
                    },
                }
            }
        },
    )

    floor_1 = floor_registry.async_create("first floor")
    kitchen = area_registry.async_get_or_create("kitchen")
    area_registry.async_update(kitchen.id, floor_id=floor_1.floor_id)
    bathroom = area_registry.async_get_or_create("bathroom")
    entity_registry.async_get_or_create(
        "light",
        "demo",
        "kitchen",
        suggested_object_id="kitchen",
        original_name="overhead light",
    )
    entity_registry.async_update_entity("light.kitchen", area_id=kitchen.id)
    hass.states.async_set(
        "light.kitchen", "off", attributes={ATTR_FRIENDLY_NAME: "overhead light"}
    )
    entity_registry.async_get_or_create(
        "light",
        "demo",
        "bathroom",
        suggested_object_id="bathroom",
        original_name="overhead light",
    )
    entity_registry.async_update_entity("light.bathroom", area_id=bathroom.id)
    hass.states.async_set(
        "light.bathroom", "off", attributes={ATTR_FRIENDLY_NAME: "overhead light"}
    )

    response = await intent.async_handle(
        hass,
        "test",
        "Targets",
        {
            "name": {"value": "overhead light"},
            "domain": {"value": "light"},
            "preferred_area_id": {"value": "kitchen"},
        },
    )
    expect(len(calls)).to_equal(1)
    expect(calls[0].data["targets"]).to_equal({"entities": ["light.kitchen"]})
    expect(response.speech["plain"]["speech"]).to_equal("light.kitchen")
    calls.clear()

    response = await intent.async_handle(
        hass,
        "test",
        "Targets",
        {
            "area": {"value": "kitchen"},
            "floor": {"value": "first floor"},
        },
    )
    expect(len(calls)).to_equal(1)
    expect(calls[0].data["targets"]).to_equal(
        {
            "entities": ["light.kitchen"],
            "areas": ["kitchen"],
            "floors": ["first_floor"],
        }
    )
    calls.clear()

    response = await intent.async_handle(
        hass,
        "test",
        "Targets",
        {"device_class": {"value": "door"}},
    )
    expect(len(calls)).to_equal(1)
    expect(calls[0].data["targets"]).to_equal("")
    calls.clear()


@test
async def intent_script_action_validation(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test action validation in intent scripts."""
    calls = async_mock_service(hass, "test", "service")

    entry = entity_registry.async_get_or_create(
        "binary_sensor", "test", "1234", suggested_object_id="test_sensor"
    )
    expect(entry.entity_id).to_equal("binary_sensor.test_sensor")

    non_existent_registry_id = "abcd1234abcd1234abcd1234abcd1234"

    await async_setup_component(
        hass,
        "intent_script",
        {
            "intent_script": {
                "ChooseWithRegistryIdIntent": {
                    "action": [
                        {
                            "choose": [
                                {
                                    "conditions": [
                                        {
                                            "condition": "state",
                                            "entity_id": entry.id,
                                            "state": "on",
                                        }
                                    ],
                                    "sequence": [
                                        {
                                            "action": "test.service",
                                            "data": {"result": "sensor_on"},
                                        }
                                    ],
                                }
                            ],
                            "default": [
                                {
                                    "action": "test.service",
                                    "data": {"result": "sensor_off"},
                                }
                            ],
                        }
                    ],
                    "speech": {"text": "Done"},
                },
                "InvalidIntent": {
                    "action": [
                        {
                            "choose": [
                                {
                                    "conditions": [
                                        {
                                            "condition": "state",
                                            "entity_id": non_existent_registry_id,
                                            "state": "on",
                                        }
                                    ],
                                    "sequence": [
                                        {"action": "test.service"},
                                    ],
                                }
                            ],
                        }
                    ],
                    "speech": {"text": "Invalid"},
                },
            }
        },
    )

    expect("Failed to validate actions for intent InvalidIntent" in caplog.text).to_be(
        True
    )

    async with expect_raises_async(intent.UnknownIntent):
        await intent.async_handle(hass, "test", "InvalidIntent")

    hass.states.async_set("binary_sensor.test_sensor", "on")

    response = await intent.async_handle(hass, "test", "ChooseWithRegistryIdIntent")

    expect(len(calls)).to_equal(1)
    expect(calls[0].data["result"]).to_equal("sensor_on")
    expect(response.speech["plain"]["speech"]).to_equal("Done")

    calls.clear()

    hass.states.async_set("binary_sensor.test_sensor", "off")

    response = await intent.async_handle(hass, "test", "ChooseWithRegistryIdIntent")

    expect(len(calls)).to_equal(1)
    expect(calls[0].data["result"]).to_equal("sensor_off")
    expect(response.speech["plain"]["speech"]).to_equal("Done")


@test
async def reload(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Verify we can reload intent config."""
    config = {"intent_script": {"NewIntent1": {"speech": {"text": "HelloWorld123"}}}}

    await async_setup_component(hass, "intent_script", config)
    await hass.async_block_till_done()

    intents = hass.data.get(intent.DATA_KEY)

    expect(len(intents)).to_equal(1)
    expect(intents.get("NewIntent1") is not None).to_be(True)

    yaml_path = get_fixture_path("configuration.yaml", "intent_script")

    with patch.object(hass_config, "YAML_CONFIG_FILE", yaml_path):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_RELOAD,
            {},
            blocking=True,
        )
        await hass.async_block_till_done()

    expect(len(intents)).to_equal(1)

    expect(intents.get("NewIntent1") is None).to_be(True)
    expect(intents.get("NewIntent2") is not None).to_be(True)

    yaml_path = get_fixture_path("configuration_no_entry.yaml", "intent_script")

    with patch.object(hass_config, "YAML_CONFIG_FILE", yaml_path):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_RELOAD,
            {},
            blocking=True,
        )
        await hass.async_block_till_done()

    expect(len(intents)).to_equal(0)
    expect(intents.get("NewIntent1") is None).to_be(True)
    expect(intents.get("NewIntent2") is None).to_be(True)


@test
async def reload_unloads_scripts(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that reloading intent scripts unloads the action scripts."""
    await async_setup_component(
        hass,
        "intent_script",
        {
            "intent_script": {
                "TestIntent": {
                    "action": {"service": "test.service"},
                }
            }
        },
    )

    existing_intents = hass.data[DOMAIN]
    action_script = existing_intents["TestIntent"][CONF_ACTION]
    expect(isinstance(action_script, script.Script)).to_be(True)

    yaml_path = get_fixture_path("configuration_no_entry.yaml", "intent_script")
    with (
        patch.object(hass_config, "YAML_CONFIG_FILE", yaml_path),
        patch.object(
            action_script, "async_stop", wraps=action_script.async_stop
        ) as stop_mock,
        patch.object(
            action_script, "async_unload", wraps=action_script.async_unload
        ) as unload_mock,
    ):
        await hass.services.async_call(DOMAIN, SERVICE_RELOAD, blocking=True)
        await hass.async_block_till_done()

    stop_mock.assert_called_once()
    unload_mock.assert_called_once()
