"""Test Automation config panel."""

from collections.abc import Generator
from http import HTTPStatus
import json
from typing import Any
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components import config
from homeassistant.components.config import automation
from homeassistant.const import STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component
from homeassistant.util import yaml as yaml_util

from ._fixtures import hass_read_only_access_token as hass_read_only_access_token_fx
from .conftest import mock_config_store

from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fx,
    entity_registry as entity_registry_fx,
    hass as hass_fixture,
    hass_client as hass_client_fx,
)
from tests.typing import ClientSessionGenerator


@fixture
def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Opt the module into Tryke's HookExecutor path."""
    return hass


@fixture
def hass_config_store() -> Generator[dict[str, Any]]:
    """Fixture to mock config yaml store."""
    with mock_config_store() as stored_data:
        yield stored_data


async def _setup_automation(
    hass: HomeAssistant, automation_config: Any
) -> None:
    """Set up automation integration."""
    assert await async_setup_component(
        hass, "automation", {"automation": automation_config}
    )


@test
async def get_automation_config(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    hass_config_store: dict[str, Any] = Depends(hass_config_store),
) -> None:
    """Test getting automation config."""
    await _setup_automation(hass, {})
    with patch.object(config, "SECTIONS", [automation]):
        await async_setup_component(hass, "config", {})

    client = await hass_client()

    hass_config_store["automations.yaml"] = [{"id": "sun"}, {"id": "moon"}]

    resp = await client.get("/api/config/automation/config/moon")

    expect(resp.status).to_equal(HTTPStatus.OK)
    result = await resp.json()

    expect(result).to_equal({"id": "moon"})


@test
async def update_automation_config(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    hass_config_store: dict[str, Any] = Depends(hass_config_store),
) -> None:
    """Test updating automation config."""
    await _setup_automation(hass, {})
    with patch.object(config, "SECTIONS", [automation]):
        await async_setup_component(hass, "config", {})

    expect(sorted(hass.states.async_entity_ids("automation"))).to_equal([])

    client = await hass_client()

    orig_data = [{"id": "sun"}, {"id": "moon"}]
    hass_config_store["automations.yaml"] = orig_data

    resp = await client.post(
        "/api/config/automation/config/moon",
        data=json.dumps({"triggers": [], "actions": [], "conditions": []}),
    )
    await hass.async_block_till_done()
    expect(sorted(hass.states.async_entity_ids("automation"))).to_equal(
        ["automation.automation_1"]
    )
    expect(hass.states.get("automation.automation_1").state).to_equal(STATE_ON)

    expect(resp.status).to_equal(HTTPStatus.OK)
    result = await resp.json()
    expect(result).to_equal({"result": "ok"})

    new_data = hass_config_store["automations.yaml"]
    expect(list(new_data[1])).to_equal(["id", "triggers", "conditions", "actions"])
    expect(new_data[1]).to_equal(
        {
            "id": "moon",
            "triggers": [],
            "conditions": [],
            "actions": [],
        }
    )


@test.cases(
    test.case(
        "missing_triggers",
        updated_config={"action": []},
        validation_error="required key not provided @ data['triggers']",
    ),
    test.case(
        "automation_trigger_unsupported",
        updated_config={
            "trigger": {"trigger": "automation"},
            "action": [],
        },
        validation_error="Integration 'automation' does not provide trigger support",
    ),
    test.case(
        "condition_unknown_entity",
        updated_config={
            "trigger": {"trigger": "event", "event_type": "test_event"},
            "condition": {
                "condition": "state",
                "entity_id": "abcdabcdabcdabcdabcdabcdabcdabcd",
                "state": "blah",
            },
            "action": [],
        },
        validation_error="Unknown entity registry entry abcdabcdabcdabcdabcdabcdabcdabcd",
    ),
    test.case(
        "action_unknown_entity",
        updated_config={
            "trigger": {"trigger": "event", "event_type": "test_event"},
            "action": {
                "condition": "state",
                "entity_id": "abcdabcdabcdabcdabcdabcdabcdabcd",
                "state": "blah",
            },
        },
        validation_error="Unknown entity registry entry abcdabcdabcdabcdabcdabcdabcdabcd",
    ),
    test.case(
        "blueprint_missing_inputs",
        updated_config={
            "use_blueprint": {"path": "test_event_service.yaml", "input": {}},
        },
        validation_error="Missing input a_number, service_to_call, trigger_event",
    ),
)
async def update_automation_config_with_error(
    updated_config: Any,
    validation_error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    hass_config_store: dict[str, Any] = Depends(hass_config_store),
    caplog: LogCapture = Depends(caplog_fx),
) -> None:
    """Test updating automation config with errors."""
    await _setup_automation(hass, {})
    with patch.object(config, "SECTIONS", [automation]):
        await async_setup_component(hass, "config", {})

    expect(sorted(hass.states.async_entity_ids("automation"))).to_equal([])

    client = await hass_client()

    orig_data = [{"id": "sun"}, {"id": "moon"}]
    hass_config_store["automations.yaml"] = orig_data

    resp = await client.post(
        "/api/config/automation/config/moon",
        data=json.dumps(updated_config),
    )
    await hass.async_block_till_done()
    expect(sorted(hass.states.async_entity_ids("automation"))).to_equal([])

    expect(resp.status != HTTPStatus.OK).to_be(True)
    result = await resp.json()
    expect(result).to_equal({"message": f"Message malformed: {validation_error}"})
    expect(validation_error not in caplog.text).to_be(True)


@test.cases(
    test.case(
        "blueprint_substitution_error",
        updated_config={
            "use_blueprint": {
                "path": "test_event_service.yaml",
                "input": {
                    "trigger_event": "test_event",
                    "service_to_call": "test.automation",
                    "a_number": 5,
                },
            },
        },
        validation_error="No substitution found for input blah",
    ),
)
async def update_automation_config_with_blueprint_substitution_error(
    updated_config: Any,
    validation_error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    hass_config_store: dict[str, Any] = Depends(hass_config_store),
    caplog: LogCapture = Depends(caplog_fx),
) -> None:
    """Test updating automation config with errors."""
    await _setup_automation(hass, {})
    with patch.object(config, "SECTIONS", [automation]):
        await async_setup_component(hass, "config", {})

    expect(sorted(hass.states.async_entity_ids("automation"))).to_equal([])

    client = await hass_client()

    orig_data = [{"id": "sun"}, {"id": "moon"}]
    hass_config_store["automations.yaml"] = orig_data

    with patch(
        "homeassistant.components.blueprint.models.BlueprintInputs.async_substitute",
        side_effect=yaml_util.UndefinedSubstitution("blah"),
    ):
        resp = await client.post(
            "/api/config/automation/config/moon",
            data=json.dumps(updated_config),
        )
        await hass.async_block_till_done()
    expect(sorted(hass.states.async_entity_ids("automation"))).to_equal([])

    expect(resp.status != HTTPStatus.OK).to_be(True)
    result = await resp.json()
    expect(result).to_equal({"message": f"Message malformed: {validation_error}"})
    expect(validation_error not in caplog.text).to_be(True)


@test
async def update_remove_key_automation_config(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    hass_config_store: dict[str, Any] = Depends(hass_config_store),
) -> None:
    """Test updating automation config while removing a key."""
    await _setup_automation(hass, {})
    with patch.object(config, "SECTIONS", [automation]):
        await async_setup_component(hass, "config", {})

    expect(sorted(hass.states.async_entity_ids("automation"))).to_equal([])

    client = await hass_client()

    orig_data = [{"id": "sun", "key": "value"}, {"id": "moon", "key": "value"}]
    hass_config_store["automations.yaml"] = orig_data

    resp = await client.post(
        "/api/config/automation/config/moon",
        data=json.dumps({"triggers": [], "actions": [], "conditions": []}),
    )
    await hass.async_block_till_done()
    expect(sorted(hass.states.async_entity_ids("automation"))).to_equal(
        ["automation.automation_1"]
    )
    expect(hass.states.get("automation.automation_1").state).to_equal(STATE_ON)

    expect(resp.status).to_equal(HTTPStatus.OK)
    result = await resp.json()
    expect(result).to_equal({"result": "ok"})

    new_data = hass_config_store["automations.yaml"]
    expect(list(new_data[1])).to_equal(["id", "triggers", "conditions", "actions"])
    expect(new_data[1]).to_equal(
        {
            "id": "moon",
            "triggers": [],
            "conditions": [],
            "actions": [],
        }
    )


@test
async def bad_formatted_automations(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    hass_config_store: dict[str, Any] = Depends(hass_config_store),
) -> None:
    """Test that we handle automations without ID."""
    await _setup_automation(hass, {})
    with patch.object(config, "SECTIONS", [automation]):
        await async_setup_component(hass, "config", {})

    expect(sorted(hass.states.async_entity_ids("automation"))).to_equal([])

    client = await hass_client()

    orig_data = [
        {
            # No ID
            "action": {"event": "hello"}
        },
        {"id": "moon"},
    ]
    hass_config_store["automations.yaml"] = orig_data

    resp = await client.post(
        "/api/config/automation/config/moon",
        data=json.dumps({"triggers": [], "actions": [], "conditions": []}),
    )
    await hass.async_block_till_done()
    expect(sorted(hass.states.async_entity_ids("automation"))).to_equal(
        ["automation.automation_1"]
    )
    expect(hass.states.get("automation.automation_1").state).to_equal(STATE_ON)

    expect(resp.status).to_equal(HTTPStatus.OK)
    result = await resp.json()
    expect(result).to_equal({"result": "ok"})

    new_data = hass_config_store["automations.yaml"]
    expect("id" in new_data[0]).to_be(True)
    expect(new_data[1]).to_equal(
        {
            "id": "moon",
            "triggers": [],
            "conditions": [],
            "actions": [],
        }
    )


@test
async def delete_automation(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    hass_config_store: dict[str, Any] = Depends(hass_config_store),
) -> None:
    """Test deleting an automation."""
    await _setup_automation(
        hass,
        [
            {
                "id": "sun",
                "trigger": {"trigger": "event", "event_type": "test_event"},
                "action": {"service": "test.automation"},
            },
            {
                "id": "moon",
                "trigger": {"trigger": "event", "event_type": "test_event"},
                "action": {"service": "test.automation"},
            },
        ],
    )

    expect(len(entity_registry.entities)).to_equal(2)

    with patch.object(config, "SECTIONS", [automation]):
        expect(await async_setup_component(hass, "config", {})).to_be(True)

    expect(sorted(hass.states.async_entity_ids("automation"))).to_equal(
        ["automation.automation_0", "automation.automation_1"]
    )

    client = await hass_client()

    orig_data = [{"id": "sun"}, {"id": "moon"}]
    hass_config_store["automations.yaml"] = orig_data

    resp = await client.delete("/api/config/automation/config/sun")
    await hass.async_block_till_done()

    expect(sorted(hass.states.async_entity_ids("automation"))).to_equal(
        ["automation.automation_1"]
    )

    expect(resp.status).to_equal(HTTPStatus.OK)
    result = await resp.json()
    expect(result).to_equal({"result": "ok"})

    expect(hass_config_store["automations.yaml"]).to_equal([{"id": "moon"}])

    expect(len(entity_registry.entities)).to_equal(1)


@test
async def api_calls_require_admin(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    hass_read_only_access_token: str = Depends(hass_read_only_access_token_fx),
    hass_config_store: dict[str, Any] = Depends(hass_config_store),
) -> None:
    """Test cloud APIs endpoints do not work as a normal user."""
    await _setup_automation(hass, {})
    with patch.object(config, "SECTIONS", [automation]):
        await async_setup_component(hass, "config", {})

    hass_config_store["automations.yaml"] = [{"id": "sun"}, {"id": "moon"}]

    client = await hass_client(hass_read_only_access_token)

    # Get
    resp = await client.get("/api/config/automation/config/moon")
    expect(resp.status).to_equal(HTTPStatus.UNAUTHORIZED)

    # Update
    resp = await client.post(
        "/api/config/automation/config/moon",
        data=json.dumps({"trigger": [], "action": [], "condition": []}),
    )
    expect(resp.status).to_equal(HTTPStatus.UNAUTHORIZED)

    # Delete
    resp = await client.delete("/api/config/automation/config/sun")
    expect(resp.status).to_equal(HTTPStatus.UNAUTHORIZED)
