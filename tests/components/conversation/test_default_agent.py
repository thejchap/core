"""Test for the default agent."""

from collections import defaultdict
import os
import tempfile
from typing import Any
from unittest.mock import AsyncMock, patch

from hassil.recognize import Intent, IntentData, MatchEntity, RecognizeResult
from syrupy.assertion import SnapshotAssertion
from tryke import Depends, expect, fixture, test
import yaml

from homeassistant.components import conversation, cover, media_player, weather
from homeassistant.components.conversation import (
    async_get_agent,
    default_agent,
    get_agent_manager,
)
from homeassistant.components.conversation.chat_log import (
    AssistantContent,
    ToolResultContent,
    async_get_chat_log,
)
from homeassistant.components.conversation.default_agent import METADATA_CUSTOM_SENTENCE
from homeassistant.components.conversation.models import ConversationInput
from homeassistant.components.cover import SERVICE_OPEN_COVER
from homeassistant.components.homeassistant.exposed_entities import (
    async_get_assistant_settings,
)
from homeassistant.components.intent import (
    TimerEventType,
    TimerInfo,
    async_register_timer_handler,
)
from homeassistant.components.light import (
    ATTR_SUPPORTED_COLOR_MODES,
    DOMAIN as LIGHT_DOMAIN,
    ColorMode,
    intent as light_intent,
)
from homeassistant.const import (
    ATTR_DEVICE_CLASS,
    ATTR_FRIENDLY_NAME,
    STATE_CLOSED,
    STATE_OFF,
    STATE_ON,
    STATE_UNKNOWN,
    EntityCategory,
)
from homeassistant.core import (
    DOMAIN as HOMEASSISTANT_DOMAIN,
    Context,
    HomeAssistant,
    callback,
)
from homeassistant.helpers import (
    area_registry as ar,
    chat_session,
    device_registry as dr,
    entity_registry as er,
    floor_registry as fr,
    intent,
)
from homeassistant.setup import async_setup_component

from . import expose_entity, expose_new

from ._fixtures import init_components as init_components_fixture

from tests.common import (
    MockConfigEntry,
    MockUser,
    async_mock_service,
    setup_test_component_platform,
)
from tests.components.light.common import MockLight
from tests.hass_fixtures import (
    area_registry as area_registry_fixture,
    device_registry as device_registry_fixture,
    entity_registry as entity_registry_fixture,
    floor_registry as floor_registry_fixture,
    hass as hass_fixture,
    hass_admin_user as hass_admin_user_fixture,
    mock_network as mock_network_fixture,
)
from tests.hass_tryke_helpers import snapshot as snapshot_fixture


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
    _network: None = Depends(mock_network_fixture),
    _init: None = Depends(init_components_fixture),
) -> HomeAssistant:
    """Anchor cross-module fixtures so tryke resolves before the test body."""
    return hass


class OrderBeerIntentHandler(intent.IntentHandler):
    """Handle OrderBeer intent."""

    intent_type = "OrderBeer"

    async def async_handle(self, intent_obj: intent.Intent) -> intent.IntentResponse:
        """Return speech response."""
        beer_style = intent_obj.slots["beer_style"]["value"]
        response = intent_obj.create_response()
        response.async_set_speech(f"You ordered a {beer_style}")
        return response


@fixture
async def sl_setup(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Set up the shopping list."""
    from homeassistant.components.shopping_list import intent as sl_intent

    entry = MockConfigEntry(domain="shopping_list")
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)

    await sl_intent.async_setup_intents(hass)


@test.cases(
    test.case("hidden_by_user", er_kwargs={"hidden_by": er.RegistryEntryHider.USER}),
    test.case(
        "hidden_by_integration",
        er_kwargs={"hidden_by": er.RegistryEntryHider.INTEGRATION},
    ),
    test.case("config", er_kwargs={"entity_category": EntityCategory.CONFIG}),
    test.case("diagnostic", er_kwargs={"entity_category": EntityCategory.DIAGNOSTIC}),
)
async def hidden_entities_skipped(
    er_kwargs: dict[str, Any],
    hass: HomeAssistant = Depends(_trigger_executor),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test we skip hidden entities."""
    entity_registry.async_get_or_create(
        "light", "demo", "1234", suggested_object_id="Test light", **er_kwargs
    )
    hass.states.async_set("light.test_light", "off")
    calls = async_mock_service(hass, HOMEASSISTANT_DOMAIN, "turn_on")
    result = await conversation.async_converse(
        hass, "turn on test light", None, Context(), None
    )

    expect(len(calls)).to_equal(0)
    expect(result.response.response_type).to_equal(intent.IntentResponseType.ERROR)
    expect(result.response.error_code).to_equal(
        intent.IntentResponseErrorCode.NO_VALID_TARGETS
    )


@test
async def exposed_domains(hass: HomeAssistant = Depends(_trigger_executor)) -> None:
    """Test that we can't interact with entities that aren't exposed."""
    hass.states.async_set(
        "lock.front_door", "off", attributes={ATTR_FRIENDLY_NAME: "Front Door"}
    )
    hass.states.async_set(
        "script.my_script", "off", attributes={ATTR_FRIENDLY_NAME: "My Script"}
    )

    result = await conversation.async_converse(
        hass, "unlock front door", None, Context(), None
    )
    expect(result.response.response_type).to_equal(intent.IntentResponseType.ERROR)
    expect(result.response.error_code).to_equal(
        intent.IntentResponseErrorCode.NO_VALID_TARGETS
    )

    result = await conversation.async_converse(
        hass, "run my script", None, Context(), None
    )
    expect(result.response.response_type).to_equal(intent.IntentResponseType.ERROR)
    expect(result.response.error_code).to_equal(
        intent.IntentResponseErrorCode.NO_VALID_TARGETS
    )


@test
async def exposed_areas(
    hass: HomeAssistant = Depends(_trigger_executor),
    area_registry: ar.AreaRegistry = Depends(area_registry_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test that all areas are exposed."""
    area_kitchen = area_registry.async_get_or_create("kitchen_id")
    area_kitchen = area_registry.async_update(area_kitchen.id, name="kitchen")
    area_bedroom = area_registry.async_get_or_create("bedroom_id")
    area_bedroom = area_registry.async_update(area_bedroom.id, name="bedroom")

    entry = MockConfigEntry()
    entry.add_to_hass(hass)
    kitchen_device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        connections=set(),
        identifiers={("demo", "id-1234")},
    )
    device_registry.async_update_device(kitchen_device.id, area_id=area_kitchen.id)

    kitchen_light = entity_registry.async_get_or_create("light", "demo", "1234")
    kitchen_light = entity_registry.async_update_entity(
        kitchen_light.entity_id, device_id=kitchen_device.id
    )
    hass.states.async_set(
        kitchen_light.entity_id, "on", attributes={ATTR_FRIENDLY_NAME: "kitchen light"}
    )

    bedroom_light = entity_registry.async_get_or_create("light", "demo", "5678")
    bedroom_light = entity_registry.async_update_entity(
        bedroom_light.entity_id, area_id=area_bedroom.id
    )
    hass.states.async_set(
        bedroom_light.entity_id, "on", attributes={ATTR_FRIENDLY_NAME: "bedroom light"}
    )

    expose_entity(hass, bedroom_light.entity_id, False)

    result = await conversation.async_converse(
        hass, "turn on lights in the kitchen", None, Context(), None
    )

    expect(result.response.response_type).to_equal(
        intent.IntentResponseType.ACTION_DONE
    )
    expect(result.response.intent is not None).to_be(True)
    expect(result.response.intent.slots["area"]["value"]).to_equal(area_kitchen.id)
    expect(result.response.intent.slots["area"]["text"]).to_equal(
        area_kitchen.normalized_name
    )

    result = await conversation.async_converse(
        hass, "turn on lights in the bedroom", None, Context(), None
    )

    expect(result.response.response_type).to_equal(intent.IntentResponseType.ERROR)
    expect(result.response.error_code).to_equal(
        intent.IntentResponseErrorCode.NO_VALID_TARGETS
    )

    result = await conversation.async_converse(
        hass, "how many lights are on in the bedroom?", None, Context(), None
    )
    expect(result.response.response_type).to_equal(
        intent.IntentResponseType.QUERY_ANSWER
    )


@test
async def conversation_agent(hass: HomeAssistant = Depends(_trigger_executor)) -> None:
    """Test DefaultAgent."""
    agent = async_get_agent(hass)
    with patch(
        "homeassistant.components.conversation.default_agent.get_languages",
        return_value=["dwarvish", "elvish", "entish"],
    ):
        expect(agent.supported_languages).to_equal(["dwarvish", "elvish", "entish"])

    state = hass.states.get(agent.entity_id)
    expect(state is not None).to_be(True)
    expect(state.state).to_equal(STATE_UNKNOWN)
    expect(state.attributes["supported_features"]).to_equal(
        conversation.ConversationEntityFeature.CONTROL
    )


@test
async def punctuation(hass: HomeAssistant = Depends(_trigger_executor)) -> None:
    """Test punctuation is handled properly."""
    hass.states.async_set(
        "light.test_light",
        "off",
        attributes={ATTR_FRIENDLY_NAME: "Test light"},
    )
    expose_entity(hass, "light.test_light", True)

    calls = async_mock_service(hass, "light", "turn_on")
    result = await conversation.async_converse(
        hass, "Turn?? on,, test;; light!!!", None, Context(), None
    )

    expect(len(calls)).to_equal(1)
    expect(calls[0].data["entity_id"][0]).to_equal("light.test_light")
    expect(result.response.response_type).to_equal(
        intent.IntentResponseType.ACTION_DONE
    )
    expect(result.response.intent is not None).to_be(True)
    expect(result.response.intent.slots["name"]["value"]).to_equal("test light")
    expect(result.response.intent.slots["name"]["text"]).to_equal("test light")


@test
async def expose_flag_automatically_set(
    hass: HomeAssistant = Depends(hass_fixture),
    _network: None = Depends(mock_network_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test DefaultAgent sets the expose flag on all entities automatically."""
    expect(await async_setup_component(hass, "homeassistant", {})).to_be_truthy()

    light = entity_registry.async_get_or_create("light", "demo", "1234")
    test_entity = entity_registry.async_get_or_create("test", "demo", "1234")

    expect(async_get_assistant_settings(hass, conversation.DOMAIN)).to_equal({})

    expect(await async_setup_component(hass, "conversation", {})).to_be_truthy()
    await hass.async_block_till_done()
    with patch("homeassistant.components.http.start_http_server_and_save_config"):
        await hass.async_start()

    expect(async_get_assistant_settings(hass, conversation.DOMAIN)).to_equal(
        {
            "conversation.home_assistant": {"should_expose": False},
            light.entity_id: {"should_expose": True},
            test_entity.entity_id: {"should_expose": False},
        }
    )

    new_light = "light.demo_2345"
    hass.states.async_set(new_light, "test")
    await hass.async_block_till_done()
    expect(async_get_assistant_settings(hass, conversation.DOMAIN)).to_equal(
        {
            "conversation.home_assistant": {"should_expose": False},
            light.entity_id: {"should_expose": True},
            new_light: {"should_expose": True},
            test_entity.entity_id: {"should_expose": False},
        }
    )


@test
async def unexposed_entities_skipped(
    hass: HomeAssistant = Depends(_trigger_executor),
    area_registry: ar.AreaRegistry = Depends(area_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test that unexposed entities are skipped in exposed areas."""
    area_kitchen = area_registry.async_get_or_create("kitchen_id")
    area_kitchen = area_registry.async_update(area_kitchen.id, name="kitchen")

    exposed_light = entity_registry.async_get_or_create("light", "demo", "1234")
    exposed_light = entity_registry.async_update_entity(
        exposed_light.entity_id,
        area_id=area_kitchen.id,
    )
    hass.states.async_set(exposed_light.entity_id, "off")

    unexposed_light = entity_registry.async_get_or_create("light", "demo", "5678")
    unexposed_light = entity_registry.async_update_entity(
        unexposed_light.entity_id,
        area_id=area_kitchen.id,
    )
    hass.states.async_set(unexposed_light.entity_id, "off")

    expose_entity(hass, exposed_light.entity_id, True)
    expose_entity(hass, unexposed_light.entity_id, False)

    calls = async_mock_service(hass, "light", "turn_on")
    result = await conversation.async_converse(
        hass, "turn on kitchen lights", None, Context(), None
    )

    expect(len(calls)).to_equal(1)
    expect(result.response.response_type).to_equal(
        intent.IntentResponseType.ACTION_DONE
    )
    expect(result.response.intent is not None).to_be(True)
    expect(result.response.intent.slots["area"]["value"]).to_equal(area_kitchen.id)
    expect(result.response.intent.slots["area"]["text"]).to_equal(
        area_kitchen.normalized_name
    )

    hass.states.async_set(exposed_light.entity_id, "on")
    hass.states.async_set(unexposed_light.entity_id, "on")
    result = await conversation.async_converse(
        hass, "how many lights are on in the kitchen", None, Context(), None
    )

    expect(result.response.response_type).to_equal(
        intent.IntentResponseType.QUERY_ANSWER
    )
    expect(len(result.response.matched_states)).to_equal(1)
    expect(result.response.matched_states[0].entity_id).to_equal(
        exposed_light.entity_id
    )


@test
async def duplicated_names_resolved_with_device_area(
    hass: HomeAssistant = Depends(_trigger_executor),
    area_registry: ar.AreaRegistry = Depends(area_registry_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test entities deduplication with device ID context."""
    area_kitchen = area_registry.async_get_or_create("kitchen_id")
    area_bedroom = area_registry.async_get_or_create("bedroom_id")

    kitchen_light = entity_registry.async_get_or_create("light", "demo", "1234")
    bedroom_light = entity_registry.async_get_or_create("light", "demo", "5678")

    for light in (kitchen_light, bedroom_light):
        light = entity_registry.async_update_entity(
            light.entity_id,
            name="top light",
            aliases=[er.COMPUTED_NAME, "overhead light"],
        )
        hass.states.async_set(
            light.entity_id,
            "off",
            attributes={ATTR_FRIENDLY_NAME: light.name},
        )
    kitchen_light = entity_registry.async_update_entity(
        kitchen_light.entity_id,
        area_id=area_kitchen.id,
    )
    bedroom_light = entity_registry.async_update_entity(
        bedroom_light.entity_id,
        area_id=area_bedroom.id,
    )

    entry = MockConfigEntry()
    entry.add_to_hass(hass)
    assist_device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        connections=set(),
        identifiers={("demo", "id-1234")},
    )
    assist_device = device_registry.async_update_device(
        assist_device.id,
        area_id=area_bedroom.id,
    )

    for name in ("top light", "overhead light"):
        calls = async_mock_service(hass, "light", "turn_on")
        result = await conversation.async_converse(
            hass, f"turn on {name}", None, Context(), device_id=assist_device.id
        )

        expect(len(calls)).to_equal(1)
        expect(calls[0].data["entity_id"][0]).to_equal(bedroom_light.entity_id)

        expect(result.response.response_type).to_equal(
            intent.IntentResponseType.ACTION_DONE
        )
        expect(result.response.intent is not None).to_be(True)
        expect(result.response.intent.slots.get("name", {}).get("value")).to_equal(name)
        expect(result.response.intent.slots.get("name", {}).get("text")).to_equal(name)


@test
async def trigger_sentences(hass: HomeAssistant = Depends(_trigger_executor)) -> None:
    """Test registering/unregistering/matching a few trigger sentences."""
    trigger_sentences = ["It's party time", "It is time to party"]
    trigger_response = "Cowabunga!"

    manager = get_agent_manager(hass)

    callback_mock = AsyncMock(return_value=trigger_response)
    unregister = manager.register_trigger(trigger_sentences, callback_mock)

    result = await conversation.async_converse(hass, "Not the trigger", None, Context())
    expect(result.response.response_type).to_equal(intent.IntentResponseType.ERROR)

    test_sentences = ["it's party time!", "IT IS TIME TO PARTY."]
    for sentence in test_sentences:
        callback_mock.reset_mock()
        result = await conversation.async_converse(hass, sentence, None, Context())
        expect(callback_mock.call_count).to_equal(1)
        expect(callback_mock.call_args[0][0].text).to_equal(sentence)
        expect(result.response.response_type).to_equal(
            intent.IntentResponseType.ACTION_DONE
        )
        expect(result.response.speech).to_equal(
            {"plain": {"speech": trigger_response, "extra_data": None}}
        )

    unregister()

    callback_mock.reset_mock()
    for sentence in test_sentences:
        result = await conversation.async_converse(hass, sentence, None, Context())
        expect(result.response.response_type).to_equal(
            intent.IntentResponseType.ERROR
        )

    expect(len(callback_mock.mock_calls)).to_equal(0)


@test.cases(
    test.case("en", language="en", expected="English done"),
    test.case("de", language="de", expected="German done"),
    test.case("not_translated", language="not_translated", expected="Done"),
)
async def trigger_sentence_response_translation(
    language: str,
    expected: str,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test translation of default response 'done'."""
    hass.config.language = language

    manager = get_agent_manager(hass)

    translations = {
        "en": {"component.conversation.conversation.agent.done": "English done"},
        "de": {"component.conversation.conversation.agent.done": "German done"},
        "not_translated": {},
    }

    with patch(
        "homeassistant.components.conversation.default_agent.translation.async_get_translations",
        return_value=translations.get(language),
    ):
        unregister = manager.register_trigger(
            ["test sentence"], AsyncMock(return_value=None)
        )
        result = await conversation.async_converse(
            hass, "test sentence", None, Context()
        )
        expect(result.response.response_type).to_equal(
            intent.IntentResponseType.ACTION_DONE
        )
        expect(result.response.speech).to_equal(
            {"plain": {"speech": expected, "extra_data": None}}
        )

        unregister()


@test
async def shopping_list_add_item(
    hass: HomeAssistant = Depends(_trigger_executor),
    _sl: None = Depends(sl_setup),
) -> None:
    """Test adding an item to the shopping list through the default agent."""
    result = await conversation.async_converse(
        hass, "add apples to my shopping list", None, Context()
    )
    expect(result.response.response_type).to_equal(
        intent.IntentResponseType.ACTION_DONE
    )
    expect(result.response.speech).to_equal(
        {"plain": {"speech": "Added apples", "extra_data": None}}
    )


@test
async def nevermind_intent(hass: HomeAssistant = Depends(_trigger_executor)) -> None:
    """Test HassNevermind intent through the default agent."""
    result = await conversation.async_converse(hass, "nevermind", None, Context())
    expect(result.response.intent is not None).to_be(True)
    expect(result.response.intent.intent_type).to_equal(intent.INTENT_NEVERMIND)

    expect(result.response.response_type).to_equal(
        intent.IntentResponseType.ACTION_DONE
    )
    expect(bool(result.response.speech)).to_be(False)


@test
async def respond_intent(hass: HomeAssistant = Depends(_trigger_executor)) -> None:
    """Test HassRespond intent through the default agent."""
    result = await conversation.async_converse(hass, "hello", None, Context())
    expect(result.response.intent is not None).to_be(True)
    expect(result.response.intent.intent_type).to_equal(intent.INTENT_RESPOND)

    expect(result.response.response_type).to_equal(
        intent.IntentResponseType.ACTION_DONE
    )
    expect(result.response.speech["plain"]["speech"]).to_equal(
        "Hello from Home Assistant."
    )


@test
async def satellite_area_context(
    hass: HomeAssistant = Depends(_trigger_executor),
    area_registry: ar.AreaRegistry = Depends(area_registry_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test that including a satellite will target a specific area."""
    turn_on_calls = async_mock_service(hass, "light", "turn_on")
    turn_off_calls = async_mock_service(hass, "light", "turn_off")

    area_kitchen = area_registry.async_get_or_create("kitchen_id")
    area_kitchen = area_registry.async_update(area_kitchen.id, name="kitchen")
    area_bedroom = area_registry.async_get_or_create("bedroom_id")
    area_bedroom = area_registry.async_update(area_bedroom.id, name="bedroom")

    area_lights = defaultdict(list)
    all_lights = []
    for area in (area_kitchen, area_bedroom):
        for i in range(2):
            light_entity = entity_registry.async_get_or_create(
                "light", "demo", f"{area.name}-light-{i}"
            )
            light_entity = entity_registry.async_update_entity(
                light_entity.entity_id, area_id=area.id
            )
            hass.states.async_set(
                light_entity.entity_id,
                "off",
                attributes={ATTR_FRIENDLY_NAME: f"{area.name} light {i}"},
            )
            area_lights[area.id].append(light_entity)
            all_lights.append(light_entity)

    entry = MockConfigEntry()
    entry.add_to_hass(hass)

    kitchen_satellite = entity_registry.async_get_or_create(
        "assist_satellite", "demo", "kitchen"
    )
    entity_registry.async_update_entity(
        kitchen_satellite.entity_id, area_id=area_kitchen.id
    )

    bedroom_satellite = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        connections=set(),
        identifiers={("demo", "id-satellite-bedroom")},
    )
    device_registry.async_update_device(bedroom_satellite.id, area_id=area_bedroom.id)

    result = await conversation.async_converse(
        hass,
        "turn on the lights",
        None,
        Context(),
        None,
        satellite_id=kitchen_satellite.entity_id,
    )
    await hass.async_block_till_done()
    expect(result.response.response_type).to_equal(
        intent.IntentResponseType.ACTION_DONE
    )
    expect(result.response.intent is not None).to_be(True)
    expect(result.response.intent.slots["area"]["value"]).to_equal(area_kitchen.id)
    expect(result.response.intent.slots["area"]["text"]).to_equal(
        area_kitchen.normalized_name
    )

    expect({s.entity_id for s in result.response.matched_states}).to_equal(
        {e.entity_id for e in area_lights[area_kitchen.id]}
    )
    expect({c.data["entity_id"][0] for c in turn_on_calls}).to_equal(
        {e.entity_id for e in area_lights[area_kitchen.id]}
    )
    turn_on_calls.clear()

    result = await conversation.async_converse(
        hass,
        "turn on lights in the bedroom",
        None,
        Context(),
        None,
        satellite_id=kitchen_satellite.entity_id,
    )
    await hass.async_block_till_done()
    expect(result.response.response_type).to_equal(
        intent.IntentResponseType.ACTION_DONE
    )
    expect(result.response.intent is not None).to_be(True)
    expect(result.response.intent.slots["area"]["value"]).to_equal(area_bedroom.id)
    expect(result.response.intent.slots["area"]["text"]).to_equal(
        area_bedroom.normalized_name
    )

    expect({s.entity_id for s in result.response.matched_states}).to_equal(
        {e.entity_id for e in area_lights[area_bedroom.id]}
    )
    expect({c.data["entity_id"][0] for c in turn_on_calls}).to_equal(
        {e.entity_id for e in area_lights[area_bedroom.id]}
    )
    turn_on_calls.clear()

    result = await conversation.async_converse(
        hass,
        "turn lights off",
        None,
        Context(),
        None,
        device_id=bedroom_satellite.id,
    )
    await hass.async_block_till_done()
    expect(result.response.response_type).to_equal(
        intent.IntentResponseType.ACTION_DONE
    )
    expect(result.response.intent is not None).to_be(True)
    expect(result.response.intent.slots["area"]["value"]).to_equal(area_bedroom.id)
    expect(result.response.intent.slots["area"]["text"]).to_equal(
        area_bedroom.normalized_name
    )

    expect({s.entity_id for s in result.response.matched_states}).to_equal(
        {e.entity_id for e in area_lights[area_bedroom.id]}
    )
    expect({c.data["entity_id"][0] for c in turn_off_calls}).to_equal(
        {e.entity_id for e in area_lights[area_bedroom.id]}
    )
    turn_off_calls.clear()

    for command in ("on", "off"):
        result = await conversation.async_converse(
            hass, f"turn {command} all lights", None, Context(), None
        )
        await hass.async_block_till_done()
        expect(result.response.response_type).to_equal(
            intent.IntentResponseType.ACTION_DONE
        )

        expect({s.entity_id for s in result.response.matched_states}).to_equal(
            {e.entity_id for e in all_lights}
        )


@test
async def error_no_device(hass: HomeAssistant = Depends(_trigger_executor)) -> None:
    """Test error message when device/entity doesn't exist."""
    result = await conversation.async_converse(
        hass, "turn on missing entity", None, Context(), None
    )

    expect(result.response.response_type).to_equal(intent.IntentResponseType.ERROR)
    expect(result.response.error_code).to_equal(
        intent.IntentResponseErrorCode.NO_VALID_TARGETS
    )
    expect(result.response.speech["plain"]["speech"]).to_equal(
        "Sorry, I am not aware of any device called missing entity"
    )


@test
async def error_no_device_exposed(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test error message when device/entity exists but is not exposed."""
    hass.states.async_set("light.kitchen_light", "off")
    expose_entity(hass, "light.kitchen_light", False)

    result = await conversation.async_converse(
        hass, "turn on kitchen light", None, Context(), None
    )

    expect(result.response.response_type).to_equal(intent.IntentResponseType.ERROR)
    expect(result.response.error_code).to_equal(
        intent.IntentResponseErrorCode.NO_VALID_TARGETS
    )
    expect(result.response.speech["plain"]["speech"]).to_equal(
        "Sorry, kitchen light is not exposed"
    )


@test
async def error_no_area(hass: HomeAssistant = Depends(_trigger_executor)) -> None:
    """Test error message when area doesn't exist."""
    result = await conversation.async_converse(
        hass, "turn on the lights in missing area", None, Context(), None
    )

    expect(result.response.response_type).to_equal(intent.IntentResponseType.ERROR)
    expect(result.response.error_code).to_equal(
        intent.IntentResponseErrorCode.NO_VALID_TARGETS
    )
    expect(result.response.speech["plain"]["speech"]).to_equal(
        "Sorry, I am not aware of any area called missing area"
    )


@test
async def error_no_floor(hass: HomeAssistant = Depends(_trigger_executor)) -> None:
    """Test error message when floor doesn't exist."""
    result = await conversation.async_converse(
        hass, "turn on all the lights on missing floor", None, Context(), None
    )

    expect(result.response.response_type).to_equal(intent.IntentResponseType.ERROR)
    expect(result.response.error_code).to_equal(
        intent.IntentResponseErrorCode.NO_VALID_TARGETS
    )
    expect(result.response.speech["plain"]["speech"]).to_equal(
        "Sorry, I am not aware of any floor called missing"
    )


@test
async def error_no_device_in_area(
    hass: HomeAssistant = Depends(_trigger_executor),
    area_registry: ar.AreaRegistry = Depends(area_registry_fixture),
) -> None:
    """Test error message when area exists but is does not contain a device/entity."""
    area_kitchen = area_registry.async_get_or_create("kitchen_id")
    area_kitchen = area_registry.async_update(area_kitchen.id, name="kitchen")
    result = await conversation.async_converse(
        hass, "turn on missing entity in the kitchen", None, Context(), None
    )

    expect(result.response.response_type).to_equal(intent.IntentResponseType.ERROR)
    expect(result.response.error_code).to_equal(
        intent.IntentResponseErrorCode.NO_VALID_TARGETS
    )
    expect(result.response.speech["plain"]["speech"]).to_equal(
        "Sorry, I am not aware of any device called missing entity in the kitchen area"
    )


@test
async def error_no_device_on_floor(
    hass: HomeAssistant = Depends(_trigger_executor),
    floor_registry: fr.FloorRegistry = Depends(floor_registry_fixture),
) -> None:
    """Test error message when floor exists but is does not contain a device/entity."""
    floor_registry.async_create("ground")
    result = await conversation.async_converse(
        hass, "turn on missing entity on ground floor", None, Context(), None
    )

    expect(result.response.response_type).to_equal(intent.IntentResponseType.ERROR)
    expect(result.response.error_code).to_equal(
        intent.IntentResponseErrorCode.NO_VALID_TARGETS
    )
    expect(result.response.speech["plain"]["speech"]).to_equal(
        "Sorry, I am not aware of any device called missing entity on ground floor"
    )


@test
async def error_no_device_on_floor_exposed(
    hass: HomeAssistant = Depends(_trigger_executor),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    area_registry: ar.AreaRegistry = Depends(area_registry_fixture),
    floor_registry: fr.FloorRegistry = Depends(floor_registry_fixture),
) -> None:
    """Test error message when a device/entity exists on a floor but isn't exposed."""
    floor_ground = floor_registry.async_create("ground")

    area_kitchen = area_registry.async_get_or_create("kitchen_id")
    area_kitchen = area_registry.async_update(
        area_kitchen.id, name="kitchen", floor_id=floor_ground.floor_id
    )

    kitchen_light = entity_registry.async_get_or_create("light", "demo", "1234")
    kitchen_light = entity_registry.async_update_entity(
        kitchen_light.entity_id,
        name="test light",
        area_id=area_kitchen.id,
    )
    hass.states.async_set(
        kitchen_light.entity_id,
        "off",
        attributes={ATTR_FRIENDLY_NAME: kitchen_light.name},
    )
    expose_entity(hass, kitchen_light.entity_id, False)
    await hass.async_block_till_done()

    name = MatchEntity(name="name", value=kitchen_light.name, text=kitchen_light.name)
    floor = MatchEntity(name="floor", value=floor_ground.name, text=floor_ground.name)
    recognize_result = RecognizeResult(
        intent=Intent("HassTurnOn"),
        intent_data=IntentData([]),
        entities={"name": name, "floor": floor},
        entities_list=[name, floor],
    )

    with patch(
        "homeassistant.components.conversation.default_agent.recognize_best",
        return_value=recognize_result,
    ):
        result = await conversation.async_converse(
            hass, "turn on test light on the ground floor", None, Context(), None
        )

        expect(result.response.response_type).to_equal(
            intent.IntentResponseType.ERROR
        )
        expect(result.response.error_code).to_equal(
            intent.IntentResponseErrorCode.NO_VALID_TARGETS
        )
        expect(result.response.speech["plain"]["speech"]).to_equal(
            "Sorry, test light in the ground floor is not exposed"
        )


@test
async def error_no_device_in_area_exposed(
    hass: HomeAssistant = Depends(_trigger_executor),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    area_registry: ar.AreaRegistry = Depends(area_registry_fixture),
) -> None:
    """Test error message when a device/entity exists in an area but isn't exposed."""
    area_kitchen = area_registry.async_get_or_create("kitchen_id")
    area_kitchen = area_registry.async_update(area_kitchen.id, name="kitchen")

    kitchen_light = entity_registry.async_get_or_create("light", "demo", "1234")
    kitchen_light = entity_registry.async_update_entity(
        kitchen_light.entity_id,
        name="test light",
        area_id=area_kitchen.id,
    )
    hass.states.async_set(
        kitchen_light.entity_id,
        "off",
        attributes={ATTR_FRIENDLY_NAME: kitchen_light.name},
    )
    expose_entity(hass, kitchen_light.entity_id, False)
    await hass.async_block_till_done()

    result = await conversation.async_converse(
        hass, "turn on test light in the kitchen", None, Context(), None
    )

    expect(result.response.response_type).to_equal(intent.IntentResponseType.ERROR)
    expect(result.response.error_code).to_equal(
        intent.IntentResponseErrorCode.NO_VALID_TARGETS
    )
    expect(result.response.speech["plain"]["speech"]).to_equal(
        "Sorry, test light in the kitchen area is not exposed"
    )


@test
async def error_no_domain(hass: HomeAssistant = Depends(_trigger_executor)) -> None:
    """Test error message when no devices/entities exist for a domain."""
    fan_domain = MatchEntity(name="domain", value="fan", text="fans")
    recognize_result = RecognizeResult(
        intent=Intent("HassTurnOn"),
        intent_data=IntentData([]),
        entities={"domain": fan_domain},
        entities_list=[fan_domain],
    )

    with patch(
        "homeassistant.components.conversation.default_agent.recognize_best",
        return_value=recognize_result,
    ):
        result = await conversation.async_converse(
            hass, "turn on the fans", None, Context(), None
        )

        expect(result.response.response_type).to_equal(
            intent.IntentResponseType.ERROR
        )
        expect(result.response.error_code).to_equal(
            intent.IntentResponseErrorCode.NO_VALID_TARGETS
        )
        expect(result.response.speech["plain"]["speech"]).to_equal(
            "Sorry, I am not aware of any fan"
        )


@test
async def error_no_domain_exposed(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test error message when devices/entities exist for a domain but are not exposed."""
    hass.states.async_set("fan.test_fan", "off")
    expose_entity(hass, "fan.test_fan", False)
    await hass.async_block_till_done()

    fan_domain = MatchEntity(name="domain", value="fan", text="fans")
    recognize_result = RecognizeResult(
        intent=Intent("HassTurnOn"),
        intent_data=IntentData([]),
        entities={"domain": fan_domain},
        entities_list=[fan_domain],
    )

    with patch(
        "homeassistant.components.conversation.default_agent.recognize_best",
        return_value=recognize_result,
    ):
        result = await conversation.async_converse(
            hass, "turn on the fans", None, Context(), None
        )

        expect(result.response.response_type).to_equal(
            intent.IntentResponseType.ERROR
        )
        expect(result.response.error_code).to_equal(
            intent.IntentResponseErrorCode.NO_VALID_TARGETS
        )
        expect(result.response.speech["plain"]["speech"]).to_equal(
            "Sorry, no fan is exposed"
        )


@test
async def error_no_domain_in_area(
    hass: HomeAssistant = Depends(_trigger_executor),
    area_registry: ar.AreaRegistry = Depends(area_registry_fixture),
) -> None:
    """Test error message when no devices/entities for a domain exist in an area."""
    area_kitchen = area_registry.async_get_or_create("kitchen_id")
    area_kitchen = area_registry.async_update(area_kitchen.id, name="kitchen")
    result = await conversation.async_converse(
        hass, "turn on the lights in the kitchen", None, Context(), None
    )

    expect(result.response.response_type).to_equal(intent.IntentResponseType.ERROR)
    expect(result.response.error_code).to_equal(
        intent.IntentResponseErrorCode.NO_VALID_TARGETS
    )
    expect(result.response.speech["plain"]["speech"]).to_equal(
        "Sorry, I am not aware of any light in the kitchen area"
    )


@test
async def error_no_domain_in_area_exposed(
    hass: HomeAssistant = Depends(_trigger_executor),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    area_registry: ar.AreaRegistry = Depends(area_registry_fixture),
) -> None:
    """Test error message when devices for a domain exist in an area but unexposed."""
    area_kitchen = area_registry.async_get_or_create("kitchen_id")
    area_kitchen = area_registry.async_update(area_kitchen.id, name="kitchen")

    kitchen_light = entity_registry.async_get_or_create("light", "demo", "1234")
    kitchen_light = entity_registry.async_update_entity(
        kitchen_light.entity_id,
        name="test light",
        area_id=area_kitchen.id,
    )
    hass.states.async_set(
        kitchen_light.entity_id,
        "off",
        attributes={ATTR_FRIENDLY_NAME: kitchen_light.name},
    )
    expose_entity(hass, kitchen_light.entity_id, False)
    await hass.async_block_till_done()

    result = await conversation.async_converse(
        hass, "turn on the lights in the kitchen", None, Context(), None
    )

    expect(result.response.response_type).to_equal(intent.IntentResponseType.ERROR)
    expect(result.response.error_code).to_equal(
        intent.IntentResponseErrorCode.NO_VALID_TARGETS
    )
    expect(result.response.speech["plain"]["speech"]).to_equal(
        "Sorry, no light in the kitchen area is exposed"
    )


@test
async def error_no_domain_on_floor(
    hass: HomeAssistant = Depends(_trigger_executor),
    area_registry: ar.AreaRegistry = Depends(area_registry_fixture),
    floor_registry: fr.FloorRegistry = Depends(floor_registry_fixture),
) -> None:
    """Test error message when no devices/entities for a domain exist on a floor."""
    floor_ground = floor_registry.async_create("ground")
    area_kitchen = area_registry.async_get_or_create("kitchen_id")
    area_kitchen = area_registry.async_update(
        area_kitchen.id, name="kitchen", floor_id=floor_ground.floor_id
    )
    result = await conversation.async_converse(
        hass, "turn on all lights on the ground floor", None, Context(), None
    )

    expect(result.response.response_type).to_equal(intent.IntentResponseType.ERROR)
    expect(result.response.error_code).to_equal(
        intent.IntentResponseErrorCode.NO_VALID_TARGETS
    )
    expect(result.response.speech["plain"]["speech"]).to_equal(
        "Sorry, I am not aware of any light on the ground floor"
    )

    floor_upstairs = floor_registry.async_create("upstairs")
    area_bedroom = area_registry.async_get_or_create("bedroom_id")
    area_bedroom = area_registry.async_update(
        area_bedroom.id, name="bedroom", floor_id=floor_upstairs.floor_id
    )

    result = await conversation.async_converse(
        hass, "turn on all lights upstairs", None, Context(), None
    )

    expect(result.response.response_type).to_equal(intent.IntentResponseType.ERROR)
    expect(result.response.error_code).to_equal(
        intent.IntentResponseErrorCode.NO_VALID_TARGETS
    )
    expect(result.response.speech["plain"]["speech"]).to_equal(
        "Sorry, I am not aware of any light on the upstairs floor"
    )


@test
async def error_no_domain_on_floor_exposed(
    hass: HomeAssistant = Depends(_trigger_executor),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    area_registry: ar.AreaRegistry = Depends(area_registry_fixture),
    floor_registry: fr.FloorRegistry = Depends(floor_registry_fixture),
) -> None:
    """Test error message when devices for a domain exist on a floor but unexposed."""
    floor_ground = floor_registry.async_create("ground")
    area_kitchen = area_registry.async_get_or_create("kitchen_id")
    area_kitchen = area_registry.async_update(
        area_kitchen.id, name="kitchen", floor_id=floor_ground.floor_id
    )
    kitchen_light = entity_registry.async_get_or_create("light", "demo", "1234")
    kitchen_light = entity_registry.async_update_entity(
        kitchen_light.entity_id,
        name="test light",
        area_id=area_kitchen.id,
    )
    hass.states.async_set(
        kitchen_light.entity_id,
        "off",
        attributes={ATTR_FRIENDLY_NAME: kitchen_light.name},
    )
    expose_entity(hass, kitchen_light.entity_id, False)
    await hass.async_block_till_done()

    result = await conversation.async_converse(
        hass, "turn on all lights on the ground floor", None, Context(), None
    )

    expect(result.response.response_type).to_equal(intent.IntentResponseType.ERROR)
    expect(result.response.error_code).to_equal(
        intent.IntentResponseErrorCode.NO_VALID_TARGETS
    )
    expect(result.response.speech["plain"]["speech"]).to_equal(
        "Sorry, no light in the ground floor is exposed"
    )


@test
async def error_no_device_class(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test error message when no entities of a device class exist."""
    hass.states.async_set(
        "cover.garage_door",
        STATE_CLOSED,
        attributes={ATTR_DEVICE_CLASS: cover.CoverDeviceClass.GARAGE},
    )

    cover_domain = MatchEntity(name="domain", value="cover", text="cover")
    window_class = MatchEntity(name="device_class", value="window", text="windows")
    recognize_result = RecognizeResult(
        intent=Intent("HassTurnOn"),
        intent_data=IntentData([]),
        entities={"domain": cover_domain, "device_class": window_class},
        entities_list=[cover_domain, window_class],
    )

    with patch(
        "homeassistant.components.conversation.default_agent.recognize_best",
        return_value=recognize_result,
    ):
        result = await conversation.async_converse(
            hass, "open the windows", None, Context(), None
        )

        expect(result.response.response_type).to_equal(
            intent.IntentResponseType.ERROR
        )
        expect(result.response.error_code).to_equal(
            intent.IntentResponseErrorCode.NO_VALID_TARGETS
        )
        expect(result.response.speech["plain"]["speech"]).to_equal(
            "Sorry, I am not aware of any window"
        )


@test
async def error_no_device_class_exposed(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test error message when entities of a device class exist but aren't exposed."""
    hass.states.async_set(
        "cover.garage_door",
        STATE_CLOSED,
        attributes={ATTR_DEVICE_CLASS: cover.CoverDeviceClass.GARAGE},
    )

    hass.states.async_set(
        "cover.test_window",
        STATE_CLOSED,
        attributes={ATTR_DEVICE_CLASS: cover.CoverDeviceClass.WINDOW},
    )
    expose_entity(hass, "cover.test_window", False)

    cover_domain = MatchEntity(name="domain", value="cover", text="cover")
    window_class = MatchEntity(name="device_class", value="window", text="windows")
    recognize_result = RecognizeResult(
        intent=Intent("HassTurnOn"),
        intent_data=IntentData([]),
        entities={"domain": cover_domain, "device_class": window_class},
        entities_list=[cover_domain, window_class],
    )

    with patch(
        "homeassistant.components.conversation.default_agent.recognize_best",
        return_value=recognize_result,
    ):
        result = await conversation.async_converse(
            hass, "open all the windows", None, Context(), None
        )

        expect(result.response.response_type).to_equal(
            intent.IntentResponseType.ERROR
        )
        expect(result.response.error_code).to_equal(
            intent.IntentResponseErrorCode.NO_VALID_TARGETS
        )
        expect(result.response.speech["plain"]["speech"]).to_equal(
            "Sorry, no window is exposed"
        )


@test
async def error_no_device_class_in_area(
    hass: HomeAssistant = Depends(_trigger_executor),
    area_registry: ar.AreaRegistry = Depends(area_registry_fixture),
) -> None:
    """Test error message when no entities of a device class exist in an area."""
    area_bedroom = area_registry.async_get_or_create("bedroom_id")
    area_bedroom = area_registry.async_update(area_bedroom.id, name="bedroom")
    result = await conversation.async_converse(
        hass, "open bedroom windows", None, Context(), None
    )

    expect(result.response.response_type).to_equal(intent.IntentResponseType.ERROR)
    expect(result.response.error_code).to_equal(
        intent.IntentResponseErrorCode.NO_VALID_TARGETS
    )
    expect(result.response.speech["plain"]["speech"]).to_equal(
        "Sorry, I am not aware of any window in the bedroom area"
    )


@test
async def error_no_device_class_in_area_exposed(
    hass: HomeAssistant = Depends(_trigger_executor),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    area_registry: ar.AreaRegistry = Depends(area_registry_fixture),
) -> None:
    """Test error message when device class entities exist in an area but unexposed."""
    area_bedroom = area_registry.async_get_or_create("bedroom_id")
    area_bedroom = area_registry.async_update(area_bedroom.id, name="bedroom")
    bedroom_window = entity_registry.async_get_or_create("cover", "demo", "1234")
    bedroom_window = entity_registry.async_update_entity(
        bedroom_window.entity_id,
        name="test cover",
        area_id=area_bedroom.id,
    )
    hass.states.async_set(
        bedroom_window.entity_id,
        "off",
        attributes={ATTR_DEVICE_CLASS: cover.CoverDeviceClass.WINDOW},
    )
    expose_entity(hass, bedroom_window.entity_id, False)
    await hass.async_block_till_done()

    result = await conversation.async_converse(
        hass, "open bedroom windows", None, Context(), None
    )

    expect(result.response.response_type).to_equal(intent.IntentResponseType.ERROR)
    expect(result.response.error_code).to_equal(
        intent.IntentResponseErrorCode.NO_VALID_TARGETS
    )
    expect(result.response.speech["plain"]["speech"]).to_equal(
        "Sorry, no window in the bedroom area is exposed"
    )


@test
async def error_no_device_class_on_floor_exposed(
    hass: HomeAssistant = Depends(_trigger_executor),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    area_registry: ar.AreaRegistry = Depends(area_registry_fixture),
    floor_registry: fr.FloorRegistry = Depends(floor_registry_fixture),
) -> None:
    """Test error message when device class entities exist on a floor but unexposed."""
    floor_ground = floor_registry.async_create("ground")

    area_bedroom = area_registry.async_get_or_create("bedroom_id")
    area_bedroom = area_registry.async_update(
        area_bedroom.id, name="bedroom", floor_id=floor_ground.floor_id
    )
    bedroom_window = entity_registry.async_get_or_create("cover", "demo", "1234")
    bedroom_window = entity_registry.async_update_entity(
        bedroom_window.entity_id,
        name="test cover",
        area_id=area_bedroom.id,
    )
    hass.states.async_set(
        bedroom_window.entity_id,
        "off",
        attributes={ATTR_DEVICE_CLASS: cover.CoverDeviceClass.WINDOW},
    )
    expose_entity(hass, bedroom_window.entity_id, False)
    await hass.async_block_till_done()

    cover_domain = MatchEntity(name="domain", value="cover", text="cover")
    window_class = MatchEntity(name="device_class", value="window", text="windows")
    floor = MatchEntity(name="floor", value=floor_ground.name, text=floor_ground.name)
    recognize_result = RecognizeResult(
        intent=Intent("HassTurnOn"),
        intent_data=IntentData([]),
        entities={"domain": cover_domain, "device_class": window_class, "floor": floor},
        entities_list=[cover_domain, window_class, floor],
    )

    with patch(
        "homeassistant.components.conversation.default_agent.recognize_best",
        return_value=recognize_result,
    ):
        result = await conversation.async_converse(
            hass, "open ground floor windows", None, Context(), None
        )

        expect(result.response.response_type).to_equal(
            intent.IntentResponseType.ERROR
        )
        expect(result.response.error_code).to_equal(
            intent.IntentResponseErrorCode.NO_VALID_TARGETS
        )
        expect(result.response.speech["plain"]["speech"]).to_equal(
            "Sorry, no window in the ground floor is exposed"
        )


@test
async def error_no_intent(hass: HomeAssistant = Depends(_trigger_executor)) -> None:
    """Test response with an intent match failure."""
    with patch(
        "homeassistant.components.conversation.default_agent.recognize_best",
        return_value=None,
    ):
        result = await conversation.async_converse(
            hass, "do something", None, Context(), None
        )

        expect(result.response.response_type).to_equal(
            intent.IntentResponseType.ERROR
        )
        expect(result.response.error_code).to_equal(
            intent.IntentResponseErrorCode.NO_INTENT_MATCH
        )
        expect(result.response.speech["plain"]["speech"]).to_equal(
            "Sorry, I couldn't understand that"
        )


@test
async def error_duplicate_names(
    hass: HomeAssistant = Depends(_trigger_executor),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test error message when multiple devices have the same name (or alias)."""
    kitchen_light_1 = entity_registry.async_get_or_create("light", "demo", "1234")
    kitchen_light_2 = entity_registry.async_get_or_create("light", "demo", "5678")

    for light in (kitchen_light_1, kitchen_light_2):
        light = entity_registry.async_update_entity(
            light.entity_id,
            name="kitchen light",
            aliases=[er.COMPUTED_NAME, "overhead light"],
        )
        hass.states.async_set(
            light.entity_id,
            "off",
            attributes={ATTR_FRIENDLY_NAME: light.name},
        )

    for name in ("kitchen light", "overhead light"):
        result = await conversation.async_converse(
            hass, f"turn on {name}", None, Context(), None
        )
        expect(result.response.response_type).to_equal(
            intent.IntentResponseType.ERROR
        )
        expect(result.response.error_code).to_equal(
            intent.IntentResponseErrorCode.NO_VALID_TARGETS
        )
        expect(result.response.speech["plain"]["speech"]).to_equal(
            f"Sorry, there are multiple devices called {name}"
        )

        result = await conversation.async_converse(
            hass, f"is {name} on?", None, Context(), None
        )
        expect(result.response.response_type).to_equal(
            intent.IntentResponseType.ERROR
        )
        expect(result.response.error_code).to_equal(
            intent.IntentResponseErrorCode.NO_VALID_TARGETS
        )
        expect(result.response.speech["plain"]["speech"]).to_equal(
            f"Sorry, there are multiple devices called {name}"
        )


@test
async def duplicate_names_but_one_is_exposed(
    hass: HomeAssistant = Depends(_trigger_executor),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test multiple devices with the same name, only one of which is exposed."""
    kitchen_light_1 = entity_registry.async_get_or_create("light", "demo", "1234")
    kitchen_light_2 = entity_registry.async_get_or_create("light", "demo", "5678")

    for light in (kitchen_light_1, kitchen_light_2):
        light = entity_registry.async_update_entity(
            light.entity_id,
            name="kitchen light",
            aliases=[er.COMPUTED_NAME, "overhead light"],
        )
        hass.states.async_set(
            light.entity_id,
            "off",
            attributes={ATTR_FRIENDLY_NAME: light.name},
        )

    expose_entity(hass, kitchen_light_1.entity_id, True)
    expose_entity(hass, kitchen_light_2.entity_id, False)

    async_mock_service(hass, "light", "turn_on")
    for name in ("kitchen light", "overhead light"):
        result = await conversation.async_converse(
            hass, f"turn on {name}", None, Context(), None
        )
        expect(result.response.response_type).to_equal(
            intent.IntentResponseType.ACTION_DONE
        )
        expect(result.response.matched_states[0].entity_id).to_equal(
            kitchen_light_1.entity_id
        )


@test
async def error_duplicate_names_same_area(
    hass: HomeAssistant = Depends(_trigger_executor),
    area_registry: ar.AreaRegistry = Depends(area_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test error message when multiple devices have the same name in the same area."""
    area_kitchen = area_registry.async_get_or_create("kitchen_id")
    area_kitchen = area_registry.async_update(area_kitchen.id, name="kitchen")

    kitchen_light_1 = entity_registry.async_get_or_create("light", "demo", "1234")
    kitchen_light_2 = entity_registry.async_get_or_create("light", "demo", "5678")

    for light in (kitchen_light_1, kitchen_light_2):
        light = entity_registry.async_update_entity(
            light.entity_id,
            name="kitchen light",
            area_id=area_kitchen.id,
            aliases=[er.COMPUTED_NAME, "overhead light"],
        )
        hass.states.async_set(
            light.entity_id,
            "off",
            attributes={ATTR_FRIENDLY_NAME: light.name},
        )

    for name in ("kitchen light", "overhead light"):
        result = await conversation.async_converse(
            hass, f"turn on {name} in {area_kitchen.name}", None, Context(), None
        )
        expect(result.response.response_type).to_equal(
            intent.IntentResponseType.ERROR
        )
        expect(result.response.error_code).to_equal(
            intent.IntentResponseErrorCode.NO_VALID_TARGETS
        )
        expect(result.response.speech["plain"]["speech"]).to_equal(
            f"Sorry, there are multiple devices called {name} in the "
            f"{area_kitchen.name} area"
        )

        result = await conversation.async_converse(
            hass, f"is {name} on in the {area_kitchen.name}?", None, Context(), None
        )
        expect(result.response.response_type).to_equal(
            intent.IntentResponseType.ERROR
        )
        expect(result.response.error_code).to_equal(
            intent.IntentResponseErrorCode.NO_VALID_TARGETS
        )
        expect(result.response.speech["plain"]["speech"]).to_equal(
            f"Sorry, there are multiple devices called {name} in the "
            f"{area_kitchen.name} area"
        )


@test
async def duplicate_names_same_area_but_one_is_exposed(
    hass: HomeAssistant = Depends(_trigger_executor),
    area_registry: ar.AreaRegistry = Depends(area_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test multiple same-named devices in an area, only one of which is exposed."""
    area_kitchen = area_registry.async_get_or_create("kitchen_id")
    area_kitchen = area_registry.async_update(area_kitchen.id, name="kitchen")

    kitchen_light_1 = entity_registry.async_get_or_create("light", "demo", "1234")
    kitchen_light_2 = entity_registry.async_get_or_create("light", "demo", "5678")

    for light in (kitchen_light_1, kitchen_light_2):
        light = entity_registry.async_update_entity(
            light.entity_id,
            name="kitchen light",
            area_id=area_kitchen.id,
            aliases=[er.COMPUTED_NAME, "overhead light"],
        )
        hass.states.async_set(
            light.entity_id,
            "off",
            attributes={ATTR_FRIENDLY_NAME: light.name},
        )

    expose_entity(hass, kitchen_light_1.entity_id, True)
    expose_entity(hass, kitchen_light_2.entity_id, False)

    async_mock_service(hass, "light", "turn_on")
    for name in ("kitchen light", "overhead light"):
        result = await conversation.async_converse(
            hass, f"turn on {name} in {area_kitchen.name}", None, Context(), None
        )
        expect(result.response.response_type).to_equal(
            intent.IntentResponseType.ACTION_DONE
        )
        expect(result.response.matched_states[0].entity_id).to_equal(
            kitchen_light_1.entity_id
        )


@test
async def duplicate_names_different_areas(
    hass: HomeAssistant = Depends(_trigger_executor),
    area_registry: ar.AreaRegistry = Depends(area_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test preferred area when same-named devices are in different areas."""
    area_kitchen = area_registry.async_get_or_create("kitchen_id")
    area_kitchen = area_registry.async_update(area_kitchen.id, name="kitchen")

    area_bedroom = area_registry.async_get_or_create("bedroom_id")
    area_bedroom = area_registry.async_update(area_bedroom.id, name="bedroom")

    kitchen_light = entity_registry.async_get_or_create("light", "demo", "1234")
    kitchen_light = entity_registry.async_update_entity(
        kitchen_light.entity_id, area_id=area_kitchen.id
    )
    bedroom_light = entity_registry.async_get_or_create("light", "demo", "5678")
    bedroom_light = entity_registry.async_update_entity(
        bedroom_light.entity_id, area_id=area_bedroom.id
    )

    for light in (kitchen_light, bedroom_light):
        light = entity_registry.async_update_entity(
            light.entity_id,
            name="test light",
            aliases=[er.COMPUTED_NAME, "overhead light"],
        )
        hass.states.async_set(
            light.entity_id,
            "off",
            attributes={ATTR_FRIENDLY_NAME: light.name},
        )

    kitchen_entry = MockConfigEntry()
    kitchen_entry.add_to_hass(hass)
    device_kitchen = device_registry.async_get_or_create(
        config_entry_id=kitchen_entry.entry_id,
        connections=set(),
        identifiers={("demo", "device-kitchen")},
    )
    device_registry.async_update_device(device_kitchen.id, area_id=area_kitchen.id)

    bedroom_entry = MockConfigEntry()
    bedroom_entry.add_to_hass(hass)
    device_bedroom = device_registry.async_get_or_create(
        config_entry_id=bedroom_entry.entry_id,
        connections=set(),
        identifiers={("demo", "device-bedroom")},
    )
    device_registry.async_update_device(device_bedroom.id, area_id=area_bedroom.id)

    async_mock_service(hass, "light", "turn_on")
    for name in ("test light", "overhead light"):
        result = await conversation.async_converse(
            hass, f"turn on {name}", None, Context(), None
        )
        expect(result.response.response_type).to_equal(
            intent.IntentResponseType.ERROR
        )

        result = await conversation.async_converse(
            hass, f"turn on {name}", None, Context(), None, device_id=device_kitchen.id
        )
        expect(result.response.response_type).to_equal(
            intent.IntentResponseType.ACTION_DONE
        )
        expect(result.response.matched_states[0].entity_id).to_equal(
            kitchen_light.entity_id
        )

        result = await conversation.async_converse(
            hass, f"turn on {name}", None, Context(), None, device_id=device_bedroom.id
        )
        expect(result.response.response_type).to_equal(
            intent.IntentResponseType.ACTION_DONE
        )
        expect(result.response.matched_states[0].entity_id).to_equal(
            bedroom_light.entity_id
        )


@test
async def error_wrong_state(hass: HomeAssistant = Depends(_trigger_executor)) -> None:
    """Test error message when no entities are in the correct state."""
    expect(await async_setup_component(hass, media_player.DOMAIN, {})).to_be_truthy()

    hass.states.async_set(
        "media_player.test_player",
        media_player.STATE_IDLE,
        {ATTR_FRIENDLY_NAME: "test player"},
    )

    result = await conversation.async_converse(
        hass, "pause test player", None, Context(), None
    )

    expect(result.response.response_type).to_equal(intent.IntentResponseType.ERROR)
    expect(result.response.error_code).to_equal(
        intent.IntentResponseErrorCode.NO_VALID_TARGETS
    )
    expect(result.response.speech["plain"]["speech"]).to_equal(
        "Sorry, no device is playing"
    )


@test
async def error_feature_not_supported(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test error message when no devices support a required feature."""
    expect(await async_setup_component(hass, media_player.DOMAIN, {})).to_be_truthy()

    hass.states.async_set(
        "media_player.test_player",
        media_player.STATE_PLAYING,
        {ATTR_FRIENDLY_NAME: "test player"},
    )

    result = await conversation.async_converse(
        hass, "set test player volume to 100%", None, Context(), None
    )

    expect(result.response.response_type).to_equal(intent.IntentResponseType.ERROR)
    expect(result.response.error_code).to_equal(
        intent.IntentResponseErrorCode.NO_VALID_TARGETS
    )
    expect(result.response.speech["plain"]["speech"]).to_equal(
        "Sorry, no device supports the required features"
    )


@test
async def error_no_timer_support(
    hass: HomeAssistant = Depends(_trigger_executor),
    area_registry: ar.AreaRegistry = Depends(area_registry_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test error message when a device does not support timers."""
    area_kitchen = area_registry.async_create("kitchen")

    entry = MockConfigEntry()
    entry.add_to_hass(hass)
    device_kitchen = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        connections=set(),
        identifiers={("demo", "device-kitchen")},
    )
    device_registry.async_update_device(device_kitchen.id, area_id=area_kitchen.id)
    device_id = device_kitchen.id

    result = await conversation.async_converse(
        hass, "set a 5 minute timer", None, Context(), None, device_id=device_id
    )

    expect(result.response.response_type).to_equal(intent.IntentResponseType.ERROR)
    expect(result.response.error_code).to_equal(
        intent.IntentResponseErrorCode.FAILED_TO_HANDLE
    )
    expect(result.response.speech["plain"]["speech"]).to_equal(
        "Sorry, timers are not supported on this device"
    )


@test
async def error_timer_not_found(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test error message when a timer cannot be matched."""
    device_id = "test_device"

    @callback
    def handle_timer(event_type: TimerEventType, timer: TimerInfo) -> None:
        pass

    async_register_timer_handler(hass, device_id, handle_timer)

    result = await conversation.async_converse(
        hass, "pause timer", None, Context(), None, device_id=device_id
    )

    expect(result.response.response_type).to_equal(intent.IntentResponseType.ERROR)
    expect(result.response.error_code).to_equal(
        intent.IntentResponseErrorCode.FAILED_TO_HANDLE
    )
    expect(result.response.speech["plain"]["speech"]).to_equal(
        "Sorry, I couldn't find that timer"
    )


@test
async def error_multiple_timers_matched(
    hass: HomeAssistant = Depends(_trigger_executor),
    area_registry: ar.AreaRegistry = Depends(area_registry_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test error message when an intent would target multiple timers."""
    area_kitchen = area_registry.async_create("kitchen")

    entry = MockConfigEntry()
    entry.add_to_hass(hass)
    device_kitchen = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        connections=set(),
        identifiers={("demo", "device-kitchen")},
    )
    device_registry.async_update_device(device_kitchen.id, area_id=area_kitchen.id)
    device_id = device_kitchen.id

    @callback
    def handle_timer(event_type: TimerEventType, timer: TimerInfo) -> None:
        pass

    async_register_timer_handler(hass, device_id, handle_timer)

    result = await conversation.async_converse(
        hass, "set a timer for 5 minutes", None, Context(), None, device_id=device_id
    )
    expect(result.response.response_type).to_equal(
        intent.IntentResponseType.ACTION_DONE
    )

    result = await conversation.async_converse(
        hass, "set a timer for 5 minutes", None, Context(), None, device_id=device_id
    )
    expect(result.response.response_type).to_equal(
        intent.IntentResponseType.ACTION_DONE
    )

    result = await conversation.async_converse(
        hass, "cancel timer", None, Context(), None, device_id=device_id
    )
    expect(result.response.response_type).to_equal(intent.IntentResponseType.ERROR)
    expect(result.response.error_code).to_equal(
        intent.IntentResponseErrorCode.FAILED_TO_HANDLE
    )
    expect(result.response.speech["plain"]["speech"]).to_equal(
        "Sorry, I am unable to target multiple timers"
    )


@test
async def no_states_matched_default_error(
    hass: HomeAssistant = Depends(_trigger_executor),
    area_registry: ar.AreaRegistry = Depends(area_registry_fixture),
) -> None:
    """Test default response when no states match and slots are missing."""
    area_kitchen = area_registry.async_get_or_create("kitchen_id")
    area_kitchen = area_registry.async_update(area_kitchen.id, name="kitchen")

    with patch(
        "homeassistant.components.conversation.default_agent.intent.async_handle",
        side_effect=intent.MatchFailedError(
            intent.MatchTargetsResult(False), intent.MatchTargetsConstraints()
        ),
    ):
        result = await conversation.async_converse(
            hass, "turn on lights in the kitchen", None, Context(), None
        )

        expect(result.response.response_type).to_equal(
            intent.IntentResponseType.ERROR
        )
        expect(result.response.error_code).to_equal(
            intent.IntentResponseErrorCode.NO_VALID_TARGETS
        )
        expect(result.response.speech["plain"]["speech"]).to_equal(
            "Sorry, I couldn't understand that"
        )


@test
async def empty_aliases(
    hass: HomeAssistant = Depends(_trigger_executor),
    area_registry: ar.AreaRegistry = Depends(area_registry_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    floor_registry: fr.FloorRegistry = Depends(floor_registry_fixture),
) -> None:
    """Test that empty aliases are not added to slot lists."""
    floor_1 = floor_registry.async_create("first floor", aliases={" "})

    area_kitchen = area_registry.async_get_or_create("kitchen_id")
    area_kitchen = area_registry.async_update(area_kitchen.id, name="kitchen")
    area_kitchen = area_registry.async_update(
        area_kitchen.id, aliases={" "}, floor_id=floor_1.floor_id
    )

    entry = MockConfigEntry()
    entry.add_to_hass(hass)
    kitchen_device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        connections=set(),
        identifiers={("demo", "id-1234")},
    )
    device_registry.async_update_device(kitchen_device.id, area_id=area_kitchen.id)

    kitchen_light = entity_registry.async_get_or_create("light", "demo", "1234")
    kitchen_light = entity_registry.async_update_entity(
        kitchen_light.entity_id,
        device_id=kitchen_device.id,
        name="kitchen light",
        aliases=[er.COMPUTED_NAME, " "],
    )
    hass.states.async_set(
        kitchen_light.entity_id,
        "on",
        attributes={ATTR_FRIENDLY_NAME: kitchen_light.name},
    )

    with patch(
        "homeassistant.components.conversation.default_agent.DefaultAgent._recognize",
        return_value=None,
    ) as mock_recognize_all:
        await conversation.async_converse(
            hass, "turn on kitchen light", None, Context(), None
        )

        expect(mock_recognize_all.call_count > 0).to_be(True)
        slot_lists = mock_recognize_all.call_args[0][2]

        expect(set(slot_lists.keys())).to_equal({"area", "name", "floor"})
        areas = slot_lists["area"]
        expect(len(areas.values)).to_equal(1)
        expect(areas.values[0].text_in.text).to_equal(area_kitchen.normalized_name)

        names = slot_lists["name"]
        expect(len(names.values)).to_equal(1)
        expect(names.values[0].text_in.text).to_equal(kitchen_light.name)

        floors = slot_lists["floor"]
        expect(len(floors.values)).to_equal(1)
        expect(floors.values[0].text_in.text).to_equal(floor_1.name)


@test
async def all_domains_loaded(hass: HomeAssistant = Depends(_trigger_executor)) -> None:
    """Test that sentences for all domains are always loaded."""
    expect("light" not in hass.config.components).to_be(True)

    result = await conversation.async_converse(
        hass, "set brightness of test light to 100%", None, Context(), None
    )

    expect(result.response.response_type).to_equal(intent.IntentResponseType.ERROR)
    expect(result.response.error_code).to_equal(
        intent.IntentResponseErrorCode.NO_VALID_TARGETS
    )
    expect(result.response.speech["plain"]["speech"]).to_equal(
        "Sorry, I am not aware of any device called test light"
    )


@test
async def same_named_entities_in_different_areas(
    hass: HomeAssistant = Depends(_trigger_executor),
    area_registry: ar.AreaRegistry = Depends(area_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test that entities with the same name in different areas can be targeted."""
    area_kitchen = area_registry.async_get_or_create("kitchen_id")
    area_kitchen = area_registry.async_update(area_kitchen.id, name="kitchen")

    area_bedroom = area_registry.async_get_or_create("bedroom_id")
    area_bedroom = area_registry.async_update(area_bedroom.id, name="bedroom")

    kitchen_light = entity_registry.async_get_or_create("light", "demo", "1234")
    kitchen_light = entity_registry.async_update_entity(
        kitchen_light.entity_id,
        area_id=area_kitchen.id,
        name="overhead light",
    )
    hass.states.async_set(
        kitchen_light.entity_id,
        "off",
        attributes={ATTR_FRIENDLY_NAME: kitchen_light.name},
    )

    bedroom_light = entity_registry.async_get_or_create("light", "demo", "5678")
    bedroom_light = entity_registry.async_update_entity(
        bedroom_light.entity_id,
        area_id=area_bedroom.id,
        name="overhead light",
    )
    hass.states.async_set(
        bedroom_light.entity_id,
        "off",
        attributes={ATTR_FRIENDLY_NAME: bedroom_light.name},
    )

    calls = async_mock_service(hass, "light", "turn_on")
    result = await conversation.async_converse(
        hass, "turn on overhead light in the kitchen", None, Context(), None
    )
    await hass.async_block_till_done()

    expect(len(calls)).to_equal(1)
    expect(result.response.response_type).to_equal(
        intent.IntentResponseType.ACTION_DONE
    )
    expect(result.response.intent is not None).to_be(True)
    expect(result.response.intent.slots.get("name", {}).get("value")).to_equal(
        kitchen_light.name
    )
    expect(result.response.intent.slots.get("name", {}).get("text")).to_equal(
        kitchen_light.name
    )
    expect(len(result.response.matched_states)).to_equal(1)
    expect(result.response.matched_states[0].entity_id).to_equal(
        kitchen_light.entity_id
    )
    expect(calls[0].data.get("entity_id")).to_equal([kitchen_light.entity_id])

    calls.clear()
    result = await conversation.async_converse(
        hass, "turn on overhead light in the bedroom", None, Context(), None
    )
    await hass.async_block_till_done()

    expect(len(calls)).to_equal(1)
    expect(result.response.response_type).to_equal(
        intent.IntentResponseType.ACTION_DONE
    )
    expect(result.response.intent is not None).to_be(True)
    expect(result.response.intent.slots.get("name", {}).get("value")).to_equal(
        bedroom_light.name
    )
    expect(result.response.intent.slots.get("name", {}).get("text")).to_equal(
        bedroom_light.name
    )
    expect(len(result.response.matched_states)).to_equal(1)
    expect(result.response.matched_states[0].entity_id).to_equal(
        bedroom_light.entity_id
    )
    expect(calls[0].data.get("entity_id")).to_equal([bedroom_light.entity_id])

    result = await conversation.async_converse(
        hass, "turn on overhead light", None, Context(), None
    )
    expect(result.response.response_type).to_equal(intent.IntentResponseType.ERROR)

    result = await conversation.async_converse(
        hass, "is the overhead light on?", None, Context(), None
    )
    expect(result.response.response_type).to_equal(intent.IntentResponseType.ERROR)

    result = await conversation.async_converse(
        hass, "how many lights are on?", None, Context(), None
    )
    expect(result.response.response_type).to_equal(
        intent.IntentResponseType.QUERY_ANSWER
    )


@test
async def same_aliased_entities_in_different_areas(
    hass: HomeAssistant = Depends(_trigger_executor),
    area_registry: ar.AreaRegistry = Depends(area_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test entities with the same alias in different areas can be targeted."""
    area_kitchen = area_registry.async_get_or_create("kitchen_id")
    area_kitchen = area_registry.async_update(area_kitchen.id, name="kitchen")

    area_bedroom = area_registry.async_get_or_create("bedroom_id")
    area_bedroom = area_registry.async_update(area_bedroom.id, name="bedroom")

    kitchen_light = entity_registry.async_get_or_create("light", "demo", "1234")
    kitchen_light = entity_registry.async_update_entity(
        kitchen_light.entity_id,
        area_id=area_kitchen.id,
        name="kitchen overhead light",
        aliases=[er.COMPUTED_NAME, "overhead light"],
    )
    hass.states.async_set(
        kitchen_light.entity_id,
        "off",
        attributes={ATTR_FRIENDLY_NAME: kitchen_light.name},
    )

    bedroom_light = entity_registry.async_get_or_create("light", "demo", "5678")
    bedroom_light = entity_registry.async_update_entity(
        bedroom_light.entity_id,
        area_id=area_bedroom.id,
        name="bedroom overhead light",
        aliases=[er.COMPUTED_NAME, "overhead light"],
    )
    hass.states.async_set(
        bedroom_light.entity_id,
        "off",
        attributes={ATTR_FRIENDLY_NAME: bedroom_light.name},
    )

    calls = async_mock_service(hass, "light", "turn_on")
    result = await conversation.async_converse(
        hass, "turn on overhead light in the kitchen", None, Context(), None
    )
    await hass.async_block_till_done()

    expect(len(calls)).to_equal(1)
    expect(result.response.response_type).to_equal(
        intent.IntentResponseType.ACTION_DONE
    )
    expect(result.response.intent is not None).to_be(True)
    expect(result.response.intent.slots.get("name", {}).get("value")).to_equal(
        "overhead light"
    )
    expect(result.response.intent.slots.get("name", {}).get("text")).to_equal(
        "overhead light"
    )
    expect(len(result.response.matched_states)).to_equal(1)
    expect(result.response.matched_states[0].entity_id).to_equal(
        kitchen_light.entity_id
    )
    expect(calls[0].data.get("entity_id")).to_equal([kitchen_light.entity_id])

    calls.clear()
    result = await conversation.async_converse(
        hass, "turn on overhead light in the bedroom", None, Context(), None
    )
    await hass.async_block_till_done()

    expect(len(calls)).to_equal(1)
    expect(result.response.response_type).to_equal(
        intent.IntentResponseType.ACTION_DONE
    )
    expect(result.response.intent is not None).to_be(True)
    expect(result.response.intent.slots.get("name", {}).get("value")).to_equal(
        "overhead light"
    )
    expect(result.response.intent.slots.get("name", {}).get("text")).to_equal(
        "overhead light"
    )
    expect(len(result.response.matched_states)).to_equal(1)
    expect(result.response.matched_states[0].entity_id).to_equal(
        bedroom_light.entity_id
    )
    expect(calls[0].data.get("entity_id")).to_equal([bedroom_light.entity_id])

    result = await conversation.async_converse(
        hass, "turn on overhead light", None, Context(), None
    )
    expect(result.response.response_type).to_equal(intent.IntentResponseType.ERROR)

    result = await conversation.async_converse(
        hass, "is the overhead light on?", None, Context(), None
    )
    expect(result.response.response_type).to_equal(intent.IntentResponseType.ERROR)

    result = await conversation.async_converse(
        hass, "how many lights are on?", None, Context(), None
    )
    expect(result.response.response_type).to_equal(
        intent.IntentResponseType.QUERY_ANSWER
    )


@test
async def device_id_in_handler(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that the default agent passes device_id to intent handler."""
    device_id = "test_device"

    class _OrderBeerIntentHandler(intent.IntentHandler):
        intent_type = "OrderBeer"

        def __init__(self) -> None:
            super().__init__()
            self.device_id: str | None = None

        async def async_handle(
            self, intent_obj: intent.Intent
        ) -> intent.IntentResponse:
            self.device_id = intent_obj.device_id
            return intent_obj.create_response()

    handler = _OrderBeerIntentHandler()
    intent.async_register(hass, handler)

    result = await conversation.async_converse(
        hass,
        "I'd like to order a stout please",
        None,
        Context(),
        device_id=device_id,
    )
    expect(result.response.response_type).to_equal(
        intent.IntentResponseType.ACTION_DONE
    )
    expect(handler.device_id).to_equal(device_id)


@test
async def name_wildcard_lower_priority(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that the default agent does not prioritize a wildcard {name} slot."""

    class _OrderBeerIntentHandler(intent.IntentHandler):
        intent_type = "OrderBeer"

        def __init__(self) -> None:
            super().__init__()
            self.triggered = False

        async def async_handle(
            self, intent_obj: intent.Intent
        ) -> intent.IntentResponse:
            self.triggered = True
            return intent_obj.create_response()

    class _OrderFoodIntentHandler(intent.IntentHandler):
        intent_type = "OrderFood"

        def __init__(self) -> None:
            super().__init__()
            self.triggered = False

        async def async_handle(
            self, intent_obj: intent.Intent
        ) -> intent.IntentResponse:
            self.triggered = True
            return intent_obj.create_response()

    beer_handler = _OrderBeerIntentHandler()
    food_handler = _OrderFoodIntentHandler()
    intent.async_register(hass, beer_handler)
    intent.async_register(hass, food_handler)

    result = await conversation.async_converse(
        hass, "I'd like to order a stout please", None, Context(), None
    )
    expect(result.response.response_type).to_equal(
        intent.IntentResponseType.ACTION_DONE
    )
    expect(beer_handler.triggered).to_be(True)
    expect(food_handler.triggered).to_be(False)

    beer_handler.triggered = False
    result = await conversation.async_converse(
        hass, "I'd like to order a cookie please", None, Context(), None
    )
    expect(result.response.response_type).to_equal(
        intent.IntentResponseType.ACTION_DONE
    )
    expect(beer_handler.triggered).to_be(False)
    expect(food_handler.triggered).to_be(True)


@test
async def intent_entity_added_removed(
    hass: HomeAssistant = Depends(_trigger_executor),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    snapshot: SnapshotAssertion = Depends(snapshot_fixture),
) -> None:
    """Test processing intent via HTTP API with entities added later."""
    context = Context()
    entity_registry.async_get_or_create(
        "light", "demo", "1234", suggested_object_id="kitchen"
    )
    entity_registry.async_update_entity(
        "light.kitchen", aliases=[er.COMPUTED_NAME, "my cool light"]
    )
    await hass.async_block_till_done()
    hass.states.async_set("light.kitchen", "off")

    calls = async_mock_service(hass, LIGHT_DOMAIN, "turn_on")
    result = await conversation.async_converse(
        hass, "turn on my cool light", None, context
    )

    expect(len(calls)).to_equal(1)
    data = result.as_dict()

    expect(data).to_equal(snapshot)
    expect(data["response"]["response_type"]).to_equal("action_done")

    entity_registry.async_get_or_create(
        "light",
        "demo",
        "5678",
        suggested_object_id="late",
        original_name="friendly light",
    )
    hass.states.async_set("light.late", "off", {"friendly_name": "friendly light"})

    result = await conversation.async_converse(
        hass, "turn on friendly light", None, context
    )
    data = result.as_dict()

    expect(data).to_equal(snapshot)
    expect(data["response"]["response_type"]).to_equal("action_done")

    entity_registry.async_update_entity(
        "light.late", aliases=[er.COMPUTED_NAME, "late added light"]
    )

    result = await conversation.async_converse(
        hass, "turn on late added light", None, context
    )

    data = result.as_dict()

    expect(data).to_equal(snapshot)
    expect(data["response"]["response_type"]).to_equal("action_done")

    hass.states.async_remove("light.late")

    result = await conversation.async_converse(
        hass, "turn on late added light", None, context
    )
    data = result.as_dict()
    expect(data).to_equal(snapshot)
    expect(data["response"]["response_type"]).to_equal("error")


@test
async def intent_alias_added_removed(
    hass: HomeAssistant = Depends(_trigger_executor),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    snapshot: SnapshotAssertion = Depends(snapshot_fixture),
) -> None:
    """Test processing intent via HTTP API with aliases added later."""
    context = Context()
    entity_registry.async_get_or_create(
        "light",
        "demo",
        "1234",
        suggested_object_id="kitchen",
        original_name="kitchen light",
    )
    hass.states.async_set("light.kitchen", "off", {"friendly_name": "kitchen light"})

    calls = async_mock_service(hass, LIGHT_DOMAIN, "turn_on")
    result = await conversation.async_converse(
        hass, "turn on kitchen light", None, context
    )
    expect(len(calls)).to_equal(1)
    data = result.as_dict()

    expect(data).to_equal(snapshot)
    expect(data["response"]["response_type"]).to_equal("action_done")

    entity_registry.async_update_entity(
        "light.kitchen", aliases=[er.COMPUTED_NAME, "late added alias"]
    )

    result = await conversation.async_converse(
        hass, "turn on late added alias", None, context
    )

    data = result.as_dict()

    expect(data).to_equal(snapshot)
    expect(data["response"]["response_type"]).to_equal("action_done")

    entity_registry.async_update_entity("light.kitchen", aliases=[er.COMPUTED_NAME])

    result = await conversation.async_converse(
        hass, "turn on late added alias", None, context
    )

    data = result.as_dict()
    expect(data).to_equal(snapshot)
    expect(data["response"]["response_type"]).to_equal("error")


@test
async def intent_entity_renamed(
    hass: HomeAssistant = Depends(_trigger_executor),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    snapshot: SnapshotAssertion = Depends(snapshot_fixture),
) -> None:
    """Test processing intent via HTTP API with entities renamed later."""
    context = Context()
    entity = MockLight("kitchen light", STATE_ON)
    entity._attr_unique_id = "1234"
    entity.entity_id = "light.kitchen"
    setup_test_component_platform(hass, LIGHT_DOMAIN, [entity])

    expect(
        await async_setup_component(
            hass,
            LIGHT_DOMAIN,
            {LIGHT_DOMAIN: [{"platform": "test"}]},
        )
    ).to_be_truthy()
    await hass.async_block_till_done()

    calls = async_mock_service(hass, LIGHT_DOMAIN, "turn_on")
    result = await conversation.async_converse(
        hass, "turn on kitchen light", None, context
    )

    expect(len(calls)).to_equal(1)
    data = result.as_dict()

    expect(data).to_equal(snapshot)
    expect(data["response"]["response_type"]).to_equal("action_done")

    entity_registry.async_update_entity("light.kitchen", name="renamed light")
    await hass.async_block_till_done()

    result = await conversation.async_converse(
        hass, "turn on renamed light", None, context
    )

    data = result.as_dict()

    expect(data).to_equal(snapshot)
    expect(data["response"]["response_type"]).to_equal("action_done")


@test
async def intent_entity_remove_custom_name(
    hass: HomeAssistant = Depends(_trigger_executor),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    snapshot: SnapshotAssertion = Depends(snapshot_fixture),
) -> None:
    """Test removing a custom name allows targeting by auto-generated name again."""
    context = Context()
    entity = MockLight("kitchen light", STATE_ON)
    entity._attr_unique_id = "1234"
    entity.entity_id = "light.kitchen"
    setup_test_component_platform(hass, LIGHT_DOMAIN, [entity])

    expect(
        await async_setup_component(
            hass,
            LIGHT_DOMAIN,
            {LIGHT_DOMAIN: [{"platform": "test"}]},
        )
    ).to_be_truthy()
    await hass.async_block_till_done()

    calls = async_mock_service(hass, LIGHT_DOMAIN, "turn_on")

    entity_registry.async_update_entity("light.kitchen", name="renamed light")
    result = await conversation.async_converse(
        hass, "turn on kitchen light", None, context
    )

    data = result.as_dict()
    expect(data).to_equal(snapshot)
    expect(data["response"]["response_type"]).to_equal("error")

    entity_registry.async_update_entity("light.kitchen", name=None)
    await hass.async_block_till_done()

    result = await conversation.async_converse(
        hass, "turn on kitchen light", None, context
    )

    data = result.as_dict()

    expect(data).to_equal(snapshot)
    expect(data["response"]["response_type"]).to_equal("action_done")
    expect(len(calls)).to_equal(1)

    result = await conversation.async_converse(
        hass, "turn on renamed light", None, context
    )

    data = result.as_dict()
    expect(data).to_equal(snapshot)
    expect(data["response"]["response_type"]).to_equal("error")


@test
async def intent_entity_fail_if_unexposed(
    hass: HomeAssistant = Depends(_trigger_executor),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    snapshot: SnapshotAssertion = Depends(snapshot_fixture),
) -> None:
    """Test that an entity is not usable if unexposed."""
    context = Context()
    entity = MockLight("kitchen light", STATE_ON)
    entity._attr_unique_id = "1234"
    entity.entity_id = "light.kitchen"
    setup_test_component_platform(hass, LIGHT_DOMAIN, [entity])

    expect(
        await async_setup_component(
            hass,
            LIGHT_DOMAIN,
            {LIGHT_DOMAIN: [{"platform": "test"}]},
        )
    ).to_be_truthy()
    await hass.async_block_till_done()

    calls = async_mock_service(hass, LIGHT_DOMAIN, "turn_on")

    expose_entity(hass, "light.kitchen", False)
    await hass.async_block_till_done(wait_background_tasks=True)

    result = await conversation.async_converse(
        hass, "turn on kitchen light", None, context
    )

    data = result.as_dict()
    expect(data).to_equal(snapshot)
    expect(data["response"]["response_type"]).to_equal("error")
    expect(len(calls)).to_equal(0)


@test
async def intent_entity_exposed(
    hass: HomeAssistant = Depends(_trigger_executor),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    snapshot: SnapshotAssertion = Depends(snapshot_fixture),
) -> None:
    """Test processing intent via HTTP API with manual expose."""
    context = Context()
    entity = MockLight("kitchen light", STATE_ON)
    entity._attr_unique_id = "1234"
    entity.entity_id = "light.kitchen"
    setup_test_component_platform(hass, LIGHT_DOMAIN, [entity])

    expect(
        await async_setup_component(
            hass,
            LIGHT_DOMAIN,
            {LIGHT_DOMAIN: [{"platform": "test"}]},
        )
    ).to_be_truthy()
    await hass.async_block_till_done()

    calls = async_mock_service(hass, LIGHT_DOMAIN, "turn_on")

    expose_entity(hass, "light.kitchen", False)
    await hass.async_block_till_done()
    expose_entity(hass, "light.kitchen", True)
    await hass.async_block_till_done()

    result = await conversation.async_converse(
        hass, "turn on kitchen light", None, context
    )

    data = result.as_dict()
    expect(data).to_equal(snapshot)
    expect(data["response"]["response_type"]).to_equal("action_done")
    expect(len(calls)).to_equal(1)


@test
async def intent_conversion_not_expose_new(
    hass: HomeAssistant = Depends(_trigger_executor),
    hass_admin_user: MockUser = Depends(hass_admin_user_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    snapshot: SnapshotAssertion = Depends(snapshot_fixture),
) -> None:
    """Test processing intent via HTTP API when not exposing new entities."""
    expose_new(hass, False)

    context = Context()
    entity = MockLight("kitchen light", STATE_ON)
    entity._attr_unique_id = "1234"
    entity.entity_id = "light.kitchen"
    setup_test_component_platform(hass, LIGHT_DOMAIN, [entity])

    expect(
        await async_setup_component(
            hass,
            LIGHT_DOMAIN,
            {LIGHT_DOMAIN: [{"platform": "test"}]},
        )
    ).to_be_truthy()
    await hass.async_block_till_done()

    calls = async_mock_service(hass, LIGHT_DOMAIN, "turn_on")

    result = await conversation.async_converse(
        hass, "turn on kitchen light", None, context
    )

    data = result.as_dict()
    expect(data).to_equal(snapshot)
    expect(data["response"]["response_type"]).to_equal("error")

    expose_entity(hass, "light.kitchen", True)
    await hass.async_block_till_done()

    result = await conversation.async_converse(
        hass, "turn on kitchen light", None, context
    )

    expect(len(calls)).to_equal(1)
    data = result.as_dict()

    expect(data).to_equal(snapshot)
    expect(data["response"]["response_type"]).to_equal("action_done")


@test
async def custom_sentences(
    hass: HomeAssistant = Depends(_trigger_executor),
    snapshot: SnapshotAssertion = Depends(snapshot_fixture),
) -> None:
    """Test custom sentences with a custom intent."""
    intent.async_register(hass, OrderBeerIntentHandler())

    language = "en-us"

    for beer_style in ("stout", "lager"):
        result = await conversation.async_converse(
            hass,
            f"I'd like to order a {beer_style}, please",
            None,
            Context(),
            language=language,
        )

        data = result.as_dict()
        expect(data).to_equal(snapshot)
        expect(data["response"]["response_type"]).to_equal("action_done")
        expect(data["response"]["speech"]["plain"]["speech"]).to_equal(
            f"You ordered a {beer_style}"
        )


@test
async def custom_sentences_config(
    hass: HomeAssistant = Depends(hass_fixture),
    _network: None = Depends(mock_network_fixture),
    snapshot: SnapshotAssertion = Depends(snapshot_fixture),
) -> None:
    """Test custom sentences with a custom intent in config."""
    expect(await async_setup_component(hass, "homeassistant", {})).to_be_truthy()
    expect(
        await async_setup_component(
            hass,
            "conversation",
            {"conversation": {"intents": {"StealthMode": ["engage stealth mode"]}}},
        )
    ).to_be_truthy()
    expect(await async_setup_component(hass, "intent", {})).to_be_truthy()
    expect(
        await async_setup_component(
            hass,
            "intent_script",
            {
                "intent_script": {
                    "StealthMode": {"speech": {"text": "Stealth mode engaged"}}
                }
            },
        )
    ).to_be_truthy()

    result = await conversation.async_converse(
        hass, "engage stealth mode", None, Context(), None
    )

    data = result.as_dict()
    expect(data).to_equal(snapshot)
    expect(data["response"]["response_type"]).to_equal("action_done")
    expect(data["response"]["speech"]["plain"]["speech"]).to_equal(
        "Stealth mode engaged"
    )


@test
async def language_region(hass: HomeAssistant = Depends(_trigger_executor)) -> None:
    """Test regional languages."""
    hass.states.async_set("light.kitchen", "off")
    calls = async_mock_service(hass, LIGHT_DOMAIN, "turn_on")

    language = f"{hass.config.language}-YZ"
    await hass.services.async_call(
        "conversation",
        "process",
        {
            conversation.ATTR_TEXT: "turn on the kitchen",
            conversation.ATTR_LANGUAGE: language,
        },
    )
    await hass.async_block_till_done()

    expect(len(calls)).to_equal(1)
    call = calls[0]
    expect(call.domain).to_equal(LIGHT_DOMAIN)
    expect(call.service).to_equal("turn_on")
    expect(call.data).to_equal({"entity_id": ["light.kitchen"]})


@test
async def non_default_response(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test intent response that is not the default."""
    hass.states.async_set("cover.front_door", "closed")
    calls = async_mock_service(hass, "cover", SERVICE_OPEN_COVER)

    agent = async_get_agent(hass)

    result = await agent.async_process(
        ConversationInput(
            text="open the front door",
            context=Context(),
            conversation_id=None,
            device_id=None,
            satellite_id=None,
            language=hass.config.language,
            agent_id=None,
        )
    )
    expect(len(calls)).to_equal(1)
    expect(result.response.speech["plain"]["speech"]).to_equal("Opening")


@test
async def turn_on_area(
    hass: HomeAssistant = Depends(_trigger_executor),
    area_registry: ar.AreaRegistry = Depends(area_registry_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test turning on an area."""
    entry = MockConfigEntry(domain="test")
    entry.add_to_hass(hass)

    device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )

    kitchen_area = area_registry.async_create("kitchen")
    device_registry.async_update_device(device.id, area_id=kitchen_area.id)

    entity_registry.async_get_or_create(
        "light", "demo", "1234", suggested_object_id="stove"
    )
    entity_registry.async_update_entity(
        "light.stove",
        aliases=[er.COMPUTED_NAME, "my stove light"],
        area_id=kitchen_area.id,
    )
    hass.states.async_set("light.stove", "off")

    calls = async_mock_service(hass, LIGHT_DOMAIN, "turn_on")

    await hass.services.async_call(
        "conversation",
        "process",
        {conversation.ATTR_TEXT: "turn on lights in the kitchen"},
    )
    await hass.async_block_till_done()

    expect(len(calls)).to_equal(1)
    call = calls[0]
    expect(call.domain).to_equal(LIGHT_DOMAIN)
    expect(call.service).to_equal("turn_on")
    expect(call.data).to_equal({"entity_id": ["light.stove"]})

    basement_area = area_registry.async_create("basement")
    device_registry.async_update_device(device.id, area_id=basement_area.id)
    entity_registry.async_update_entity("light.stove", area_id=basement_area.id)
    calls.clear()

    await hass.services.async_call(
        "conversation",
        "process",
        {conversation.ATTR_TEXT: "turn on lights in the kitchen"},
    )
    await hass.async_block_till_done()

    expect(len(calls)).to_equal(0)

    await hass.services.async_call(
        "conversation",
        "process",
        {conversation.ATTR_TEXT: "turn on lights in the basement"},
    )
    await hass.async_block_till_done()

    expect(len(calls)).to_equal(1)
    call = calls[0]
    expect(call.domain).to_equal(LIGHT_DOMAIN)
    expect(call.service).to_equal("turn_on")
    expect(call.data).to_equal({"entity_id": ["light.stove"]})


@test
async def light_area_same_name(
    hass: HomeAssistant = Depends(_trigger_executor),
    area_registry: ar.AreaRegistry = Depends(area_registry_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test turning on a light with the same name as an area."""
    entry = MockConfigEntry(domain="test")
    entry.add_to_hass(hass)

    device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )

    kitchen_area = area_registry.async_create("kitchen")
    device_registry.async_update_device(device.id, area_id=kitchen_area.id)

    kitchen_light = entity_registry.async_get_or_create(
        "light", "demo", "1234", original_name="light in the kitchen"
    )
    entity_registry.async_update_entity(
        kitchen_light.entity_id, area_id=kitchen_area.id
    )
    hass.states.async_set(
        kitchen_light.entity_id,
        "off",
        attributes={ATTR_FRIENDLY_NAME: "light in the kitchen"},
    )

    ceiling_light = entity_registry.async_get_or_create(
        "light", "demo", "5678", original_name="ceiling light"
    )
    entity_registry.async_update_entity(
        ceiling_light.entity_id, area_id=kitchen_area.id
    )
    hass.states.async_set(
        ceiling_light.entity_id, "off", attributes={ATTR_FRIENDLY_NAME: "ceiling light"}
    )

    bathroom_light = entity_registry.async_get_or_create(
        "light", "demo", "9012", original_name="light"
    )
    hass.states.async_set(
        bathroom_light.entity_id, "off", attributes={ATTR_FRIENDLY_NAME: "light"}
    )

    calls = async_mock_service(hass, LIGHT_DOMAIN, "turn_on")

    await hass.services.async_call(
        "conversation",
        "process",
        {conversation.ATTR_TEXT: "turn on light in the kitchen"},
    )
    await hass.async_block_till_done()

    expect(len(calls)).to_equal(1)
    call = calls[0]
    expect(call.domain).to_equal(LIGHT_DOMAIN)
    expect(call.service).to_equal("turn_on")
    expect(call.data).to_equal({"entity_id": [kitchen_light.entity_id]})


@test
async def custom_sentences_priority(
    hass: HomeAssistant = Depends(hass_fixture),
    _network: None = Depends(mock_network_fixture),
    hass_admin_user: MockUser = Depends(hass_admin_user_fixture),
    snapshot: SnapshotAssertion = Depends(snapshot_fixture),
) -> None:
    """Test that user intents from custom_sentences have priority over builtins."""
    with tempfile.NamedTemporaryFile(
        mode="w+",
        encoding="utf-8",
        suffix=".yaml",
        dir=os.path.join(hass.config.config_dir, "custom_sentences", "en"),
    ) as custom_sentences_file:
        yaml.dump(
            {
                "language": "en",
                "intents": {
                    "CustomIntent": {"data": [{"sentences": ["turn on the lamp"]}]}
                },
            },
            custom_sentences_file,
        )
        custom_sentences_file.flush()
        custom_sentences_file.seek(0)

        expect(await async_setup_component(hass, "homeassistant", {})).to_be_truthy()
        expect(await async_setup_component(hass, "conversation", {})).to_be_truthy()
        expect(await async_setup_component(hass, "light", {})).to_be_truthy()
        expect(await async_setup_component(hass, "intent", {})).to_be_truthy()
        expect(
            await async_setup_component(
                hass,
                "intent_script",
                {
                    "intent_script": {
                        "CustomIntent": {"speech": {"text": "custom response"}}
                    }
                },
            )
        ).to_be_truthy()

        hass.states.async_set("light.lamp", "off")

        result = await conversation.async_converse(
            hass,
            "turn on the lamp",
            None,
            Context(),
            language=hass.config.language,
        )

        data = result.as_dict()
        expect(data["response"]["response_type"]).to_equal("action_done")
        expect(data["response"]["speech"]["plain"]["speech"]).to_equal(
            "custom response"
        )


@test
async def config_sentences_priority(
    hass: HomeAssistant = Depends(hass_fixture),
    _network: None = Depends(mock_network_fixture),
    hass_admin_user: MockUser = Depends(hass_admin_user_fixture),
    snapshot: SnapshotAssertion = Depends(snapshot_fixture),
) -> None:
    """Test that user intents from configuration.yaml have priority over builtins."""
    expect(await async_setup_component(hass, "homeassistant", {})).to_be_truthy()
    expect(await async_setup_component(hass, "intent", {})).to_be_truthy()
    expect(
        await async_setup_component(
            hass,
            "conversation",
            {
                "conversation": {
                    "intents": {
                        "CustomIntent": ["turn on <name>"],
                        "WorseCustomIntent": ["turn on the lamp"],
                        "FakeCustomIntent": ["turn on <name>"],
                    }
                }
            },
        )
    ).to_be_truthy()

    intents = (
        await conversation.async_get_agent(hass).async_get_or_load_intents(
            hass.config.language
        )
    ).intents.intents
    intents["FakeCustomIntent"].data[0].metadata[METADATA_CUSTOM_SENTENCE] = False

    expect(await async_setup_component(hass, "light", {})).to_be_truthy()
    expect(
        await async_setup_component(
            hass,
            "intent_script",
            {
                "intent_script": {
                    "CustomIntent": {"speech": {"text": "custom response"}},
                    "WorseCustomIntent": {"speech": {"text": "worse custom response"}},
                    "FakeCustomIntent": {"speech": {"text": "fake custom response"}},
                }
            },
        )
    ).to_be_truthy()

    hass.states.async_set("light.lamp", "off")

    result = await conversation.async_converse(
        hass,
        "turn on the lamp",
        None,
        Context(),
        language=hass.config.language,
    )
    data = result.as_dict()
    expect(data["response"]["response_type"]).to_equal("action_done")
    expect(data["response"]["speech"]["plain"]["speech"]).to_equal("custom response")


@test
async def query_same_name_different_areas(
    hass: HomeAssistant = Depends(_trigger_executor),
    area_registry: ar.AreaRegistry = Depends(area_registry_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test asking a question about same-named entities in different areas."""
    entry = MockConfigEntry(domain="test")
    entry.add_to_hass(hass)

    kitchen_device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )

    kitchen_area = area_registry.async_create("kitchen")
    device_registry.async_update_device(kitchen_device.id, area_id=kitchen_area.id)

    kitchen_light = entity_registry.async_get_or_create(
        "light",
        "demo",
        "1234",
        original_name="overhead light",
    )
    entity_registry.async_update_entity(
        kitchen_light.entity_id, area_id=kitchen_area.id
    )
    hass.states.async_set(
        kitchen_light.entity_id,
        "on",
        attributes={ATTR_FRIENDLY_NAME: "overhead light"},
    )

    bedroom_area = area_registry.async_create("bedroom")
    bedroom_light = entity_registry.async_get_or_create(
        "light",
        "demo",
        "5678",
        original_name="overhead light",
    )
    entity_registry.async_update_entity(
        bedroom_light.entity_id, area_id=bedroom_area.id
    )
    hass.states.async_set(
        bedroom_light.entity_id,
        "off",
        attributes={ATTR_FRIENDLY_NAME: "overhead light"},
    )

    result = await conversation.async_converse(
        hass, "is the overhead light on?", None, Context(), None
    )
    expect(result.response.response_type).to_equal(intent.IntentResponseType.ERROR)

    result = await conversation.async_converse(
        hass,
        "is the overhead light on?",
        None,
        Context(),
        None,
        device_id=kitchen_device.id,
    )
    expect(result.response.response_type).to_equal(
        intent.IntentResponseType.QUERY_ANSWER
    )
    expect(len(result.response.matched_states)).to_equal(1)
    expect(result.response.matched_states[0].entity_id).to_equal(
        kitchen_light.entity_id
    )


@test
async def intent_cache_exposed(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that intent recognition results are cached for exposed entities."""
    agent = async_get_agent(hass)

    entity_id = "light.test_light"
    hass.states.async_set(entity_id, "off")
    expose_entity(hass, entity_id, True)
    await hass.async_block_till_done()

    user_input = ConversationInput(
        text="turn on test light",
        context=Context(),
        conversation_id=None,
        device_id=None,
        satellite_id=None,
        language=hass.config.language,
        agent_id=None,
    )
    result = await agent.async_recognize_intent(user_input)
    expect(result is not None).to_be(True)
    expect(result.entities["name"].text).to_equal("test light")

    mark = "_from_cache"
    setattr(result, mark, True)

    result = await agent.async_recognize_intent(user_input)
    expect(result is not None).to_be(True)
    expect(getattr(result, mark, None)).to_be(True)

    expose_entity(hass, entity_id, False)
    result = await agent.async_recognize_intent(user_input)
    expect(result is not None).to_be(True)
    expect(getattr(result, mark, None)).to_be(None)


@test
async def intent_cache_all_entities(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that intent recognition results are cached for all entities."""
    agent = async_get_agent(hass)

    entity_id = "light.test_light"
    hass.states.async_set(entity_id, "off")
    expose_entity(hass, entity_id, False)
    await hass.async_block_till_done()

    user_input = ConversationInput(
        text="turn on test light",
        context=Context(),
        conversation_id=None,
        device_id=None,
        satellite_id=None,
        language=hass.config.language,
        agent_id=None,
    )
    result = await agent.async_recognize_intent(user_input)
    expect(result is not None).to_be(True)
    expect(result.entities["name"].text).to_equal("test light")

    mark = "_from_cache"
    setattr(result, mark, True)

    result = await agent.async_recognize_intent(user_input)
    expect(result is not None).to_be(True)
    expect(getattr(result, mark, None)).to_be(True)

    hass.states.async_set("light.new_light", "off")
    result = await agent.async_recognize_intent(user_input)
    expect(result is not None).to_be(True)
    expect(getattr(result, mark, None)).to_be(None)


@test
async def intent_cache_fuzzy(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that intent recognition results are cached for fuzzy matches."""
    agent = async_get_agent(hass)

    user_input = ConversationInput(
        text="turn on test light",
        context=Context(),
        conversation_id=None,
        device_id=None,
        satellite_id=None,
        language=hass.config.language,
        agent_id=None,
    )
    result = await agent.async_recognize_intent(user_input)
    expect(result is not None).to_be(True)
    expect(result.unmatched_entities["area"].text).to_equal("test ")

    mark = "_from_cache"
    setattr(result, mark, True)

    result = await agent.async_recognize_intent(user_input)
    expect(result is not None).to_be(True)
    expect(getattr(result, mark, None)).to_be(True)


@test
async def entities_filtered_by_input(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that entities are filtered by the input text before intent matching."""
    agent = async_get_agent(hass)

    hass.states.async_set("light.test_light", "off")
    hass.states.async_set(
        "light.test_light_2", "off", attributes={ATTR_FRIENDLY_NAME: "test light"}
    )
    hass.states.async_set("cover.garage_door", "closed")
    hass.states.async_set("switch.test_switch", "off")
    expose_entity(hass, "light.test_light", False)
    expose_entity(hass, "light.test_light_2", False)
    expose_entity(hass, "cover.garage_door", False)
    expose_entity(hass, "switch.test_switch", True)
    await hass.async_block_till_done()

    user_input = ConversationInput(
        text="turn on test switch",
        context=Context(),
        conversation_id=None,
        device_id=None,
        satellite_id=None,
        language=hass.config.language,
        agent_id=None,
    )

    with patch(
        "homeassistant.components.conversation.default_agent.recognize_best",
        return_value=None,
    ) as recognize_best:
        await agent.async_recognize_intent(user_input)

        expect(len(recognize_best.call_args_list)).to_equal(2)

        slot_lists = recognize_best.call_args_list[0].kwargs["slot_lists"]
        name_list = slot_lists["name"]
        expect(len(name_list.values)).to_equal(1)
        expect(name_list.values[0].text_in.text).to_equal("test switch")

    user_input = ConversationInput(
        text="turn on Test Light",
        context=Context(),
        conversation_id=None,
        device_id=None,
        satellite_id=None,
        language=hass.config.language,
        agent_id=None,
    )

    with patch(
        "homeassistant.components.conversation.default_agent.recognize_best",
        return_value=None,
    ) as recognize_best:
        await agent.async_recognize_intent(user_input)

        expect(len(recognize_best.call_args_list)).to_equal(2)

        slot_lists = recognize_best.call_args_list[1].kwargs["slot_lists"]
        name_list = slot_lists["name"]
        expect(len(name_list.values)).to_equal(2)
        expect(name_list.values[0].text_in.text).to_equal("test light")
        expect(name_list.values[1].text_in.text).to_equal("test light")


@test
async def entities_names_are_not_templates(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that entities names are not treated as hassil templates."""
    hass.states.async_set(
        "light.test_light", "off", attributes={ATTR_FRIENDLY_NAME: "<test [light"}
    )

    async_mock_service(hass, LIGHT_DOMAIN, "turn_on")

    result = await conversation.async_converse(
        hass,
        "turn on <test [light",
        None,
        Context(),
        language=hass.config.language,
    )

    expect(result is not None).to_be(True)
    expect(result.response.response_type).to_equal(
        intent.IntentResponseType.ACTION_DONE
    )

    expose_entity(hass, "light.test_light", False)
    result = await conversation.async_converse(
        hass,
        "turn on <test [light",
        None,
        Context(),
        language=hass.config.language,
    )

    expect(result is not None).to_be(True)
    expect(result.response.response_type).to_equal(intent.IntentResponseType.ERROR)


@test.cases(
    test.case(
        "en",
        language="en",
        light_name="test light",
        on_sentence="turn on test light",
        off_sentence="turn off test light",
    ),
    test.case(
        "de",
        language="de",
        light_name="Testlicht",
        on_sentence="Schalte Testlicht ein",
        off_sentence="Schalte Testlicht aus",
    ),
    test.case(
        "fr",
        language="fr",
        light_name="lumière de test",
        on_sentence="Allumer la lumière de test",
        off_sentence="Éteindre la lumière de test",
    ),
    test.case(
        "nl",
        language="nl",
        light_name="testlicht",
        on_sentence="Zet testlicht aan",
        off_sentence="Zet testlicht uit",
    ),
    test.case(
        "zh-cn",
        language="zh-cn",
        light_name="卧室灯",
        on_sentence="打开卧室灯",
        off_sentence="关闭卧室灯",
    ),
    test.case(
        "zh-hk",
        language="zh-hk",
        light_name="睡房燈",
        on_sentence="打開睡房燈",
        off_sentence="關閉睡房燈",
    ),
    test.case(
        "zh-tw",
        language="zh-tw",
        light_name="臥室檯燈",
        on_sentence="打開臥室檯燈",
        off_sentence="關臥室檯燈",
    ),
)
async def turn_on_off(
    language: str,
    light_name: str,
    on_sentence: str,
    off_sentence: str,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test turn on/off in multiple languages."""
    entity_id = "light.light1234"
    hass.states.async_set(
        entity_id, STATE_OFF, attributes={ATTR_FRIENDLY_NAME: light_name}
    )

    on_calls = async_mock_service(hass, LIGHT_DOMAIN, "turn_on")
    await conversation.async_converse(
        hass,
        on_sentence,
        None,
        Context(),
        language=language,
    )
    expect(len(on_calls)).to_equal(1)
    expect(on_calls[0].data.get("entity_id")).to_equal([entity_id])

    off_calls = async_mock_service(hass, LIGHT_DOMAIN, "turn_off")
    await conversation.async_converse(
        hass,
        off_sentence,
        None,
        Context(),
        language=language,
    )
    expect(len(off_calls)).to_equal(1)
    expect(off_calls[0].data.get("entity_id")).to_equal([entity_id])


@test.cases(
    test.case(
        "no_intent_match",
        error_code=intent.IntentResponseErrorCode.NO_INTENT_MATCH,
        return_response=False,
    ),
    test.case(
        "no_valid_targets",
        error_code=intent.IntentResponseErrorCode.NO_VALID_TARGETS,
        return_response=False,
    ),
    test.case(
        "failed_to_handle",
        error_code=intent.IntentResponseErrorCode.FAILED_TO_HANDLE,
        return_response=True,
    ),
    test.case(
        "unknown",
        error_code=intent.IntentResponseErrorCode.UNKNOWN,
        return_response=True,
    ),
)
async def handle_intents_with_response_errors(
    error_code: intent.IntentResponseErrorCode,
    return_response: bool,
    hass: HomeAssistant = Depends(_trigger_executor),
    area_registry: ar.AreaRegistry = Depends(area_registry_fixture),
) -> None:
    """Test that handle_intents does not return response errors."""
    expect(await async_setup_component(hass, "climate", {})).to_be_truthy()
    area_registry.async_create("living room")

    agent = async_get_agent(hass)

    user_input = ConversationInput(
        text="What is the temperature in the living room?",
        context=Context(),
        conversation_id=None,
        device_id=None,
        satellite_id=None,
        language=hass.config.language,
        agent_id=None,
    )

    with (
        patch(
            "homeassistant.components.conversation.default_agent.DefaultAgent._async_process_intent_result",
            return_value=default_agent._make_error_result(
                user_input.language, error_code, "Mock error message"
            ),
        ) as mock_process,
        chat_session.async_get_chat_session(hass) as session,
        async_get_chat_log(hass, session, user_input) as chat_log,
    ):
        response = await agent.async_handle_intents(user_input, chat_log)

    expect(len(mock_process.mock_calls)).to_equal(1)

    if return_response:
        expect(response is not None and response.error_code == error_code).to_be(True)
    else:
        expect(response).to_be(None)


@test.cases(
    test.case(
        "match_failed",
        side_effect=intent.MatchFailedError(
            result=intent.MatchTargetsResult(is_match=False),
            constraints=intent.MatchTargetsConstraints(),
        ),
        error_code=intent.IntentResponseErrorCode.NO_VALID_TARGETS,
        return_response=False,
    ),
    test.case(
        "handle_error",
        side_effect=intent.IntentHandleError(),
        error_code=intent.IntentResponseErrorCode.FAILED_TO_HANDLE,
        return_response=True,
    ),
    test.case(
        "unexpected_error",
        side_effect=intent.IntentUnexpectedError(),
        error_code=intent.IntentResponseErrorCode.UNKNOWN,
        return_response=True,
    ),
)
async def handle_failed_intents(
    side_effect: intent.IntentError,
    error_code: intent.IntentResponseErrorCode,
    return_response: bool,
    hass: HomeAssistant = Depends(_trigger_executor),
    area_registry: ar.AreaRegistry = Depends(area_registry_fixture),
) -> None:
    """Test that error results from intent handler are saved to chat_log."""
    expect(await async_setup_component(hass, "climate", {})).to_be_truthy()
    area_registry.async_create("living room")

    agent = async_get_agent(hass)

    user_input = ConversationInput(
        text="What is the temperature in the living room?",
        context=Context(),
        conversation_id=None,
        device_id=None,
        satellite_id=None,
        language=hass.config.language,
        agent_id=None,
    )

    with (
        patch(
            "homeassistant.components.conversation.default_agent.intent.async_handle",
            side_effect=side_effect,
        ) as mock_handle,
        chat_session.async_get_chat_session(hass) as session,
        async_get_chat_log(hass, session, user_input) as chat_log,
    ):
        response = await agent.async_handle_intents(user_input, chat_log)
        expect(len(chat_log.content)).to_equal(4)
        expect(chat_log.content[-1].role).to_equal("tool_result")

    expect(len(mock_handle.mock_calls)).to_equal(1)

    if return_response:
        expect(response is not None and response.error_code == error_code).to_be(True)
    else:
        expect(response).to_be(None)


@test
async def handle_intents_filters_results(
    hass: HomeAssistant = Depends(_trigger_executor),
    area_registry: ar.AreaRegistry = Depends(area_registry_fixture),
) -> None:
    """Test that handle_intents can filter responses."""
    expect(await async_setup_component(hass, "climate", {})).to_be_truthy()
    area_registry.async_create("living room")

    agent = async_get_agent(hass)

    user_input = ConversationInput(
        text="What is the temperature in the living room?",
        context=Context(),
        conversation_id=None,
        device_id=None,
        satellite_id=None,
        language=hass.config.language,
        agent_id=None,
    )

    mock_result = RecognizeResult(
        intent=Intent("HassTurnOn"),
        intent_data=IntentData([]),
        entities={},
        entities_list=[],
    )
    results = []

    def _filter_intents(result):
        results.append(result)
        return len(results) == 1

    with (
        patch(
            "homeassistant.components.conversation.default_agent.DefaultAgent.async_recognize_intent",
            return_value=mock_result,
        ) as mock_recognize,
        patch(
            "homeassistant.components.conversation.default_agent.DefaultAgent._async_process_intent_result",
        ) as mock_process,
        chat_session.async_get_chat_session(hass) as session,
        async_get_chat_log(hass, session, user_input) as chat_log,
    ):
        response = await agent.async_handle_intents(
            user_input, chat_log, intent_filter=_filter_intents
        )

        expect(len(mock_recognize.mock_calls)).to_equal(1)
        expect(len(mock_process.mock_calls)).to_equal(0)

        expect(response).to_be(None)

        expect(len(results)).to_equal(1)
        expect(results[0] is mock_result).to_be(True)

        response = await agent.async_handle_intents(
            user_input, chat_log, intent_filter=_filter_intents
        )

        expect(len(mock_recognize.mock_calls)).to_equal(2)
        expect(len(mock_process.mock_calls)).to_equal(2)

        expect(len(results)).to_equal(2)
        expect(results[1] is mock_result).to_be(True)

        expect(response is not None).to_be(True)


@test
async def state_names_are_not_translated(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that state names are not translated in responses."""
    await async_setup_component(hass, "weather", {})

    hass.states.async_set("weather.test_weather", weather.ATTR_CONDITION_PARTLYCLOUDY)
    expose_entity(hass, "weather.test_weather", True)

    with patch(
        "homeassistant.helpers.template.Template.async_render"
    ) as mock_async_render:
        result = await conversation.async_converse(
            hass, "what is the weather like?", None, Context(), None
        )
        expect(result.response.response_type).to_equal(
            intent.IntentResponseType.QUERY_ANSWER
        )
        mock_async_render.assert_called_once()

        expect(mock_async_render.call_args.args[0]["state"].state).to_equal(
            weather.ATTR_CONDITION_PARTLYCLOUDY
        )


@test
async def language_with_alternative_code(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test different codes for the same language."""
    entity_ids: dict[str, str] = {}
    for i, (lang_code, sentence, name) in enumerate(
        (
            ("no", "slå på lampen", "lampen"),
            ("no-NO", "slå på lampen", "lampen"),
            ("iw", "הדליקי את המנורה", "מנורה"),
        )
    ):
        if not (entity_id := entity_ids.get(name)):
            entity_id = f"light.test{i}"
            entity_ids[name] = entity_id

        hass.states.async_set(entity_id, "off", attributes={ATTR_FRIENDLY_NAME: name})
        calls = async_mock_service(hass, LIGHT_DOMAIN, "turn_on")
        await hass.services.async_call(
            "conversation",
            "process",
            {
                conversation.ATTR_TEXT: sentence,
                conversation.ATTR_LANGUAGE: lang_code,
            },
        )
        await hass.async_block_till_done()

        expect(len(calls)).to_equal(1)
        call = calls[0]
        expect(call.domain).to_equal(LIGHT_DOMAIN)
        expect(call.service).to_equal("turn_on")
        expect(call.data).to_equal({"entity_id": [entity_id]})


@test.cases(
    test.case(
        "time_fuzzy",
        fuzzy_matching=True,
        sentence="time",
        intent_type="HassGetCurrentTime",
        slots={},
    ),
    test.case(
        "time_no_fuzzy",
        fuzzy_matching=False,
        sentence="time",
        intent_type="HassGetCurrentTime",
        slots={},
    ),
    test.case(
        "timers_fuzzy",
        fuzzy_matching=True,
        sentence="how about my timers",
        intent_type="HassTimerStatus",
        slots={},
    ),
    test.case(
        "timers_no_fuzzy",
        fuzzy_matching=False,
        sentence="how about my timers",
        intent_type="HassTimerStatus",
        slots={},
    ),
    test.case(
        "blue_fuzzy",
        fuzzy_matching=True,
        sentence="the office needs more blue",
        intent_type="HassLightSet",
        slots={"area": "office", "color": "blue"},
    ),
    test.case(
        "blue_no_fuzzy",
        fuzzy_matching=False,
        sentence="the office needs more blue",
        intent_type="HassLightSet",
        slots={"area": "office", "color": "blue"},
    ),
    test.case(
        "brightness_fuzzy",
        fuzzy_matching=True,
        sentence="50% office light",
        intent_type="HassLightSet",
        slots={"name": "office light", "brightness": "50%"},
    ),
    test.case(
        "brightness_no_fuzzy",
        fuzzy_matching=False,
        sentence="50% office light",
        intent_type="HassLightSet",
        slots={"name": "office light", "brightness": "50%"},
    ),
    test.case(
        "spaceship_fuzzy",
        fuzzy_matching=True,
        sentence="turn on the lights in the spaceship",
        intent_type="HassTurnOn",
        slots={"domain": "lights", "area": "office"},
    ),
    test.case(
        "spaceship_no_fuzzy",
        fuzzy_matching=False,
        sentence="turn on the lights in the spaceship",
        intent_type="HassTurnOn",
        slots={"domain": "lights", "area": "office"},
    ),
)
async def fuzzy_matching(
    fuzzy_matching: bool,
    sentence: str,
    intent_type: str,
    slots: dict[str, Any],
    hass: HomeAssistant = Depends(hass_fixture),
    _network: None = Depends(mock_network_fixture),
    area_registry: ar.AreaRegistry = Depends(area_registry_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test fuzzy vs. non-fuzzy matching on some English sentences."""
    expect(await async_setup_component(hass, "homeassistant", {})).to_be_truthy()
    expect(await async_setup_component(hass, "conversation", {})).to_be_truthy()
    expect(await async_setup_component(hass, "intent", {})).to_be_truthy()
    await light_intent.async_setup_intents(hass)

    agent = async_get_agent(hass)
    agent.fuzzy_matching = fuzzy_matching

    area_office = area_registry.async_get_or_create("office_id")
    area_office = area_registry.async_update(area_office.id, name="office")

    entry = MockConfigEntry()
    entry.add_to_hass(hass)
    office_satellite = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        connections=set(),
        identifiers={("demo", "id-1234")},
    )
    device_registry.async_update_device(office_satellite.id, area_id=area_office.id)

    office_light = entity_registry.async_get_or_create(
        "light", "demo", "1234", original_name="office light"
    )
    office_light = entity_registry.async_update_entity(
        office_light.entity_id, area_id=area_office.id
    )
    hass.states.async_set(
        office_light.entity_id,
        "on",
        attributes={
            ATTR_FRIENDLY_NAME: "office light",
            ATTR_SUPPORTED_COLOR_MODES: [ColorMode.BRIGHTNESS, ColorMode.RGB],
        },
    )
    async_mock_service(hass, LIGHT_DOMAIN, "turn_on")

    result = await conversation.async_converse(
        hass,
        sentence,
        None,
        Context(),
        language="en",
        device_id=office_satellite.id,
    )
    response = result.response

    if not fuzzy_matching:
        expect(response.response_type).to_equal(intent.IntentResponseType.ERROR)
        return

    expect(
        response.response_type
        in (
            intent.IntentResponseType.ACTION_DONE,
            intent.IntentResponseType.QUERY_ANSWER,
        )
    ).to_be(True)
    expect(response.intent is not None).to_be(True)
    expect(response.intent.intent_type).to_equal(intent_type)

    actual_slots = {
        slot_name: slot_value["text"]
        for slot_name, slot_value in response.intent.slots.items()
        if slot_name != "preferred_area_id"
    }
    expect(actual_slots).to_equal(slots)


@test
async def intent_tool_call_in_chat_log(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that intent tool calls are stored in the chat log."""
    hass.states.async_set(
        "light.test_light", "off", attributes={ATTR_FRIENDLY_NAME: "Test Light"}
    )
    async_mock_service(hass, "light", "turn_on")

    result = await conversation.async_converse(
        hass, "turn on test light", None, Context(), None
    )

    expect(result.response.response_type).to_equal(
        intent.IntentResponseType.ACTION_DONE
    )

    with (
        chat_session.async_get_chat_session(hass, result.conversation_id) as session,
        async_get_chat_log(hass, session) as chat_log,
    ):
        pass

    tool_call_content: AssistantContent | None = None
    tool_result_content: ToolResultContent | None = None
    assistant_content: AssistantContent | None = None

    for content in chat_log.content:
        if content.role == "assistant" and content.tool_calls:
            tool_call_content = content
        if content.role == "tool_result":
            tool_result_content = content
        if content.role == "assistant" and not content.tool_calls:
            assistant_content = content

    expect(
        tool_call_content is not None and tool_call_content.tool_calls is not None
    ).to_be(True)
    expect(len(tool_call_content.tool_calls)).to_equal(1)
    expect(tool_call_content.tool_calls[0].tool_name).to_equal("HassTurnOn")
    expect(tool_call_content.tool_calls[0].external).to_be(True)
    expect(tool_call_content.tool_calls[0].tool_args.get("name")).to_equal("Test Light")

    expect(tool_result_content is not None).to_be(True)
    expect(tool_result_content.tool_name).to_equal("HassTurnOn")
    expect(tool_result_content.tool_result["response_type"]).to_equal("action_done")

    expect(assistant_content is not None).to_be(True)
    expect(assistant_content.content is not None).to_be(True)


@test
async def trigger_tool_call_in_chat_log(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that trigger tool calls are stored in the chat log."""
    trigger_sentence = "test automation trigger"
    trigger_response = "Trigger activated!"

    manager = get_agent_manager(hass)
    callback_mock = AsyncMock(return_value=trigger_response)
    manager.register_trigger([trigger_sentence], callback_mock)

    result = await conversation.async_converse(
        hass, trigger_sentence, None, Context(), None
    )

    expect(result.response.response_type).to_equal(
        intent.IntentResponseType.ACTION_DONE
    )

    with (
        chat_session.async_get_chat_session(hass, result.conversation_id) as session,
        async_get_chat_log(hass, session) as chat_log,
    ):
        pass

    tool_call_content: AssistantContent | None = None
    tool_result_content: ToolResultContent | None = None

    for content in chat_log.content:
        if content.role == "assistant" and content.tool_calls:
            tool_call_content = content
        if content.role == "tool_result":
            tool_result_content = content

    expect(
        tool_call_content is not None and tool_call_content.tool_calls is not None
    ).to_be(True)
    expect(len(tool_call_content.tool_calls)).to_equal(1)
    expect(tool_call_content.tool_calls[0].tool_name).to_equal("trigger_sentence")
    expect(tool_call_content.tool_calls[0].external).to_be(True)
    expect(tool_call_content.tool_calls[0].tool_args).to_equal({})

    expect(tool_result_content is not None).to_be(True)
    expect(tool_result_content.tool_name).to_equal("trigger_sentence")
    expect(tool_result_content.tool_result["response"]).to_equal(trigger_response)


@test
async def no_tool_call_on_no_intent_match(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that no tool call is stored when no intent is matched."""
    result = await conversation.async_converse(
        hass, "this is a random sentence that should not match", None, Context(), None
    )

    expect(result.response.response_type).to_equal(intent.IntentResponseType.ERROR)

    with (
        chat_session.async_get_chat_session(hass, result.conversation_id) as session,
        async_get_chat_log(hass, session) as chat_log,
    ):
        pass

    assistant_found = False
    for content in chat_log.content:
        if content.role == "assistant":
            assistant_found = True
            expect(
                content.tool_calls is None or len(content.tool_calls) == 0
            ).to_be(True)
            break

    expect(assistant_found).to_be(True)


@test
async def intent_tool_call_with_error_response(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that intent tool calls store error information correctly."""
    result = await conversation.async_converse(
        hass, "turn on the non existent device", None, Context(), None
    )

    expect(result.response.response_type).to_equal(intent.IntentResponseType.ERROR)
    expect(result.response.error_code).to_equal(
        intent.IntentResponseErrorCode.NO_VALID_TARGETS
    )

    with (
        chat_session.async_get_chat_session(hass, result.conversation_id) as session,
        async_get_chat_log(hass, session) as chat_log,
    ):
        pass

    tool_call_found = False
    for content in chat_log.content:
        if content.role == "assistant" and content.tool_calls:
            tool_call_found = True

    expect(tool_call_found).to_be(False)
