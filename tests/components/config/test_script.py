"""Test Script config panel."""

from collections.abc import Generator
from http import HTTPStatus
import json
from typing import Any
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components import config
from homeassistant.components.config import script
from homeassistant.const import STATE_OFF, STATE_UNAVAILABLE
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


async def _setup_script(hass: HomeAssistant, script_config: Any) -> None:
    """Set up script integration."""
    assert await async_setup_component(hass, "script", {"script": script_config})


@test
async def get_script_config(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    hass_config_store: dict[str, Any] = Depends(hass_config_store),
) -> None:
    """Test getting script config."""
    await _setup_script(hass, {})
    with patch.object(config, "SECTIONS", [script]):
        await async_setup_component(hass, "config", {})

    client = await hass_client()

    hass_config_store["scripts.yaml"] = {
        "sun": {"alias": "Sun"},
        "moon": {"alias": "Moon"},
    }

    resp = await client.get("/api/config/script/config/moon")

    expect(resp.status).to_equal(HTTPStatus.OK)
    result = await resp.json()

    expect(result).to_equal({"alias": "Moon"})


@test
async def update_script_config(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    hass_config_store: dict[str, Any] = Depends(hass_config_store),
) -> None:
    """Test updating script config."""
    await _setup_script(hass, {})
    with patch.object(config, "SECTIONS", [script]):
        await async_setup_component(hass, "config", {})

    expect(sorted(hass.states.async_entity_ids("script"))).to_equal([])

    client = await hass_client()

    orig_data = {"sun": {"alias": "Sun"}, "moon": {"alias": "Moon"}}
    hass_config_store["scripts.yaml"] = orig_data

    resp = await client.post(
        "/api/config/script/config/moon",
        data=json.dumps({"alias": "Moon updated", "sequence": []}),
    )
    await hass.async_block_till_done()
    expect(sorted(hass.states.async_entity_ids("script"))).to_equal(
        ["script.moon", "script.sun"]
    )
    expect(hass.states.get("script.moon").state).to_equal(STATE_OFF)
    expect(hass.states.get("script.sun").state).to_equal(STATE_UNAVAILABLE)

    expect(resp.status).to_equal(HTTPStatus.OK)
    result = await resp.json()
    expect(result).to_equal({"result": "ok"})

    new_data = hass_config_store["scripts.yaml"]
    expect(list(new_data["moon"])).to_equal(["alias", "sequence"])
    expect(new_data["moon"]).to_equal({"alias": "Moon updated", "sequence": []})


@test
async def invalid_object_id(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    hass_config_store: dict[str, Any] = Depends(hass_config_store),
) -> None:
    """Test creating a script with an invalid object_id."""
    await _setup_script(hass, {})
    with patch.object(config, "SECTIONS", [script]):
        await async_setup_component(hass, "config", {})

    expect(sorted(hass.states.async_entity_ids("script"))).to_equal([])

    client = await hass_client()

    hass_config_store["scripts.yaml"] = {}

    resp = await client.post(
        "/api/config/script/config/turn_on",
        data=json.dumps({"alias": "Turn on", "sequence": []}),
    )
    await hass.async_block_till_done()
    expect(sorted(hass.states.async_entity_ids("script"))).to_equal([])

    expect(resp.status).to_equal(HTTPStatus.BAD_REQUEST)
    result = await resp.json()
    expect(result).to_equal(
        {
            "message": (
                "Message malformed: A script's object_id must not be one of "
                "reload, toggle, turn_off, turn_on"
            )
        }
    )

    new_data = hass_config_store["scripts.yaml"]
    expect(new_data).to_equal({})


@test.cases(
    test.case(
        "missing_sequence",
        updated_config={},
        validation_error="required key not provided @ data['sequence']",
    ),
    test.case(
        "condition_unknown_entity",
        updated_config={
            "sequence": {
                "condition": "state",
                "entity_id": "abcdabcdabcdabcdabcdabcdabcdabcd",
                "state": "blah",
            }
        },
        validation_error="Unknown entity registry entry abcdabcdabcdabcdabcdabcdabcdabcd",
    ),
    test.case(
        "blueprint_missing_input",
        updated_config={
            "use_blueprint": {
                "path": "test_service.yaml",
                "input": {},
            },
        },
        validation_error="Missing input service_to_call",
    ),
)
async def update_script_config_with_error(
    updated_config: Any,
    validation_error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    hass_config_store: dict[str, Any] = Depends(hass_config_store),
    caplog: LogCapture = Depends(caplog_fx),
) -> None:
    """Test updating script config with errors."""
    await _setup_script(hass, {})
    with patch.object(config, "SECTIONS", [script]):
        await async_setup_component(hass, "config", {})

    expect(sorted(hass.states.async_entity_ids("script"))).to_equal([])

    client = await hass_client()

    orig_data = {"sun": {}, "moon": {}}
    hass_config_store["scripts.yaml"] = orig_data

    resp = await client.post(
        "/api/config/script/config/moon",
        data=json.dumps(updated_config),
    )
    await hass.async_block_till_done()
    expect(sorted(hass.states.async_entity_ids("script"))).to_equal([])

    expect(resp.status != HTTPStatus.OK).to_be(True)
    result = await resp.json()
    expect(result).to_equal({"message": f"Message malformed: {validation_error}"})
    expect(validation_error not in caplog.text).to_be(True)


@test.cases(
    test.case(
        "blueprint_substitution_error",
        updated_config={
            "use_blueprint": {
                "path": "test_service.yaml",
                "input": {
                    "service_to_call": "test.automation",
                },
            },
        },
        validation_error="No substitution found for input blah",
    ),
)
async def update_script_config_with_blueprint_substitution_error(
    updated_config: Any,
    validation_error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    hass_config_store: dict[str, Any] = Depends(hass_config_store),
    caplog: LogCapture = Depends(caplog_fx),
) -> None:
    """Test updating script config with errors."""
    await _setup_script(hass, {})
    with patch.object(config, "SECTIONS", [script]):
        await async_setup_component(hass, "config", {})

    expect(sorted(hass.states.async_entity_ids("script"))).to_equal([])

    client = await hass_client()

    orig_data = {"sun": {}, "moon": {}}
    hass_config_store["scripts.yaml"] = orig_data

    with patch(
        "homeassistant.components.blueprint.models.BlueprintInputs.async_substitute",
        side_effect=yaml_util.UndefinedSubstitution("blah"),
    ):
        resp = await client.post(
            "/api/config/script/config/moon",
            data=json.dumps(updated_config),
        )
        await hass.async_block_till_done()
    expect(sorted(hass.states.async_entity_ids("script"))).to_equal([])

    expect(resp.status != HTTPStatus.OK).to_be(True)
    result = await resp.json()
    expect(result).to_equal({"message": f"Message malformed: {validation_error}"})
    expect(validation_error not in caplog.text).to_be(True)


@test
async def update_remove_key_script_config(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    hass_config_store: dict[str, Any] = Depends(hass_config_store),
) -> None:
    """Test updating script config while removing a key."""
    await _setup_script(hass, {})
    with patch.object(config, "SECTIONS", [script]):
        await async_setup_component(hass, "config", {})

    expect(sorted(hass.states.async_entity_ids("script"))).to_equal([])

    client = await hass_client()

    orig_data = {"sun": {"key": "value"}, "moon": {"key": "value"}}
    hass_config_store["scripts.yaml"] = orig_data

    resp = await client.post(
        "/api/config/script/config/moon",
        data=json.dumps({"sequence": []}),
    )
    await hass.async_block_till_done()
    expect(sorted(hass.states.async_entity_ids("script"))).to_equal(
        ["script.moon", "script.sun"]
    )
    expect(hass.states.get("script.moon").state).to_equal(STATE_OFF)
    expect(hass.states.get("script.sun").state).to_equal(STATE_UNAVAILABLE)

    expect(resp.status).to_equal(HTTPStatus.OK)
    result = await resp.json()
    expect(result).to_equal({"result": "ok"})

    new_data = hass_config_store["scripts.yaml"]
    expect(list(new_data["moon"])).to_equal(["sequence"])
    expect(new_data["moon"]).to_equal({"sequence": []})


@test
async def delete_script(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    hass_config_store: dict[str, Any] = Depends(hass_config_store),
) -> None:
    """Test deleting a script."""
    await _setup_script(
        hass,
        {
            "one": {"alias": "Light on", "sequence": []},
            "two": {"alias": "Light off", "sequence": []},
        },
    )
    with patch.object(config, "SECTIONS", [script]):
        await async_setup_component(hass, "config", {})

    expect(sorted(hass.states.async_entity_ids("script"))).to_equal(
        ["script.one", "script.two"]
    )

    expect(len(entity_registry.entities)).to_equal(2)

    client = await hass_client()

    orig_data = {"one": {}, "two": {}}
    hass_config_store["scripts.yaml"] = orig_data

    resp = await client.delete("/api/config/script/config/two")
    await hass.async_block_till_done()

    expect(sorted(hass.states.async_entity_ids("script"))).to_equal(["script.one"])

    expect(resp.status).to_equal(HTTPStatus.OK)
    result = await resp.json()
    expect(result).to_equal({"result": "ok"})

    expect(hass_config_store["scripts.yaml"]).to_equal({"one": {}})

    expect(len(entity_registry.entities)).to_equal(1)


@test
async def api_calls_require_admin(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    hass_read_only_access_token: str = Depends(hass_read_only_access_token_fx),
    hass_config_store: dict[str, Any] = Depends(hass_config_store),
) -> None:
    """Test script APIs endpoints do not work as a normal user."""
    await _setup_script(hass, {})
    with patch.object(config, "SECTIONS", [script]):
        await async_setup_component(hass, "config", {})

    hass_config_store["scripts.yaml"] = {
        "moon": {"alias": "Moon"},
    }

    client = await hass_client(hass_read_only_access_token)

    # Get
    resp = await client.get("/api/config/script/config/moon")
    expect(resp.status).to_equal(HTTPStatus.UNAUTHORIZED)

    # Update
    resp = await client.post(
        "/api/config/script/config/moon",
        data=json.dumps({"sequence": []}),
    )
    expect(resp.status).to_equal(HTTPStatus.UNAUTHORIZED)

    # Delete
    resp = await client.delete("/api/config/script/config/moon")
    expect(resp.status).to_equal(HTTPStatus.UNAUTHORIZED)
