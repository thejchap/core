"""Tests for Intent component."""

from typing import Any

from tryke import Depends, expect, fixture, test

from homeassistant.components import conversation
from homeassistant.components.button import SERVICE_PRESS
from homeassistant.components.cover import (
    DOMAIN as COVER_DOMAIN,
    SERVICE_CLOSE_COVER,
    SERVICE_OPEN_COVER,
    SERVICE_STOP_COVER,
    CoverState,
)
from homeassistant.components.homeassistant.exposed_entities import async_expose_entity
from homeassistant.components.lock import SERVICE_LOCK, SERVICE_UNLOCK
from homeassistant.components.valve import (
    DOMAIN as VALVE_DOMAIN,
    SERVICE_CLOSE_VALVE,
    SERVICE_OPEN_VALVE,
    SERVICE_STOP_VALVE,
    ValveState,
)
from homeassistant.const import (
    ATTR_DEVICE_CLASS,
    ATTR_FRIENDLY_NAME,
    SERVICE_TOGGLE,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar, entity_registry as er, intent
from homeassistant.setup import async_setup_component

from tests.common import MockUser, async_mock_service
from tests.hass_fixtures import (
    ClientSessionGenerator,
    area_registry as area_registry_fixture,
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    hass_admin_user as hass_admin_user_fixture,
    hass_client as hass_client_fixture,
)
from tests.hass_tryke_helpers import expect_raises_async


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def http_handle_intent(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
    hass_admin_user: MockUser = Depends(hass_admin_user_fixture),
) -> None:
    """Test handle intent via HTTP API."""

    class TestIntentHandler(intent.IntentHandler):
        """Test Intent Handler."""

        intent_type = "OrderBeer"

        async def async_handle(self, intent_obj):
            """Handle the intent."""
            expect(intent_obj.context.user_id).to_equal(hass_admin_user.id)
            response = intent_obj.create_response()
            response.async_set_speech(
                f"I've ordered a {intent_obj.slots['type']['value']}!"
            )
            response.async_set_card(
                "Beer ordered",
                f"You chose a {intent_obj.slots['type']['value']}.",
            )
            return response

    intent.async_register(hass, TestIntentHandler())

    result = await async_setup_component(hass, "intent", {})
    expect(bool(result)).to_be(True)

    client = await hass_client()
    resp = await client.post(
        "/api/intent/handle", json={"name": "OrderBeer", "data": {"type": "Belgian"}}
    )

    expect(resp.status).to_equal(200)
    data = await resp.json()

    expect(data).to_equal(
        {
            "card": {
                "simple": {"content": "You chose a Belgian.", "title": "Beer ordered"}
            },
            "speech": {
                "plain": {
                    "extra_data": None,
                    "speech": "I've ordered a Belgian!",
                }
            },
            "language": hass.config.language,
            "response_type": intent.IntentResponseType.ACTION_DONE.value,
            "data": {"success": [], "failed": []},
        }
    )


@test
async def http_language_device_satellite_id(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
    hass_admin_user: MockUser = Depends(hass_admin_user_fixture),
) -> None:
    """Test handle intent with language, device id, and satellite id."""
    device_id = "test-device-id"
    satellite_id = "test-satellite-id"
    language = "en-GB"

    class TestIntentHandler(intent.IntentHandler):
        """Test Intent Handler."""

        intent_type = "TestIntent"

        async def async_handle(self, intent_obj: intent.Intent):
            """Handle the intent."""
            expect(intent_obj.context.user_id).to_equal(hass_admin_user.id)
            expect(intent_obj.language).to_equal(language)
            expect(intent_obj.device_id).to_equal(device_id)
            expect(intent_obj.satellite_id).to_equal(satellite_id)

            response = intent_obj.create_response()
            response.async_set_speech("Test response")
            response.async_set_speech_slots({"slot1": "value 1", "slot2": 2})
            return response

    intent.async_register(hass, TestIntentHandler())

    result = await async_setup_component(hass, "intent", {})
    expect(bool(result)).to_be(True)

    client = await hass_client()
    resp = await client.post(
        "/api/intent/handle",
        json={
            "name": "TestIntent",
            "language": language,
            "device_id": device_id,
            "satellite_id": satellite_id,
        },
    )

    expect(resp.status).to_equal(200)
    data = await resp.json()

    expect(data).to_equal(
        {
            "card": {},
            "speech": {
                "plain": {
                    "extra_data": None,
                    "speech": "Test response",
                }
            },
            "speech_slots": {
                "slot1": "value 1",
                "slot2": 2,
            },
            "language": language,
            "response_type": "action_done",
            "data": {"success": [], "failed": []},
        }
    )


@test
async def http_handle_intent_match_failure(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
    hass_admin_user: MockUser = Depends(hass_admin_user_fixture),
) -> None:
    """Test handle intent match failure via HTTP API."""

    expect(await async_setup_component(hass, "intent", {})).to_be(True)

    hass.states.async_set(
        "cover.garage_door_1", "closed", {ATTR_FRIENDLY_NAME: "Garage Door"}
    )
    hass.states.async_set(
        "cover.garage_door_2", "closed", {ATTR_FRIENDLY_NAME: "Garage Door"}
    )
    async_mock_service(hass, "cover", SERVICE_OPEN_COVER)

    client = await hass_client()
    resp = await client.post(
        "/api/intent/handle",
        json={"name": "HassTurnOn", "data": {"name": "Garage Door"}},
    )
    expect(resp.status).to_equal(200)
    data = await resp.json()

    expect("DUPLICATE_NAME" in data["speech"]["plain"]["speech"]).to_be(True)


@test
async def http_assistant(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
    hass_admin_user: MockUser = Depends(hass_admin_user_fixture),
) -> None:
    """Test handle intent only targets exposed entities with 'assistant' set."""

    expect(await async_setup_component(hass, "homeassistant", {})).to_be(True)
    expect(await async_setup_component(hass, "intent", {})).to_be(True)

    hass.states.async_set(
        "cover.garage_door_1", "closed", {ATTR_FRIENDLY_NAME: "Garage Door 1"}
    )
    async_mock_service(hass, "cover", SERVICE_OPEN_COVER)

    client = await hass_client()

    async_expose_entity(hass, conversation.DOMAIN, "cover.garage_door_1", True)
    resp = await client.post(
        "/api/intent/handle",
        json={
            "name": "HassTurnOn",
            "data": {"name": "Garage Door 1"},
            "assistant": conversation.DOMAIN,
        },
    )
    expect(resp.status).to_equal(200)
    data = await resp.json()
    expect(data["response_type"]).to_equal(intent.IntentResponseType.ACTION_DONE.value)

    async_expose_entity(hass, conversation.DOMAIN, "cover.garage_door_1", False)
    resp = await client.post(
        "/api/intent/handle",
        json={
            "name": "HassTurnOn",
            "data": {"name": "Garage Door 1"},
            "assistant": conversation.DOMAIN,
        },
    )
    expect(resp.status).to_equal(200)
    data = await resp.json()
    expect(data["response_type"]).to_equal(intent.IntentResponseType.ERROR.value)
    expect(data["data"]["code"]).to_equal(
        intent.IntentResponseErrorCode.FAILED_TO_HANDLE.value
    )

    resp = await client.post(
        "/api/intent/handle",
        json={"name": "HassTurnOn", "data": {"name": "Garage Door 1"}},
    )
    expect(resp.status).to_equal(200)
    data = await resp.json()
    expect(data["response_type"]).to_equal(intent.IntentResponseType.ACTION_DONE.value)


@test
async def cover_intents_loading(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test Cover Intents Loading."""
    expect(await async_setup_component(hass, "intent", {})).to_be(True)

    async with expect_raises_async(intent.UnknownIntent):
        await intent.async_handle(
            hass, "test", "HassOpenCover", {"name": {"value": "garage door"}}
        )

    expect(await async_setup_component(hass, "cover", {})).to_be(True)
    await hass.async_block_till_done()

    hass.states.async_set("cover.garage_door", "closed")
    calls = async_mock_service(hass, "cover", SERVICE_OPEN_COVER)

    await intent.async_handle(
        hass, "test", "HassOpenCover", {"name": {"value": "garage door"}}
    )
    await hass.async_block_till_done()

    expect(len(calls)).to_equal(1)
    call = calls[0]
    expect(call.domain).to_equal("cover")
    expect(call.service).to_equal("open_cover")
    expect(call.data).to_equal({"entity_id": "cover.garage_door"})


@test
async def turn_on_intent(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test HassTurnOn intent."""
    result = await async_setup_component(hass, "homeassistant", {})
    result = await async_setup_component(hass, "intent", {})
    await hass.async_block_till_done()
    expect(bool(result)).to_be(True)

    hass.states.async_set("light.test_light", "off")
    calls = async_mock_service(hass, "light", SERVICE_TURN_ON)

    await intent.async_handle(
        hass, "test", "HassTurnOn", {"name": {"value": "test light"}}
    )
    await hass.async_block_till_done()

    expect(len(calls)).to_equal(1)
    call = calls[0]
    expect(call.domain).to_equal("light")
    expect(call.service).to_equal("turn_on")
    expect(call.data).to_equal({"entity_id": ["light.test_light"]})


@test.cases(
    test.case("button", domain="button"),
    test.case("input_button", domain="input_button"),
)
async def turn_on_intent_button(
    domain: str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test HassTurnOn intent on button domains."""
    expect(await async_setup_component(hass, "intent", {})).to_be(True)

    button = entity_registry.async_get_or_create(domain, "test", "button_uid")

    hass.states.async_set(button.entity_id, "unknown")
    button_service_calls = async_mock_service(hass, domain, SERVICE_PRESS)

    async with expect_raises_async(intent.IntentHandleError):
        await intent.async_handle(
            hass, "test", "HassTurnOff", {"name": {"value": button.entity_id}}
        )

    await intent.async_handle(
        hass, "test", "HassTurnOn", {"name": {"value": button.entity_id}}
    )

    expect(len(button_service_calls)).to_equal(1)
    call = button_service_calls[0]
    expect(call.domain).to_equal(domain)
    expect(call.service).to_equal(SERVICE_PRESS)
    expect(call.data).to_equal({"entity_id": button.entity_id})


@test
async def turn_on_off_intent_valve(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test HassTurnOn/Off intent on valve domains."""
    expect(await async_setup_component(hass, "intent", {})).to_be(True)

    valve = entity_registry.async_get_or_create("valve", "test", "valve_uid")

    hass.states.async_set(valve.entity_id, "closed")
    open_calls = async_mock_service(hass, "valve", SERVICE_OPEN_VALVE)
    close_calls = async_mock_service(hass, "valve", SERVICE_CLOSE_VALVE)

    await intent.async_handle(
        hass, "test", "HassTurnOn", {"name": {"value": valve.entity_id}}
    )

    expect(len(open_calls)).to_equal(1)
    call = open_calls[0]
    expect(call.domain).to_equal("valve")
    expect(call.service).to_equal(SERVICE_OPEN_VALVE)
    expect(call.data).to_equal({"entity_id": valve.entity_id})

    await intent.async_handle(
        hass, "test", "HassTurnOff", {"name": {"value": valve.entity_id}}
    )

    expect(len(close_calls)).to_equal(1)
    call = close_calls[0]
    expect(call.domain).to_equal("valve")
    expect(call.service).to_equal(SERVICE_CLOSE_VALVE)
    expect(call.data).to_equal({"entity_id": valve.entity_id})


@test
async def turn_on_off_intent_cover(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test HassTurnOn/Off intent on cover domains."""
    expect(await async_setup_component(hass, "intent", {})).to_be(True)

    cover = entity_registry.async_get_or_create("cover", "test", "cover_uid")

    hass.states.async_set(cover.entity_id, "closed")
    open_calls = async_mock_service(hass, "cover", SERVICE_OPEN_COVER)
    close_calls = async_mock_service(hass, "cover", SERVICE_CLOSE_COVER)

    await intent.async_handle(
        hass, "test", "HassTurnOn", {"name": {"value": cover.entity_id}}
    )

    expect(len(open_calls)).to_equal(1)
    call = open_calls[0]
    expect(call.domain).to_equal("cover")
    expect(call.service).to_equal(SERVICE_OPEN_COVER)
    expect(call.data).to_equal({"entity_id": cover.entity_id})

    await intent.async_handle(
        hass, "test", "HassTurnOff", {"name": {"value": cover.entity_id}}
    )

    expect(len(close_calls)).to_equal(1)
    call = close_calls[0]
    expect(call.domain).to_equal("cover")
    expect(call.service).to_equal(SERVICE_CLOSE_COVER)
    expect(call.data).to_equal({"entity_id": cover.entity_id})


@test
async def turn_on_off_intent_lock(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test HassTurnOn/Off intent on lock domains."""
    expect(await async_setup_component(hass, "intent", {})).to_be(True)

    lock = entity_registry.async_get_or_create("lock", "test", "lock_uid")

    hass.states.async_set(lock.entity_id, "locked")
    unlock_calls = async_mock_service(hass, "lock", SERVICE_UNLOCK)
    lock_calls = async_mock_service(hass, "lock", SERVICE_LOCK)

    await intent.async_handle(
        hass, "test", "HassTurnOn", {"name": {"value": lock.entity_id}}
    )

    expect(len(lock_calls)).to_equal(1)
    call = lock_calls[0]
    expect(call.domain).to_equal("lock")
    expect(call.service).to_equal(SERVICE_LOCK)
    expect(call.data).to_equal({"entity_id": lock.entity_id})

    await intent.async_handle(
        hass, "test", "HassTurnOff", {"name": {"value": lock.entity_id}}
    )

    expect(len(unlock_calls)).to_equal(1)
    call = unlock_calls[0]
    expect(call.domain).to_equal("lock")
    expect(call.service).to_equal(SERVICE_UNLOCK)
    expect(call.data).to_equal({"entity_id": lock.entity_id})


@test
async def turn_off_intent(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test HassTurnOff intent."""
    result = await async_setup_component(hass, "homeassistant", {})
    result = await async_setup_component(hass, "intent", {})
    expect(bool(result)).to_be(True)

    hass.states.async_set("light.test_light", "on")
    calls = async_mock_service(hass, "light", SERVICE_TURN_OFF)

    await intent.async_handle(
        hass, "test", "HassTurnOff", {"name": {"value": "test light"}}
    )
    await hass.async_block_till_done()

    expect(len(calls)).to_equal(1)
    call = calls[0]
    expect(call.domain).to_equal("light")
    expect(call.service).to_equal("turn_off")
    expect(call.data).to_equal({"entity_id": ["light.test_light"]})


@test
async def toggle_intent(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test HassToggle intent."""
    result = await async_setup_component(hass, "homeassistant", {})
    result = await async_setup_component(hass, "intent", {})
    expect(bool(result)).to_be(True)

    hass.states.async_set("light.test_light", "off")
    calls = async_mock_service(hass, "light", SERVICE_TOGGLE)

    await intent.async_handle(
        hass, "test", "HassToggle", {"name": {"value": "test light"}}
    )
    await hass.async_block_till_done()

    expect(len(calls)).to_equal(1)
    call = calls[0]
    expect(call.domain).to_equal("light")
    expect(call.service).to_equal("toggle")
    expect(call.data).to_equal({"entity_id": ["light.test_light"]})


@test
async def turn_on_multiple_intent(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test HassTurnOn intent with multiple similar entities.

    This tests that matching finds the proper entity among similar names.
    """
    result = await async_setup_component(hass, "homeassistant", {})
    result = await async_setup_component(hass, "intent", {})
    expect(bool(result)).to_be(True)

    hass.states.async_set("light.test_light", "off")
    hass.states.async_set("light.test_lights_2", "off")
    hass.states.async_set("light.test_lighter", "off")
    calls = async_mock_service(hass, "light", SERVICE_TURN_ON)

    await intent.async_handle(
        hass, "test", "HassTurnOn", {"name": {"value": "test lights 2"}}
    )
    await hass.async_block_till_done()

    expect(len(calls)).to_equal(1)
    call = calls[0]
    expect(call.domain).to_equal("light")
    expect(call.service).to_equal("turn_on")
    expect(call.data).to_equal({"entity_id": ["light.test_lights_2"]})


@test
async def turn_on_all(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test HassTurnOn intent with "all" name."""
    result = await async_setup_component(hass, "homeassistant", {})
    result = await async_setup_component(hass, "intent", {})
    expect(bool(result)).to_be(True)

    hass.states.async_set("light.test_light", "off")
    hass.states.async_set("light.test_light_2", "off")
    calls = async_mock_service(hass, "light", SERVICE_TURN_ON)

    await intent.async_handle(
        hass,
        "test",
        "HassTurnOn",
        {"name": {"value": "all"}, "domain": {"value": "light"}},
    )
    await hass.async_block_till_done()

    expect(len(calls)).to_equal(2)
    entity_ids = set()
    for call in calls:
        expect(call.domain).to_equal("light")
        expect(call.service).to_equal("turn_on")
        entity_ids.update(call.data.get("entity_id", []))

    expect(entity_ids).to_equal({"light.test_light", "light.test_light_2"})


@test
async def get_state_intent(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    area_registry: ar.AreaRegistry = Depends(area_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test HassGetState intent.

    This tests name, area, domain, device class, and state constraints.
    """
    expect(await async_setup_component(hass, "homeassistant", {})).to_be(True)
    expect(await async_setup_component(hass, "intent", {})).to_be(True)

    bedroom = area_registry.async_get_or_create("bedroom")
    kitchen = area_registry.async_get_or_create("kitchen")
    office = area_registry.async_get_or_create("office")

    bedroom_light = entity_registry.async_get_or_create(
        "light", "demo", "1", original_name="bedroom light"
    )
    entity_registry.async_update_entity(bedroom_light.entity_id, area_id=bedroom.id)

    kitchen_sensor = entity_registry.async_get_or_create(
        "sensor", "demo", "2", original_name="kitchen sensor"
    )
    entity_registry.async_update_entity(kitchen_sensor.entity_id, area_id=kitchen.id)

    kitchen_light = entity_registry.async_get_or_create(
        "light", "demo", "3", original_name="kitchen light"
    )
    entity_registry.async_update_entity(kitchen_light.entity_id, area_id=kitchen.id)

    kitchen_sensor = entity_registry.async_get_or_create(
        "sensor", "demo", "4", original_name="kitchen sensor"
    )
    entity_registry.async_update_entity(kitchen_sensor.entity_id, area_id=kitchen.id)

    problem_sensor = entity_registry.async_get_or_create(
        "binary_sensor", "demo", "5", original_name="problem sensor"
    )
    entity_registry.async_update_entity(problem_sensor.entity_id, area_id=office.id)

    moisture_sensor = entity_registry.async_get_or_create(
        "binary_sensor", "demo", "6", original_name="moisture sensor"
    )
    entity_registry.async_update_entity(moisture_sensor.entity_id, area_id=office.id)

    hass.states.async_set(
        bedroom_light.entity_id, "off", attributes={ATTR_FRIENDLY_NAME: "bedroom light"}
    )
    hass.states.async_set(
        kitchen_light.entity_id, "on", attributes={ATTR_FRIENDLY_NAME: "kitchen light"}
    )
    hass.states.async_set(
        kitchen_sensor.entity_id,
        "50.0",
        attributes={ATTR_FRIENDLY_NAME: "kitchen sensor"},
    )
    hass.states.async_set(
        problem_sensor.entity_id,
        "on",
        attributes={ATTR_FRIENDLY_NAME: "problem sensor", ATTR_DEVICE_CLASS: "problem"},
    )
    hass.states.async_set(
        moisture_sensor.entity_id,
        "on",
        attributes={
            ATTR_FRIENDLY_NAME: "moisture sensor",
            ATTR_DEVICE_CLASS: "moisture",
        },
    )

    # is bedroom light off?
    result = await intent.async_handle(
        hass,
        "test",
        "HassGetState",
        {"name": {"value": "bedroom light"}, "state": {"value": "off"}},
    )

    expect(result.response_type).to_be(intent.IntentResponseType.QUERY_ANSWER)
    expect(
        bool(result.matched_states)
        and result.matched_states[0].entity_id == bedroom_light.entity_id
    ).to_be(True)
    expect(bool(result.unmatched_states)).to_be(False)

    # is light in kitchen off?
    result = await intent.async_handle(
        hass,
        "test",
        "HassGetState",
        {
            "area": {"value": "kitchen"},
            "domain": {"value": "light"},
            "state": {"value": "off"},
        },
    )

    expect(result.response_type).to_be(intent.IntentResponseType.QUERY_ANSWER)
    expect(bool(result.matched_states)).to_be(False)
    expect(
        bool(result.unmatched_states)
        and result.unmatched_states[0].entity_id == kitchen_light.entity_id
    ).to_be(True)

    # what is the value of the kitchen sensor?
    result = await intent.async_handle(
        hass,
        "test",
        "HassGetState",
        {
            "name": {"value": "kitchen sensor"},
        },
    )

    expect(result.response_type).to_be(intent.IntentResponseType.QUERY_ANSWER)
    expect(
        bool(result.matched_states)
        and result.matched_states[0].entity_id == kitchen_sensor.entity_id
    ).to_be(True)
    expect(bool(result.unmatched_states)).to_be(False)

    # is there a problem in the office?
    result = await intent.async_handle(
        hass,
        "test",
        "HassGetState",
        {
            "area": {"value": "office"},
            "device_class": {"value": "problem"},
            "state": {"value": "on"},
        },
    )

    expect(result.response_type).to_be(intent.IntentResponseType.QUERY_ANSWER)
    expect(
        bool(result.matched_states)
        and result.matched_states[0].entity_id == problem_sensor.entity_id
    ).to_be(True)
    expect(bool(result.unmatched_states)).to_be(False)

    # is there a problem or a moisture sensor in the office?
    result = await intent.async_handle(
        hass,
        "test",
        "HassGetState",
        {
            "area": {"value": "office"},
            "device_class": {"value": ["problem", "moisture"]},
        },
    )

    expect(len(result.matched_states) == 2).to_be(True)
    expect(
        {state.entity_id for state in result.matched_states}
    ).to_equal({problem_sensor.entity_id, moisture_sensor.entity_id})
    expect(bool(result.unmatched_states)).to_be(False)

    # are there any binary sensors in the kitchen?
    result = await intent.async_handle(
        hass,
        "test",
        "HassGetState",
        {
            "area": {"value": "kitchen"},
            "domain": {"value": "binary_sensor"},
        },
    )

    expect(result.response_type).to_be(intent.IntentResponseType.QUERY_ANSWER)
    expect(bool(result.matched_states)).to_be(False)
    expect(bool(result.unmatched_states)).to_be(False)

    async with expect_raises_async(intent.MatchFailedError):
        await intent.async_handle(
            hass,
            "test",
            "HassGetState",
            {
                "area": {"value": "does-not-exist"},
                "domain": {"value": "light"},
            },
        )


@test
async def set_position_intent_unsupported_domain(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that HassSetPosition intent fails with unsupported domain."""
    expect(await async_setup_component(hass, "homeassistant", {})).to_be(True)
    expect(await async_setup_component(hass, "intent", {})).to_be(True)

    hass.states.async_set("light.test_light", "off")

    async with expect_raises_async(intent.IntentHandleError):
        await intent.async_handle(
            hass,
            "test",
            "HassSetPosition",
            {"name": {"value": "test light"}, "position": {"value": 100}},
        )


@test
async def intents_with_no_responses(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test intents that should not return a response during handling."""
    expect(await async_setup_component(hass, "homeassistant", {})).to_be(True)
    expect(await async_setup_component(hass, "intent", {})).to_be(True)

    for intent_name in (intent.INTENT_NEVERMIND, intent.INTENT_RESPOND):
        response = await intent.async_handle(hass, "test", intent_name, {})
        expect(bool(response.speech)).to_be(False)


@test
async def intents_respond_intent(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test HassRespond intent with a response slot value."""
    expect(await async_setup_component(hass, "homeassistant", {})).to_be(True)
    expect(await async_setup_component(hass, "intent", {})).to_be(True)

    response = await intent.async_handle(
        hass, "test", intent.INTENT_RESPOND, {"response": {"value": "Hello World"}}
    )
    expect(response.speech["plain"]["speech"]).to_equal("Hello World")


@test
async def stop_moving_valve(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test HassStopMoving intent for valves."""
    expect(await async_setup_component(hass, "intent", {})).to_be(True)

    entity_id = f"{VALVE_DOMAIN}.test_valve"
    hass.states.async_set(entity_id, ValveState.OPEN)
    calls = async_mock_service(hass, VALVE_DOMAIN, SERVICE_STOP_VALVE)

    response = await intent.async_handle(
        hass, "test", intent.INTENT_STOP_MOVING, {"name": {"value": "test valve"}}
    )
    await hass.async_block_till_done()

    expect(response.response_type).to_be(intent.IntentResponseType.ACTION_DONE)
    expect(len(calls)).to_equal(1)
    call = calls[0]
    expect(call.domain).to_equal(VALVE_DOMAIN)
    expect(call.service).to_equal(SERVICE_STOP_VALVE)
    expect(call.data).to_equal({"entity_id": entity_id})


@test.cases(
    test.case("by_name", slots={"name": {"value": "test cover"}}),
    test.case("by_device_class", slots={"device_class": {"value": "shade"}}),
)
async def stop_moving_cover(
    slots: dict[str, Any],
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test HassStopMoving intent for covers."""
    expect(await async_setup_component(hass, "intent", {})).to_be(True)

    entity_id = f"{COVER_DOMAIN}.test_cover"
    hass.states.async_set(
        entity_id, CoverState.OPEN, attributes={"device_class": "shade"}
    )
    calls = async_mock_service(hass, COVER_DOMAIN, SERVICE_STOP_COVER)

    response = await intent.async_handle(hass, "test", intent.INTENT_STOP_MOVING, slots)
    await hass.async_block_till_done()

    expect(response.response_type).to_be(intent.IntentResponseType.ACTION_DONE)
    expect(len(calls)).to_equal(1)
    call = calls[0]
    expect(call.domain).to_equal(COVER_DOMAIN)
    expect(call.service).to_equal(SERVICE_STOP_COVER)
    expect(call.data).to_equal({"entity_id": entity_id})


@test
async def stop_moving_intent_unsupported_domain(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that HassStopMoving intent fails with unsupported domain."""
    expect(await async_setup_component(hass, "homeassistant", {})).to_be(True)
    expect(await async_setup_component(hass, "intent", {})).to_be(True)

    hass.states.async_set("light.test_light", "on")

    async with expect_raises_async(intent.IntentHandleError):
        await intent.async_handle(
            hass, "test", intent.INTENT_STOP_MOVING, {"name": {"value": "test light"}}
        )
