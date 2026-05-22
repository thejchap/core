"""The tests for the Script component."""

import asyncio
from datetime import timedelta
from typing import Any
from unittest.mock import ANY, Mock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components import script
from homeassistant.components.script import DOMAIN, EVENT_SCRIPT_STARTED, ScriptEntity
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_NAME,
    SERVICE_RELOAD,
    SERVICE_TOGGLE,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_UNAVAILABLE,
)
from homeassistant.core import (
    Context,
    CoreState,
    HomeAssistant,
    ServiceCall,
    State,
    callback,
    split_entity_id,
)
from homeassistant.exceptions import ServiceNotFound, TemplateError
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.event import async_track_state_change
from homeassistant.helpers.script import (
    SCRIPT_MODE_CHOICES,
    SCRIPT_MODE_PARALLEL,
    SCRIPT_MODE_QUEUED,
    SCRIPT_MODE_RESTART,
    SCRIPT_MODE_SINGLE,
    _async_stop_scripts_at_shutdown,
)
from homeassistant.helpers.service import async_get_all_descriptions
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from tests.common import (
    MockConfigEntry,
    MockUser,
    async_fire_time_changed,
    async_mock_service,
    mock_restore_cache,
)
from tests.components.logbook.common import MockRow, mock_humanify
from tests.components.repairs import get_repairs
from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fixture,
    device_registry as device_registry_fixture,
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    hass_admin_user as hass_admin_user_fixture,
    hass_ws_client as hass_ws_client_fixture,
)
from tests.typing import WebSocketGenerator

ENTITY_ID = "script.test"


@fixture
def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Anchor fixture for the module."""
    return hass


@fixture
def calls(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> list[ServiceCall]:
    """Track calls to a mock service."""
    return async_mock_service(hass, "test", "script")


@test
async def passing_variables(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test different ways of passing in variables."""
    mock_restore_cache(hass, ())
    calls: list[ServiceCall] = []
    context = Context()

    @callback
    def record_call(service: ServiceCall) -> None:
        """Add recorded event to set."""
        calls.append(service)

    hass.services.async_register("test", "script", record_call)

    expect(
        await async_setup_component(
            hass,
            "script",
            {
                "script": {
                    "test": {
                        "sequence": {
                            "action": "test.script",
                            "data_template": {"hello": "{{ greeting }}"},
                        }
                    }
                }
            },
        )
    ).to_be_truthy()

    await hass.services.async_call(
        DOMAIN, "test", {"greeting": "world"}, context=context
    )

    await hass.async_block_till_done()

    expect(len(calls)).to_equal(1)
    expect(calls[0].context).to_be(context)
    expect(calls[0].data["hello"]).to_equal("world")

    await hass.services.async_call(
        "script", "test", {"greeting": "universe"}, context=context
    )

    await hass.async_block_till_done()

    expect(len(calls)).to_equal(2)
    expect(calls[1].context).to_be(context)
    expect(calls[1].data["hello"]).to_equal("universe")


async def _verify_turn_on_off_toggle(
    hass: HomeAssistant, toggle: bool, action_schema_variations: str
) -> None:
    """Helper used by parametrized turn_on_off_toggle tests."""
    event = "test_event"
    event_mock = Mock()

    hass.bus.async_listen(event, event_mock)

    was_on = False

    @callback
    def state_listener(entity_id: str, old_state: Any, new_state: Any) -> None:
        nonlocal was_on
        was_on = True

    async_track_state_change(hass, ENTITY_ID, state_listener, to_state="on")

    if toggle:
        turn_off_step = {
            action_schema_variations: "script.toggle",
            "entity_id": ENTITY_ID,
        }
    else:
        turn_off_step = {
            action_schema_variations: "script.turn_off",
            "entity_id": ENTITY_ID,
        }
    expect(
        await async_setup_component(
            hass,
            "script",
            {
                "script": {
                    "test": {
                        "sequence": [
                            {"event": event},
                            turn_off_step,
                            {"event": event},
                        ]
                    }
                }
            },
        )
    ).to_be_truthy()

    expect(script.is_on(hass, ENTITY_ID)).to_be(False)

    if toggle:
        await hass.services.async_call(
            DOMAIN, SERVICE_TOGGLE, {ATTR_ENTITY_ID: ENTITY_ID}
        )
    else:
        await hass.services.async_call(DOMAIN, split_entity_id(ENTITY_ID)[1])
    await hass.async_block_till_done()

    expect(script.is_on(hass, ENTITY_ID)).to_be(False)
    expect(was_on).to_be(True)
    expect(event_mock.call_count).to_equal(1)


@test.cases(
    test.case(
        "action_no_toggle", toggle=False, action_schema_variations="action"
    ),
    test.case(
        "service_no_toggle", toggle=False, action_schema_variations="service"
    ),
    test.case(
        "action_toggle", toggle=True, action_schema_variations="action"
    ),
    test.case(
        "service_toggle", toggle=True, action_schema_variations="service"
    ),
)
async def turn_on_off_toggle_cases(
    toggle: bool,
    action_schema_variations: str,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Verify turn_on, turn_off & toggle services."""
    await _verify_turn_on_off_toggle(hass, toggle, action_schema_variations)


@test.cases(
    test.case(
        "empty_test",
        config={"test": {}},
        nbr_script_entities=1,
    ),
    test.case(
        "invalid_slug",
        config={"test hello world": {"sequence": [{"event": "bla"}]}},
        nbr_script_entities=0,
    ),
    test.case(
        "test_with_event_action",
        config={
            "test": {
                "sequence": {
                    "event": "test_event",
                    "action": "homeassistant.turn_on",
                }
            }
        },
        nbr_script_entities=1,
    ),
)
async def setup_with_invalid_configs(
    config: dict[str, Any],
    nbr_script_entities: int,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test setup with invalid configs."""
    expect(
        await async_setup_component(hass, "script", {"script": config})
    ).to_be_truthy()

    expect(len(hass.states.async_entity_ids("script"))).to_equal(nbr_script_entities)


@test.cases(
    test.case(
        "bad_slug",
        object_id="Bad Script",
        broken_config={},
        problem="has invalid object id",
        details="invalid slug Bad Script",
    ),
    test.case(
        "reserved_name",
        object_id="turn_on",
        broken_config={},
        problem="has invalid object id",
        details=(
            "A script's object_id must not be one of "
            "reload, toggle, turn_off, turn_on. Got 'turn_on'"
        ),
    ),
)
async def bad_config_validation_critical(
    object_id: str,
    broken_config: dict[str, Any],
    problem: str,
    details: str,
    hass: HomeAssistant = Depends(_trigger_executor),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test bad script configuration which can be detected during validation."""
    expect(
        await async_setup_component(
            hass,
            script.DOMAIN,
            {
                script.DOMAIN: {
                    object_id: {"alias": "bad_script", **broken_config},
                    "good_script": {
                        "alias": "good_script",
                        "sequence": {
                            "action": "test.automation",
                            "entity_id": "hello.world",
                        },
                    },
                }
            },
        )
    ).to_be_truthy()

    expect(
        f"Script with alias 'bad_script' {problem} and has been disabled: {details}"
        in caplog.text
    ).to_be(True)

    expect(hass.states.async_entity_ids("script")).to_equal(["script.good_script"])


@test.skip("pending tryke port - requires hass_ws_client + hass_admin_user + repairs helpers")
async def bad_config_validation() -> None:
    """Stub for test_bad_config_validation (port deferred)."""


@test.cases(
    test.case("not_running", running="no"),
    test.case("running_same", running="same"),
    test.case("running_different", running="different"),
)
async def reload_service(
    running: str,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Verify the reload service."""
    event = "test_event"
    event_flag = asyncio.Event()

    @callback
    def event_handler(event: Any) -> None:
        event_flag.set()

    hass.bus.async_listen_once(event, event_handler)
    hass.states.async_set("test.script", "off")

    expect(
        await async_setup_component(
            hass,
            "script",
            {
                "script": {
                    "test": {
                        "sequence": [
                            {"event": event},
                            {"wait_template": "{{ is_state('test.script', 'on') }}"},
                        ]
                    }
                }
            },
        )
    ).to_be_truthy()

    expect(hass.states.get(ENTITY_ID) is not None).to_be(True)
    expect(hass.services.has_service(script.DOMAIN, "test")).to_be(True)

    if running != "no":
        _, object_id = split_entity_id(ENTITY_ID)
        await hass.services.async_call(DOMAIN, object_id)
        await asyncio.wait_for(event_flag.wait(), 1)

        expect(script.is_on(hass, ENTITY_ID)).to_be(True)

    object_id = "test" if running == "same" else "test2"
    with patch(
        "homeassistant.config.load_yaml_config_file",
        return_value={
            "script": {object_id: {"sequence": [{"delay": {"seconds": 5}}]}}
        },
    ):
        await hass.services.async_call(DOMAIN, SERVICE_RELOAD, blocking=True)
        await hass.async_block_till_done()

    if running != "same":
        state = hass.states.get(ENTITY_ID)
        expect(state.attributes["restored"]).to_be(True)
        expect(hass.services.has_service(script.DOMAIN, "test")).to_be(False)

        expect(hass.states.get("script.test2") is not None).to_be(True)
        expect(hass.services.has_service(script.DOMAIN, "test2")).to_be(True)
    else:
        expect(hass.states.get(ENTITY_ID) is not None).to_be(True)
        expect(hass.services.has_service(script.DOMAIN, "test")).to_be(True)


@test
async def reload_unchanged_does_not_stop(
    hass: HomeAssistant = Depends(_trigger_executor),
    calls: list[ServiceCall] = Depends(calls),
) -> None:
    """Test that reloading stops any running actions as appropriate."""
    test_entity = "test.entity"

    config = {
        script.DOMAIN: {
            "test": {
                "sequence": [
                    {"event": "running"},
                    {"wait_template": "{{ is_state('test.entity', 'goodbye') }}"},
                    {"action": "test.script"},
                ],
            }
        }
    }
    expect(await async_setup_component(hass, script.DOMAIN, config)).to_be_truthy()

    expect(hass.states.get(ENTITY_ID) is not None).to_be(True)
    expect(hass.services.has_service(script.DOMAIN, "test")).to_be(True)

    running = asyncio.Event()

    @callback
    def running_cb(event: Any) -> None:
        running.set()

    hass.bus.async_listen_once("running", running_cb)
    hass.states.async_set(test_entity, "hello")

    _, object_id = split_entity_id(ENTITY_ID)
    await hass.services.async_call(DOMAIN, object_id)
    await running.wait()
    expect(len(calls)).to_equal(0)

    with patch(
        "homeassistant.config.load_yaml_config_file",
        autospec=True,
        return_value=config,
    ):
        await hass.services.async_call(script.DOMAIN, SERVICE_RELOAD, blocking=True)

    hass.states.async_set(test_entity, "goodbye")
    await hass.async_block_till_done()

    expect(len(calls)).to_equal(1)


@test.cases(
    test.case(
        "plain",
        script_config={"test": {"sequence": [{"action": "test.script"}]}},
    ),
    test.case(
        "templated",
        script_config={"test": {"sequence": [{"action": "{{ 'test.script' }}"}]}},
    ),
    test.case(
        "blueprint",
        script_config={
            "test": {
                "use_blueprint": {
                    "path": "test_service.yaml",
                    "input": {"service_to_call": "test.script"},
                }
            }
        },
    ),
    test.case(
        "blueprint_templated_input",
        script_config={
            "test": {
                "use_blueprint": {
                    "path": "test_service.yaml",
                    "input": {"service_to_call": "{{ 'test.script' }}"},
                }
            }
        },
    ),
)
async def reload_unchanged_script(
    script_config: dict[str, Any],
    hass: HomeAssistant = Depends(_trigger_executor),
    calls: list[ServiceCall] = Depends(calls),
) -> None:
    """Test an unmodified script is not reloaded."""
    with patch(
        "homeassistant.components.script.ScriptEntity", wraps=ScriptEntity
    ) as script_entity_init:
        config = {script.DOMAIN: [script_config]}
        expect(
            await async_setup_component(hass, script.DOMAIN, config)
        ).to_be_truthy()
        expect(hass.states.get(ENTITY_ID) is not None).to_be(True)
        expect(hass.services.has_service(script.DOMAIN, "test")).to_be(True)

        expect(script_entity_init.call_count).to_equal(1)
        script_entity_init.reset_mock()

        _, object_id = split_entity_id(ENTITY_ID)
        await hass.services.async_call(DOMAIN, object_id)
        await hass.async_block_till_done()
        expect(len(calls)).to_equal(1)

        with patch(
            "homeassistant.config.load_yaml_config_file",
            autospec=True,
            return_value=config,
        ):
            await hass.services.async_call(
                script.DOMAIN, SERVICE_RELOAD, blocking=True
            )

        expect(script_entity_init.call_count).to_equal(0)
        script_entity_init.reset_mock()

        _, object_id = split_entity_id(ENTITY_ID)
        await hass.services.async_call(DOMAIN, object_id)
        await hass.async_block_till_done()
        expect(len(calls)).to_equal(2)


@test
async def service_descriptions(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that service descriptions are loaded and reloaded correctly."""
    expect(
        await async_setup_component(
            hass,
            "script",
            {
                "script": {
                    "test": {
                        "description": "test description",
                        "sequence": [{"delay": {"seconds": 5}}],
                    }
                }
            },
        )
    ).to_be_truthy()

    descriptions = await async_get_all_descriptions(hass)

    expect(descriptions[DOMAIN]["test"]["name"]).to_equal("test")
    expect(descriptions[DOMAIN]["test"]["description"]).to_equal("test description")
    expect(bool(descriptions[DOMAIN]["test"]["fields"])).to_be(False)

    with patch(
        "homeassistant.config.load_yaml_config_file",
        return_value={
            "script": {
                "test": {
                    "fields": {
                        "test_param": {
                            "description": "test_param description",
                            "example": "test_param example",
                        }
                    },
                    "sequence": [{"delay": {"seconds": 5}}],
                }
            }
        },
    ):
        await hass.services.async_call(DOMAIN, SERVICE_RELOAD, blocking=True)

    descriptions = await async_get_all_descriptions(hass)

    expect(descriptions[script.DOMAIN]["test"]["description"]).to_equal("")
    expect(
        descriptions[script.DOMAIN]["test"]["fields"]["test_param"]["description"]
    ).to_equal("test_param description")
    expect(
        descriptions[script.DOMAIN]["test"]["fields"]["test_param"]["example"]
    ).to_equal("test_param example")

    with patch(
        "homeassistant.config.load_yaml_config_file",
        return_value={
            "script": {
                "test_name": {
                    "alias": "ABC",
                    "sequence": [{"delay": {"seconds": 5}}],
                }
            }
        },
    ):
        await hass.services.async_call(DOMAIN, SERVICE_RELOAD, blocking=True)

    descriptions = await async_get_all_descriptions(hass)

    expect(descriptions[DOMAIN]["test_name"]["name"]).to_equal("ABC")


@test
async def shared_context(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that the shared context is passed down the chain."""
    event = "test_event"
    context = Context()

    event_mock = Mock()
    run_mock = Mock()

    hass.bus.async_listen(event, event_mock)
    hass.bus.async_listen(EVENT_SCRIPT_STARTED, run_mock)

    expect(
        await async_setup_component(
            hass, "script", {"script": {"test": {"sequence": [{"event": event}]}}}
        )
    ).to_be_truthy()

    await hass.services.async_call(
        DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: ENTITY_ID}, context=context
    )
    await hass.async_block_till_done()

    expect(event_mock.call_count).to_equal(1)
    expect(run_mock.call_count).to_equal(1)

    args, _kwargs = run_mock.call_args
    expect(args[0].context).to_equal(context)
    expect(args[0].data.get(ATTR_NAME)).to_equal("test")
    expect(args[0].data.get(ATTR_ENTITY_ID)).to_equal("script.test")

    args, _kwargs = event_mock.call_args
    expect(args[0].context).to_equal(context)

    state = hass.states.get("script.test")
    expect(state is not None).to_be(True)
    expect(state.context).to_equal(context)


@test
async def logging_script_error(
    hass: HomeAssistant = Depends(_trigger_executor),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test logging script error."""
    expect(
        await async_setup_component(
            hass,
            "script",
            {"script": {"hello": {"sequence": [{"action": "non.existing"}]}}},
        )
    ).to_be_truthy()
    raised: ServiceNotFound | None = None
    try:
        await hass.services.async_call("script", "hello", blocking=True)
    except ServiceNotFound as exc:
        raised = exc
    expect(raised is not None).to_be(True)
    expect(raised.domain).to_equal("non")
    expect(raised.service).to_equal("existing")
    expect("Error executing script" in caplog.text).to_be(True)


@test
async def turning_no_scripts_off(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test it is possible to turn two scripts off."""
    expect(await async_setup_component(hass, "script", {})).to_be_truthy()

    await hass.services.async_call(
        DOMAIN, SERVICE_TURN_OFF, {"entity_id": []}, blocking=True
    )


@test
async def async_get_descriptions_script(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test async_set_service_schema for the script integration."""
    script_config = {
        DOMAIN: {
            "test1": {"sequence": [{"action": "homeassistant.restart"}]},
            "test2": {
                "description": "test2",
                "fields": {
                    "param": {
                        "description": "param_description",
                        "example": "param_example",
                    }
                },
                "sequence": [{"action": "homeassistant.restart"}],
            },
        }
    }

    await async_setup_component(hass, DOMAIN, script_config)
    descriptions = await async_get_all_descriptions(hass)

    expect(descriptions[DOMAIN]["test1"]["description"]).to_equal("")
    expect(bool(descriptions[DOMAIN]["test1"]["fields"])).to_be(False)

    expect(descriptions[DOMAIN]["test2"]["description"]).to_equal("test2")
    expect(
        descriptions[DOMAIN]["test2"]["fields"]["param"]["description"]
    ).to_equal("param_description")
    expect(descriptions[DOMAIN]["test2"]["fields"]["param"]["example"]).to_equal(
        "param_example"
    )


@test
async def extraction_functions_not_setup(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test extraction functions when script is not setup."""
    expect(script.scripts_with_area(hass, "area-in-both")).to_equal([])
    expect(script.areas_in_script(hass, "script.test")).to_equal([])
    expect(script.scripts_with_blueprint(hass, "blabla.yaml")).to_equal([])
    expect(script.blueprint_in_script(hass, "script.test")).to_be(None)
    expect(script.scripts_with_device(hass, "device-in-both")).to_equal([])
    expect(script.devices_in_script(hass, "script.test")).to_equal([])
    expect(script.scripts_with_entity(hass, "light.in_both")).to_equal([])
    expect(script.entities_in_script(hass, "script.test")).to_equal([])
    expect(script.scripts_with_floor(hass, "floor-in-both")).to_equal([])
    expect(script.floors_in_script(hass, "script.test")).to_equal([])
    expect(script.scripts_with_label(hass, "label-in-both")).to_equal([])
    expect(script.labels_in_script(hass, "script.test")).to_equal([])


@test
async def extraction_functions_unknown_script(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test extraction functions for an unknown script."""
    expect(await async_setup_component(hass, DOMAIN, {})).to_be_truthy()
    expect(script.labels_in_script(hass, "script.unknown")).to_equal([])
    expect(script.floors_in_script(hass, "script.unknown")).to_equal([])
    expect(script.areas_in_script(hass, "script.unknown")).to_equal([])
    expect(script.blueprint_in_script(hass, "script.unknown")).to_be(None)
    expect(script.devices_in_script(hass, "script.unknown")).to_equal([])
    expect(script.entities_in_script(hass, "script.unknown")).to_equal([])


@test
async def extraction_functions_unavailable_script(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test extraction functions for an unknown automation."""
    entity_id = "script.test1"
    expect(
        await async_setup_component(
            hass,
            DOMAIN,
            {DOMAIN: {"test1": {}}},
        )
    ).to_be_truthy()
    expect(hass.states.get(entity_id).state).to_equal(STATE_UNAVAILABLE)
    expect(script.scripts_with_area(hass, "area-in-both")).to_equal([])
    expect(script.areas_in_script(hass, entity_id)).to_equal([])
    expect(script.scripts_with_blueprint(hass, "blabla.yaml")).to_equal([])
    expect(script.blueprint_in_script(hass, entity_id)).to_be(None)
    expect(script.scripts_with_device(hass, "device-in-both")).to_equal([])
    expect(script.devices_in_script(hass, entity_id)).to_equal([])
    expect(script.scripts_with_entity(hass, "light.in_both")).to_equal([])
    expect(script.entities_in_script(hass, entity_id)).to_equal([])
    expect(script.scripts_with_floor(hass, "floor-in-both")).to_equal([])
    expect(script.floors_in_script(hass, entity_id)).to_equal([])
    expect(script.scripts_with_label(hass, "label-in-both")).to_equal([])
    expect(script.labels_in_script(hass, entity_id)).to_equal([])


@test
async def extraction_functions(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test extraction functions."""
    config_entry = MockConfigEntry(domain="fake_integration", data={})
    config_entry.mock_state(hass, ConfigEntryState.LOADED)
    config_entry.add_to_hass(hass)

    device_in_both = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "00:00:00:00:00:02")},
    )
    device_in_last = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "00:00:00:00:00:03")},
    )

    expect(
        await async_setup_component(
            hass,
            DOMAIN,
            {
                DOMAIN: {
                    "test1": {
                        "sequence": [
                            {
                                "action": "test.script",
                                "data": {"entity_id": "light.in_both"},
                            },
                            {
                                "action": "test.script",
                                "data": {"entity_id": "light.in_first"},
                            },
                            {
                                "entity_id": "light.device_in_both",
                                "domain": "light",
                                "type": "turn_on",
                                "device_id": device_in_both.id,
                            },
                            {
                                "action": "test.test",
                                "target": {"area_id": "area-in-both"},
                            },
                            {
                                "action": "test.test",
                                "target": {"floor_id": "floor-in-both"},
                            },
                            {
                                "action": "test.test",
                                "target": {"label_id": "label-in-both"},
                            },
                        ]
                    },
                    "test2": {
                        "sequence": [
                            {
                                "action": "test.script",
                                "data": {"entity_id": "light.in_both"},
                            },
                            {
                                "condition": "state",
                                "entity_id": "sensor.condition",
                                "state": "100",
                            },
                            {"scene": "scene.hello"},
                            {
                                "entity_id": "light.device_in_both",
                                "domain": "light",
                                "type": "turn_on",
                                "device_id": device_in_both.id,
                            },
                            {
                                "entity_id": "light.device_in_last",
                                "domain": "light",
                                "type": "turn_on",
                                "device_id": device_in_last.id,
                            },
                        ],
                    },
                    "test3": {
                        "sequence": [
                            {
                                "action": "test.script",
                                "data": {"entity_id": "light.in_both"},
                            },
                            {
                                "condition": "state",
                                "entity_id": "sensor.condition",
                                "state": "100",
                            },
                            {"scene": "scene.hello"},
                            {
                                "action": "test.test",
                                "target": {"area_id": "area-in-both"},
                            },
                            {
                                "action": "test.test",
                                "target": {"area_id": "area-in-last"},
                            },
                            {
                                "action": "test.test",
                                "target": {"floor_id": "floor-in-both"},
                            },
                            {
                                "action": "test.test",
                                "target": {"floor_id": "floor-in-last"},
                            },
                            {
                                "action": "test.test",
                                "target": {"label_id": "label-in-both"},
                            },
                            {
                                "action": "test.test",
                                "target": {"label_id": "label-in-last"},
                            },
                        ],
                    },
                }
            },
        )
    ).to_be_truthy()

    expect(set(script.scripts_with_entity(hass, "light.in_both"))).to_equal(
        {"script.test1", "script.test2", "script.test3"}
    )
    expect(set(script.entities_in_script(hass, "script.test1"))).to_equal(
        {"light.in_both", "light.in_first"}
    )
    expect(set(script.scripts_with_device(hass, device_in_both.id))).to_equal(
        {"script.test1", "script.test2"}
    )
    expect(set(script.devices_in_script(hass, "script.test2"))).to_equal(
        {device_in_both.id, device_in_last.id}
    )
    expect(set(script.scripts_with_area(hass, "area-in-both"))).to_equal(
        {"script.test1", "script.test3"}
    )
    expect(set(script.areas_in_script(hass, "script.test3"))).to_equal(
        {"area-in-both", "area-in-last"}
    )
    expect(set(script.scripts_with_floor(hass, "floor-in-both"))).to_equal(
        {"script.test1", "script.test3"}
    )
    expect(set(script.floors_in_script(hass, "script.test3"))).to_equal(
        {"floor-in-both", "floor-in-last"}
    )
    expect(set(script.scripts_with_label(hass, "label-in-both"))).to_equal(
        {"script.test1", "script.test3"}
    )
    expect(set(script.labels_in_script(hass, "script.test3"))).to_equal(
        {"label-in-both", "label-in-last"}
    )
    expect(script.blueprint_in_script(hass, "script.test3")).to_be(None)


@test
async def config_basic(
    hass: HomeAssistant = Depends(_trigger_executor),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test passing info in config."""
    expect(
        await async_setup_component(
            hass,
            "script",
            {
                "script": {
                    "test_script": {
                        "alias": "Script Name",
                        "icon": "mdi:party",
                        "sequence": [],
                    }
                }
            },
        )
    ).to_be_truthy()

    test_script = hass.states.get("script.test_script")
    expect(test_script.name).to_equal("Script Name")
    expect(test_script.attributes["icon"]).to_equal("mdi:party")

    entry = entity_registry.async_get("script.test_script")
    expect(entry is not None).to_be(True)
    expect(entry.unique_id).to_equal("test_script")


@test
async def config_multiple_domains(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test splitting configuration over multiple domains."""
    expect(
        await async_setup_component(
            hass,
            "script",
            {
                "script": {
                    "first_script": {
                        "alias": "Main domain",
                        "sequence": [],
                    }
                },
                "script second": {
                    "second_script": {
                        "alias": "Secondary domain",
                        "sequence": [],
                    }
                },
            },
        )
    ).to_be_truthy()

    test_script = hass.states.get("script.first_script")
    expect(test_script is not None).to_be(True)
    expect(test_script.name).to_equal("Main domain")

    test_script = hass.states.get("script.second_script")
    expect(test_script is not None).to_be(True)
    expect(test_script.name).to_equal("Secondary domain")


@test
async def logbook_humanify_script_started_event(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test humanifying script started event."""
    hass.config.components.add("recorder")
    await async_setup_component(hass, DOMAIN, {})
    await async_setup_component(hass, "logbook", {})
    await hass.async_block_till_done()

    event1, event2 = mock_humanify(
        hass,
        [
            MockRow(
                EVENT_SCRIPT_STARTED,
                {ATTR_ENTITY_ID: "script.hello", ATTR_NAME: "Hello Script"},
            ),
            MockRow(
                EVENT_SCRIPT_STARTED,
                {ATTR_ENTITY_ID: "script.bye", ATTR_NAME: "Bye Script"},
            ),
        ],
    )

    expect(event1["name"]).to_equal("Hello Script")
    expect(event1["domain"]).to_equal("script")
    expect(event1["message"]).to_equal("started")
    expect(event1["entity_id"]).to_equal("script.hello")

    expect(event2["name"]).to_equal("Bye Script")
    expect(event2["domain"]).to_equal("script")
    expect(event2["message"]).to_equal("started")
    expect(event2["entity_id"]).to_equal("script.bye")


@test.cases(
    test.case("sequential", concurrently=False),
    test.case("concurrent", concurrently=True),
)
async def concurrent_script(
    concurrently: bool,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test calling script concurrently or not."""
    if concurrently:
        call_script_2 = {
            "action": "script.turn_on",
            "data": {"entity_id": "script.script2"},
        }
    else:
        call_script_2 = {"action": "script.script2"}
    expect(
        await async_setup_component(
            hass,
            "script",
            {
                "script": {
                    "script1": {
                        "mode": "parallel",
                        "sequence": [
                            call_script_2,
                            {
                                "wait_template": (
                                    "{{ is_state('input_boolean.test1', 'on') }}"
                                )
                            },
                            {"action": "test.script", "data": {"value": "script1"}},
                        ],
                    },
                    "script2": {
                        "mode": "parallel",
                        "sequence": [
                            {"action": "test.script", "data": {"value": "script2a"}},
                            {
                                "wait_template": (
                                    "{{ is_state('input_boolean.test2', 'on') }}"
                                )
                            },
                            {"action": "test.script", "data": {"value": "script2b"}},
                        ],
                    },
                }
            },
        )
    ).to_be_truthy()

    service_called = asyncio.Event()
    service_values: list[Any] = []

    async def async_service_handler(service: ServiceCall) -> None:
        service_values.append(service.data.get("value"))
        service_called.set()

    hass.services.async_register("test", "script", async_service_handler)
    hass.states.async_set("input_boolean.test1", "off")
    hass.states.async_set("input_boolean.test2", "off")

    await hass.services.async_call("script", "script1")
    await asyncio.wait_for(service_called.wait(), 1)
    service_called.clear()

    expect(service_values[-1]).to_equal("script2a")
    expect(script.is_on(hass, "script.script1")).to_be(True)
    expect(script.is_on(hass, "script.script2")).to_be(True)

    if not concurrently:
        hass.states.async_set("input_boolean.test2", "on")
        await asyncio.wait_for(service_called.wait(), 1)
        service_called.clear()

        expect(service_values[-1]).to_equal("script2b")

    hass.states.async_set("input_boolean.test1", "on")
    await asyncio.wait_for(service_called.wait(), 1)
    service_called.clear()

    expect(service_values[-1]).to_equal("script1")
    expect(concurrently == script.is_on(hass, "script.script2")).to_be(True)

    if concurrently:
        hass.states.async_set("input_boolean.test2", "on")
        await asyncio.wait_for(service_called.wait(), 1)
        service_called.clear()

        expect(service_values[-1]).to_equal("script2b")

    await hass.async_block_till_done()

    expect(script.is_on(hass, "script.script1")).to_be(False)
    expect(script.is_on(hass, "script.script2")).to_be(False)


@test
async def script_variables(
    hass: HomeAssistant = Depends(_trigger_executor),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test defining scripts."""
    expect(
        await async_setup_component(
            hass,
            "script",
            {
                "script": {
                    "script1": {
                        "variables": {
                            "this_variable": "{{this.entity_id}}",
                            "test_var": "from_config",
                            "templated_config_var": (
                                "{{ var_from_service | default('config-default') }}"
                            ),
                        },
                        "sequence": [
                            {
                                "action": "test.script",
                                "data": {
                                    "value": "{{ test_var }}",
                                    "templated_config_var": (
                                        "{{ templated_config_var }}"
                                    ),
                                    "this_template": "{{this.entity_id}}",
                                    "this_variable": "{{this_variable}}",
                                },
                            },
                        ],
                    },
                    "script2": {
                        "variables": {
                            "test_var": "from_config",
                        },
                        "sequence": [
                            {
                                "action": "test.script",
                                "data": {
                                    "value": "{{ test_var }}",
                                },
                            },
                        ],
                    },
                    "script3": {
                        "variables": {
                            "test_var": "{{ break + 1 }}",
                        },
                        "sequence": [
                            {
                                "action": "test.script",
                                "data": {
                                    "value": "{{ test_var }}",
                                },
                            },
                        ],
                    },
                }
            },
        )
    ).to_be_truthy()

    mock_calls = async_mock_service(hass, "test", "script")

    await hass.services.async_call(
        "script", "script1", {"var_from_service": "hello"}, blocking=True
    )

    expect(len(mock_calls)).to_equal(1)
    expect(mock_calls[0].data["value"]).to_equal("from_config")
    expect(mock_calls[0].data["templated_config_var"]).to_equal("hello")
    expect(mock_calls[0].data.get("this_template")).to_equal("script.script1")
    expect(mock_calls[0].data.get("this_variable")).to_equal("script.script1")

    await hass.services.async_call(
        "script", "script1", {"test_var": "from_service"}, blocking=True
    )

    expect(len(mock_calls)).to_equal(2)
    expect(mock_calls[1].data["value"]).to_equal("from_service")
    expect(mock_calls[1].data["templated_config_var"]).to_equal("config-default")

    await hass.services.async_call(
        "script", "script2", {"test_var": "from_service"}, blocking=True
    )

    expect(len(mock_calls)).to_equal(3)
    expect(mock_calls[2].data["value"]).to_equal("from_service")

    expect("Error rendering variables" in caplog.text).to_be(False)
    template_err: TemplateError | None = None
    try:
        await hass.services.async_call("script", "script3", blocking=True)
    except TemplateError as exc:
        template_err = exc
    expect(template_err is not None).to_be(True)
    expect("Error rendering variables" in caplog.text).to_be(True)
    expect(len(mock_calls)).to_equal(3)

    await hass.services.async_call("script", "script3", {"break": 0}, blocking=True)

    expect(len(mock_calls)).to_equal(4)
    expect(mock_calls[3].data["value"]).to_equal(1)


@test
async def script_this_var_always(
    hass: HomeAssistant = Depends(_trigger_executor),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test script always has reference to this, even with no variables are configured."""
    expect(
        await async_setup_component(
            hass,
            "script",
            {
                "script": {
                    "script1": {
                        "sequence": [
                            {
                                "action": "test.script",
                                "data": {
                                    "this_template": "{{this.entity_id}}",
                                },
                            },
                        ],
                    },
                },
            },
        )
    ).to_be_truthy()
    mock_calls = async_mock_service(hass, "test", "script")

    await hass.services.async_call("script", "script1", blocking=True)

    expect(len(mock_calls)).to_equal(1)
    expect(mock_calls[0].data.get("this_template")).to_equal("script.script1")
    expect("Error rendering variables" in caplog.text).to_be(False)


@test
async def script_restore_last_triggered(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test if last triggered is restored on start."""
    time = dt_util.utcnow()
    mock_restore_cache(
        hass,
        (
            State("script.no_last_triggered", STATE_OFF),
            State(
                "script.last_triggered", STATE_OFF, {"last_triggered": time}
            ),
        ),
    )
    hass.set_state(CoreState.starting)

    expect(
        await async_setup_component(
            hass,
            "script",
            {
                "script": {
                    "no_last_triggered": {
                        "sequence": [{"delay": {"seconds": 5}}],
                    },
                    "last_triggered": {
                        "sequence": [{"delay": {"seconds": 5}}],
                    },
                },
            },
        )
    ).to_be_truthy()

    state = hass.states.get("script.no_last_triggered")
    expect(state is not None).to_be(True)
    expect(state.attributes["last_triggered"]).to_be(None)

    state = hass.states.get("script.last_triggered")
    expect(state is not None).to_be(True)
    expect(state.attributes["last_triggered"]).to_equal(time)


@test.cases(
    test.case(
        "parallel", script_mode=SCRIPT_MODE_PARALLEL,
        warning_msg="Maximum number of runs exceeded",
    ),
    test.case(
        "queued", script_mode=SCRIPT_MODE_QUEUED,
        warning_msg="Disallowed recursion detected",
    ),
    test.case(
        "restart", script_mode=SCRIPT_MODE_RESTART,
        warning_msg="Disallowed recursion detected",
    ),
    test.case(
        "single", script_mode=SCRIPT_MODE_SINGLE,
        warning_msg="Already running",
    ),
)
async def recursive_script(
    script_mode: str,
    warning_msg: str,
    hass: HomeAssistant = Depends(_trigger_executor),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test recursive script calls does not deadlock."""
    expect(
        [
            SCRIPT_MODE_PARALLEL,
            SCRIPT_MODE_QUEUED,
            SCRIPT_MODE_RESTART,
            SCRIPT_MODE_SINGLE,
        ]
    ).to_equal(SCRIPT_MODE_CHOICES)

    expect(
        await async_setup_component(
            hass,
            "script",
            {
                "script": {
                    "script1": {
                        "mode": script_mode,
                        "sequence": [
                            {"action": "script.script1"},
                            {"action": "test.script"},
                        ],
                    },
                }
            },
        )
    ).to_be_truthy()

    service_called = asyncio.Event()

    async def async_service_handler(service: ServiceCall) -> None:
        service_called.set()

    hass.services.async_register("test", "script", async_service_handler)

    await hass.services.async_call("script", "script1")
    await asyncio.wait_for(service_called.wait(), 1)

    expect(warning_msg in caplog.text).to_be(True)


@test.cases(
    test.case(
        "parallel", script_mode=SCRIPT_MODE_PARALLEL,
        warning_msg="Maximum number of runs exceeded",
    ),
    test.case(
        "queued", script_mode=SCRIPT_MODE_QUEUED,
        warning_msg="Disallowed recursion detected",
    ),
    test.case(
        "restart", script_mode=SCRIPT_MODE_RESTART,
        warning_msg="Disallowed recursion detected",
    ),
    test.case(
        "single", script_mode=SCRIPT_MODE_SINGLE,
        warning_msg="Already running",
    ),
)
async def recursive_script_indirect(
    script_mode: str,
    warning_msg: str,
    hass: HomeAssistant = Depends(_trigger_executor),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test recursive script calls does not deadlock."""
    expect(
        [
            SCRIPT_MODE_PARALLEL,
            SCRIPT_MODE_QUEUED,
            SCRIPT_MODE_RESTART,
            SCRIPT_MODE_SINGLE,
        ]
    ).to_equal(SCRIPT_MODE_CHOICES)

    expect(
        await async_setup_component(
            hass,
            "script",
            {
                "script": {
                    "script1": {
                        "mode": script_mode,
                        "sequence": [{"action": "script.script2"}],
                    },
                    "script2": {
                        "mode": script_mode,
                        "sequence": [{"action": "script.script3"}],
                    },
                    "script3": {
                        "mode": script_mode,
                        "sequence": [{"action": "script.script4"}],
                    },
                    "script4": {
                        "mode": script_mode,
                        "sequence": [
                            {"action": "script.script1"},
                            {"action": "test.script"},
                        ],
                    },
                }
            },
        )
    ).to_be_truthy()

    service_called = asyncio.Event()

    async def async_service_handler(service: ServiceCall) -> None:
        service_called.set()

    hass.services.async_register("test", "script", async_service_handler)

    await hass.services.async_call("script", "script1")
    await asyncio.wait_for(service_called.wait(), 1)

    expect(warning_msg in caplog.text).to_be(True)


@test.cases(
    test.case("parallel", script_mode=SCRIPT_MODE_PARALLEL),
    test.case("queued", script_mode=SCRIPT_MODE_QUEUED),
    test.case("restart", script_mode=SCRIPT_MODE_RESTART),
)
async def recursive_script_turn_on(
    script_mode: str,
    hass: HomeAssistant = Depends(_trigger_executor),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test script turning itself on.

    - Illegal recursion detection should not be triggered
    - Home Assistant should not hang on shut down
    - SCRIPT_MODE_SINGLE is not relevant because such a script can't turn itself on
    """
    expect(
        [
            SCRIPT_MODE_PARALLEL,
            SCRIPT_MODE_QUEUED,
            SCRIPT_MODE_RESTART,
            SCRIPT_MODE_SINGLE,
        ]
    ).to_equal(SCRIPT_MODE_CHOICES)
    stop_scripts_at_shutdown_called = asyncio.Event()
    real_stop_scripts_at_shutdown = _async_stop_scripts_at_shutdown

    async def stop_scripts_at_shutdown(*args: Any) -> None:
        await real_stop_scripts_at_shutdown(*args)
        stop_scripts_at_shutdown_called.set()

    with patch(
        "homeassistant.helpers.script._async_stop_scripts_at_shutdown",
        wraps=stop_scripts_at_shutdown,
    ):
        expect(
            await async_setup_component(
                hass,
                script.DOMAIN,
                {
                    script.DOMAIN: {
                        "script1": {
                            "mode": script_mode,
                            "sequence": [
                                {
                                    "choose": {
                                        "conditions": {
                                            "condition": "template",
                                            "value_template": (
                                                "{{ request == 'step_2' }}"
                                            ),
                                        },
                                        "sequence": {
                                            "action": "test.script_done"
                                        },
                                    },
                                    "default": {
                                        "action": "script.turn_on",
                                        "data": {
                                            "entity_id": "script.script1",
                                            "variables": {"request": "step_2"},
                                        },
                                    },
                                },
                                {
                                    "action": "script.turn_on",
                                    "data": {"entity_id": "script.script1"},
                                },
                            ],
                        }
                    }
                },
            )
        ).to_be_truthy()

        service_called = asyncio.Event()

        async def async_service_handler(service: ServiceCall) -> None:
            if service.service == "script_done":
                service_called.set()

        hass.services.async_register(
            "test", "script_done", async_service_handler
        )

        await hass.services.async_call("script", "script1")
        await asyncio.wait_for(service_called.wait(), 1)

        hass.set_state(CoreState.stopping)
        hass.bus.async_fire("homeassistant_stop")
        await asyncio.wait_for(stop_scripts_at_shutdown_called.wait(), 1)

        async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=90))
        await hass.async_block_till_done()

        expect("Disallowed recursion detected" not in caplog.text).to_be(True)


@test
async def setup_with_duplicate_scripts(
    hass: HomeAssistant = Depends(_trigger_executor),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test setup with duplicate configs."""
    expect(
        await async_setup_component(
            hass,
            "script",
            {
                "script one": {
                    "duplicate": {
                        "sequence": [],
                    },
                },
                "script two": {
                    "duplicate": {
                        "sequence": [],
                    },
                },
            },
        )
    ).to_be_truthy()
    expect("Duplicate script detected with name: 'duplicate'" in caplog.text).to_be(
        True
    )
    expect(len(hass.states.async_entity_ids("script"))).to_equal(1)


@test
async def websocket_config(
    hass: HomeAssistant = Depends(_trigger_executor),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test config command."""
    config = {
        "alias": "hello",
        "sequence": [{"action": "light.turn_on"}],
    }
    expect(
        await async_setup_component(
            hass,
            "script",
            {
                "script": {
                    "hello": config,
                },
            },
        )
    ).to_be_truthy()
    client = await hass_ws_client(hass)
    await client.send_json(
        {
            "id": 5,
            "type": "script/config",
            "entity_id": "script.hello",
        }
    )

    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    expect(msg["result"]).to_equal({"config": config})

    await client.send_json(
        {
            "id": 6,
            "type": "script/config",
            "entity_id": "script.not_exist",
        }
    )

    msg = await client.receive_json()
    expect(msg["success"]).to_be_falsy()
    expect(msg["error"]["code"]).to_equal("not_found")


@test
async def script_service_changed_entity_id(
    hass: HomeAssistant = Depends(_trigger_executor),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test the script service works for scripts with overridden entity_id."""
    entry = entity_registry.async_get_or_create("script", "script", "test")
    entry = entity_registry.async_update_entity(
        entry.entity_id, new_entity_id="script.custom_entity_id"
    )
    expect(entry.entity_id).to_equal("script.custom_entity_id")

    calls: list[ServiceCall] = []

    @callback
    def record_call(service: ServiceCall) -> None:
        """Add recorded event to set."""
        calls.append(service)

    hass.services.async_register("test", "script", record_call)

    expect(
        await async_setup_component(
            hass,
            "script",
            {
                "script": {
                    "test": {
                        "sequence": {
                            "action": "test.script",
                            "data_template": {"entity_id": "{{ this.entity_id }}"},
                        }
                    }
                }
            },
        )
    ).to_be_truthy()

    await hass.services.async_call(DOMAIN, "test", {"greeting": "world"})

    await hass.async_block_till_done()

    expect(len(calls)).to_equal(1)
    expect(calls[0].data["entity_id"]).to_equal("script.custom_entity_id")

    entry = entity_registry.async_update_entity(
        entry.entity_id, new_entity_id="script.custom_entity_id_2"
    )
    expect(entry.entity_id).to_equal("script.custom_entity_id_2")
    await hass.async_block_till_done()

    await hass.services.async_call(DOMAIN, "test", {"greeting": "world"})
    await hass.async_block_till_done()

    expect(len(calls)).to_equal(2)
    expect(calls[1].data["entity_id"]).to_equal("script.custom_entity_id_2")


@test
async def blueprint_script(
    hass: HomeAssistant = Depends(_trigger_executor),
    calls: list[ServiceCall] = Depends(calls),
) -> None:
    """Test blueprint script."""
    expect(
        await async_setup_component(
            hass,
            script.DOMAIN,
            {
                script.DOMAIN: {
                    "test_script": {
                        "use_blueprint": {
                            "path": "test_service.yaml",
                            "input": {
                                "service_to_call": "test.script",
                            },
                        }
                    }
                }
            },
        )
    ).to_be_truthy()
    await hass.services.async_call(
        "script", "test_script", {"var_from_service": "hello"}, blocking=True
    )
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(1)
    expect(script.blueprint_in_script(hass, "script.test_script")).to_equal(
        "test_service.yaml"
    )
    expect(script.scripts_with_blueprint(hass, "test_service.yaml")).to_equal(
        ["script.test_script"]
    )


@test.skip("pending tryke port - requires hass_ws_client + repairs helpers + parametrize")
async def blueprint_script_bad_config() -> None:
    """Stub for test_blueprint_script_bad_config (port deferred)."""


@test.skip("pending tryke port - requires hass_ws_client + repairs helpers")
async def blueprint_script_fails_substitution() -> None:
    """Stub for test_blueprint_script_fails_substitution (port deferred)."""


@test.cases(
    test.case("dict_response", response={"value": 5}),
    test.case("str_response", response='{"value": 5}'),
)
async def responses(
    response: Any,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test we can get responses."""
    mock_restore_cache(hass, ())
    expect(
        await async_setup_component(
            hass,
            "script",
            {
                "script": {
                    "test": {
                        "sequence": [
                            {
                                "variables": {"test_var": {"response": response}},
                            },
                            {
                                "stop": "done",
                                "response_variable": "test_var",
                            },
                        ]
                    }
                }
            },
        )
    ).to_be_truthy()

    result = await hass.services.async_call(
        DOMAIN, "test", {"greeting": "world"}, blocking=True, return_response=True
    )
    expect(result).to_equal({"response": response})
    expect(
        await hass.services.async_call(
            DOMAIN,
            "test",
            {"greeting": "world"},
            blocking=True,
            return_response=False,
        )
    ).to_be(None)


@test
async def responses_no_response(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test response variable not set."""
    mock_restore_cache(hass, ())
    expect(
        await async_setup_component(
            hass,
            "script",
            {
                "script": {
                    "test": {
                        "sequence": [
                            {
                                "stop": "done",
                                "response_variable": "test_var",
                            },
                        ]
                    }
                }
            },
        )
    ).to_be_truthy()

    expect(
        await hass.services.async_call(
            DOMAIN,
            "test",
            {"greeting": "world"},
            blocking=True,
            return_response=True,
        )
    ).to_equal({})
    expect(
        await hass.services.async_call(
            DOMAIN,
            "test",
            {"greeting": "world"},
            blocking=True,
            return_response=False,
        )
    ).to_be(None)


@test
async def script_queued_mode(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test calling a queued mode script called in parallel."""
    calls = 0

    async def async_service_handler(*args: Any, **kwargs: Any) -> None:
        """Service that simulates doing background I/O."""
        nonlocal calls
        calls += 1
        await asyncio.sleep(0)

    hass.services.async_register("test", "simulated_remote", async_service_handler)
    expect(
        await async_setup_component(
            hass,
            script.DOMAIN,
            {
                script.DOMAIN: {
                    "test_main": {
                        "sequence": [
                            {
                                "parallel": [
                                    {"action": "script.test_sub"},
                                    {"action": "script.test_sub"},
                                    {"action": "script.test_sub"},
                                    {"action": "script.test_sub"},
                                ]
                            }
                        ]
                    },
                    "test_sub": {
                        "mode": "queued",
                        "sequence": [
                            {"action": "test.simulated_remote"},
                        ],
                    },
                }
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()

    await hass.services.async_call("script", "test_main", blocking=True)
    expect(calls).to_equal(4)


@test.skip("pending tryke port - requires hass_ws_client + labs domain setup")
async def reload_when_labs_flag_changes() -> None:
    """Stub for test_reload_when_labs_flag_changes (port deferred)."""


@test
async def remove_script_entity_unloads_script(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that removing a script entity unloads its underlying script."""
    expect(
        await async_setup_component(
            hass,
            script.DOMAIN,
            {
                script.DOMAIN: {
                    "test_script": {
                        "sequence": [{"event": "test_event"}],
                    }
                }
            },
        )
    ).to_be_truthy()

    entity = hass.data[script.DOMAIN].get_entity("script.test_script")
    expect(entity is not None).to_be(True)
    expect(isinstance(entity, ScriptEntity)).to_be(True)

    with (
        patch(
            "homeassistant.config.load_yaml_config_file",
            autospec=True,
            return_value={script.DOMAIN: {}},
        ),
        patch.object(
            entity.script,
            "async_unload",
            wraps=entity.script.async_unload,
        ) as script_unload,
    ):
        await hass.services.async_call(
            script.DOMAIN, SERVICE_RELOAD, blocking=True
        )
        await hass.async_block_till_done()

    script_unload.assert_called_once()
