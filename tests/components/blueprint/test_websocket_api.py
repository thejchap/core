"""Test websocket API."""

from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import yaml
from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util.yaml import UndefinedSubstitution, parse_yaml

from tests.common import MockUser
from tests.hass_fixtures import (
    aioclient_mock as aioclient_mock_fixture,
    hass as hass_fixture,
    hass_admin_user as hass_admin_user_fixture,
    hass_ws_client as hass_ws_client_fixture,
    mock_network,
)
from tests.test_util.aiohttp import AiohttpClientMocker
from tests.typing import WebSocketGenerator


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


async def _setup_bp(
    hass: HomeAssistant,
    automation_config: dict[str, Any] | None = None,
    script_config: dict[str, Any] | None = None,
) -> None:
    """Set up the blueprint component and register automation/script blueprints."""
    assert await async_setup_component(hass, "blueprint", {})
    await async_setup_component(hass, "automation", automation_config or {})
    await async_setup_component(hass, "script", script_config or {})


@test
async def list_blueprints(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test listing blueprints."""
    await _setup_bp(hass)
    client = await hass_ws_client(hass)
    await client.send_json_auto_id({"type": "blueprint/list", "domain": "automation"})

    msg = await client.receive_json()

    expect(msg["success"]).to_be(True)
    blueprints = msg["result"]
    expect(blueprints).to_equal(
        {
            "test_event_service.yaml": {
                "metadata": {
                    "domain": "automation",
                    "input": {
                        "service_to_call": None,
                        "trigger_event": {
                            "selector": {
                                "text": {"multiline": False, "multiple": False}
                            }
                        },
                        "a_number": {
                            "selector": {"number": {"mode": "box", "step": 1.0}}
                        },
                    },
                    "name": "Call service based on event",
                },
            },
            "test_event_service_legacy_schema.yaml": {
                "metadata": {
                    "domain": "automation",
                    "input": {
                        "service_to_call": None,
                        "trigger_event": {
                            "selector": {
                                "text": {"multiline": False, "multiple": False}
                            }
                        },
                        "a_number": {
                            "selector": {"number": {"mode": "box", "step": 1.0}}
                        },
                    },
                    "name": "Call service based on event",
                },
            },
            "in_folder/in_folder_blueprint.yaml": {
                "metadata": {
                    "domain": "automation",
                    "input": {"action": None, "trigger": None},
                    "name": "In Folder Blueprint",
                }
            },
        }
    )


@test
async def list_blueprints_non_existing_domain(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test listing blueprints."""
    await _setup_bp(hass)
    client = await hass_ws_client(hass)
    await client.send_json_auto_id(
        {"type": "blueprint/list", "domain": "not_existing"}
    )

    msg = await client.receive_json()

    expect(msg["success"]).to_be(True)
    blueprints = msg["result"]
    expect(blueprints).to_equal({})


@test.cases(
    test.case(
        "list",
        message={"type": "blueprint/list", "domain": "automation"},
    ),
    test.case(
        "import",
        message={
            "type": "blueprint/import",
            "url": "https://example.com/blueprint.yaml",
        },
    ),
    test.case(
        "save",
        message={
            "type": "blueprint/save",
            "path": "test_save",
            "yaml": "raw_data",
            "domain": "automation",
        },
    ),
    test.case(
        "delete",
        message={
            "type": "blueprint/delete",
            "path": "test_delete",
            "domain": "automation",
        },
    ),
    test.case(
        "substitute",
        message={
            "type": "blueprint/substitute",
            "domain": "automation",
            "path": "test_event_service.yaml",
            "input": {
                "trigger_event": "test_event",
                "service_to_call": "test.automation",
                "a_number": 5,
            },
        },
    ),
)
async def blueprint_ws_command_requires_admin(
    message: dict[str, Any],
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    hass_admin_user: MockUser = Depends(hass_admin_user_fixture),
) -> None:
    """Test that blueprint websocket commands require admin."""
    await _setup_bp(hass)
    hass_admin_user.groups = []  # Remove admin privileges
    client = await hass_ws_client(hass)
    await client.send_json_auto_id(message)

    msg = await client.receive_json()

    expect(msg["success"]).to_be(False)
    expect(msg["error"]["code"]).to_equal("unauthorized")


@test
async def import_blueprint(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test importing blueprints."""
    await _setup_bp(hass)
    raw_data = Path(
        hass.config.path("blueprints/automation/test_event_service.yaml")
    ).read_text(encoding="utf8")

    aioclient_mock.get(
        "https://raw.githubusercontent.com/balloob/home-assistant-config/main/blueprints/automation/motion_light.yaml",
        text=raw_data,
    )

    client = await hass_ws_client(hass)
    await client.send_json_auto_id(
        {
            "type": "blueprint/import",
            "url": "https://github.com/balloob/home-assistant-config/blob/main/blueprints/automation/motion_light.yaml",
        }
    )

    msg = await client.receive_json()

    expect(msg["success"]).to_be(True)
    expect(msg["result"]).to_equal(
        {
            "suggested_filename": "balloob/motion_light",
            "raw_data": raw_data,
            "blueprint": {
                "metadata": {
                    "domain": "automation",
                    "input": {
                        "service_to_call": None,
                        "trigger_event": {
                            "selector": {
                                "text": {"multiline": False, "multiple": False}
                            }
                        },
                        "a_number": {
                            "selector": {"number": {"mode": "box", "step": 1.0}}
                        },
                    },
                    "name": "Call service based on event",
                    "source_url": "https://github.com/balloob/home-assistant-config/blob/main/blueprints/automation/motion_light.yaml",
                },
            },
            "validation_errors": None,
            "exists": False,
        }
    )


@test
async def import_blueprint_update(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test importing blueprints."""
    await _setup_bp(hass)
    raw_data = Path(
        hass.config.path("blueprints/automation/in_folder/in_folder_blueprint.yaml")
    ).read_text(encoding="utf8")

    aioclient_mock.get(
        "https://raw.githubusercontent.com/in_folder/home-assistant-config/main/blueprints/automation/in_folder_blueprint.yaml",
        text=raw_data,
    )

    client = await hass_ws_client(hass)
    await client.send_json_auto_id(
        {
            "type": "blueprint/import",
            "url": "https://github.com/in_folder/home-assistant-config/blob/main/blueprints/automation/in_folder_blueprint.yaml",
        }
    )

    msg = await client.receive_json()

    expect(msg["success"]).to_be(True)
    expect(msg["result"]).to_equal(
        {
            "suggested_filename": "in_folder/in_folder_blueprint",
            "raw_data": raw_data,
            "blueprint": {
                "metadata": {
                    "domain": "automation",
                    "input": {"action": None, "trigger": None},
                    "name": "In Folder Blueprint",
                    "source_url": "https://github.com/in_folder/home-assistant-config/blob/main/blueprints/automation/in_folder_blueprint.yaml",
                }
            },
            "validation_errors": None,
            "exists": True,
        }
    )


@test
async def save_blueprint(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test saving blueprints."""
    await _setup_bp(hass)
    raw_data = Path(
        hass.config.path("blueprints/automation/test_event_service.yaml")
    ).read_text(encoding="utf8")

    with patch("pathlib.Path.write_text") as write_mock:
        client = await hass_ws_client(hass)
        await client.send_json_auto_id(
            {
                "type": "blueprint/save",
                "path": "test_save",
                "yaml": raw_data,
                "domain": "automation",
                "source_url": "https://github.com/balloob/home-assistant-config/blob/main/blueprints/automation/motion_light.yaml",
            }
        )

        msg = await client.receive_json()

        expect(msg["success"]).to_be(True)
        expect(bool(write_mock.mock_calls)).to_be(True)
        # There are subtle differences in the dumper quoting
        # behavior when quoting is not required as both produce
        # valid yaml
        output_yaml = write_mock.call_args[0][0]
        expect(
            output_yaml
            in (
                # pure python dumper will quote the value after !input
                "blueprint:\n"
                "  name: Call service based on event\n"
                "  domain: automation\n"
                "  input:\n"
                "    trigger_event:\n"
                "      selector:\n"
                "        text:\n"
                "          multiline: false\n"
                "          multiple: false\n"
                "    service_to_call:\n"
                "    a_number:\n"
                "      selector:\n"
                "        number:\n"
                "          mode: box\n"
                "          step: 1.0\n"
                "  source_url: https://github.com/balloob/home-assistant-config/blob/main/blueprints/automation/motion_light.yaml\n"
                "triggers:\n"
                "  trigger: event\n"
                "  event_type: !input 'trigger_event'\n"
                "actions:\n"
                "  service: !input 'service_to_call'\n"
                "  entity_id: light.kitchen\n",
                # c dumper will not quote the value after !input
                "blueprint:\n"
                "  name: Call service based on event\n"
                "  domain: automation\n"
                "  input:\n"
                "    trigger_event:\n"
                "      selector:\n"
                "        text:\n"
                "          multiline: false\n"
                "          multiple: false\n"
                "    service_to_call:\n"
                "    a_number:\n"
                "      selector:\n"
                "        number:\n"
                "          mode: box\n"
                "          step: 1.0\n"
                "  source_url: https://github.com/balloob/home-assistant-config/blob/main/blueprints/automation/motion_light.yaml\n"
                "triggers:\n"
                "  trigger: event\n"
                "  event_type: !input trigger_event\n"
                "actions:\n"
                "  service: !input service_to_call\n"
                "  entity_id: light.kitchen\n",
            )
        ).to_be(True)
        # Make sure ita parsable and does not raise
        expect(len(parse_yaml(output_yaml)) > 1).to_be(True)


@test
async def save_existing_file(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test saving blueprints."""
    await _setup_bp(hass)
    client = await hass_ws_client(hass)
    await client.send_json_auto_id(
        {
            "type": "blueprint/save",
            "path": "test_event_service",
            "yaml": 'blueprint: {name: "name", domain: "automation"}',
            "domain": "automation",
            "source_url": "https://github.com/balloob/home-assistant-config/blob/main/blueprints/automation/motion_light.yaml",
        }
    )

    msg = await client.receive_json()

    expect(msg["success"]).to_be(False)
    expect(msg["error"]).to_equal(
        {"code": "already_exists", "message": "File already exists"}
    )


@test
async def save_existing_file_override(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test saving blueprints."""
    await _setup_bp(hass)
    client = await hass_ws_client(hass)
    with patch("pathlib.Path.write_text") as write_mock:
        await client.send_json_auto_id(
            {
                "type": "blueprint/save",
                "path": "test_event_service",
                "yaml": 'blueprint: {name: "name", domain: "automation"}',
                "domain": "automation",
                "source_url": "https://github.com/balloob/home-assistant-config/blob/main/blueprints/automation/test_event_service.yaml",
                "allow_override": True,
            }
        )

        msg = await client.receive_json()

    expect(msg["success"]).to_be(True)
    expect(msg["result"]).to_equal({"overrides_existing": True})
    expect(yaml.safe_load(write_mock.mock_calls[0][1][0])).to_equal(
        {
            "blueprint": {
                "name": "name",
                "domain": "automation",
                "source_url": "https://github.com/balloob/home-assistant-config/blob/main/blueprints/automation/test_event_service.yaml",
                "input": {},
            }
        }
    )


@test
async def save_file_error(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test saving blueprints with OS error."""
    await _setup_bp(hass)
    with patch("pathlib.Path.write_text", side_effect=OSError):
        client = await hass_ws_client(hass)
        await client.send_json_auto_id(
            {
                "type": "blueprint/save",
                "path": "test_save",
                "yaml": "raw_data",
                "domain": "automation",
                "source_url": "https://github.com/balloob/home-assistant-config/blob/main/blueprints/automation/motion_light.yaml",
            }
        )

        msg = await client.receive_json()

        expect(msg["success"]).to_be(False)


@test
async def save_invalid_blueprint(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test saving invalid blueprints."""
    await _setup_bp(hass)
    client = await hass_ws_client(hass)
    await client.send_json_auto_id(
        {
            "type": "blueprint/save",
            "path": "test_wrong",
            "yaml": "wrong_blueprint",
            "domain": "automation",
            "source_url": "https://github.com/balloob/home-assistant-config/blob/main/blueprints/automation/motion_light.yaml",
        }
    )

    msg = await client.receive_json()

    expect(msg["success"]).to_be(False)
    expect(msg["error"]).to_equal(
        {
            "code": "invalid_format",
            "message": "Invalid blueprint: expected a dictionary. Got 'wrong_blueprint'",
        }
    )


@test
async def delete_blueprint(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test deleting blueprints."""
    await _setup_bp(hass)
    with patch("pathlib.Path.unlink", return_value=Mock()) as unlink_mock:
        client = await hass_ws_client(hass)
        await client.send_json_auto_id(
            {
                "type": "blueprint/delete",
                "path": "test_delete",
                "domain": "automation",
            }
        )

        msg = await client.receive_json()

        expect(bool(unlink_mock.mock_calls)).to_be(True)
        expect(msg["success"]).to_be(True)


@test
async def delete_non_exist_file_blueprint(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test deleting non existing blueprints."""
    await _setup_bp(hass)
    client = await hass_ws_client(hass)
    await client.send_json_auto_id(
        {
            "type": "blueprint/delete",
            "path": "none_existing",
            "domain": "automation",
        }
    )

    msg = await client.receive_json()

    expect(msg["success"]).to_be(False)


@test
async def delete_blueprint_in_use_by_automation(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test deleting a blueprint which is in use."""
    await _setup_bp(
        hass,
        automation_config={
            "automation": {
                "use_blueprint": {
                    "path": "test_event_service.yaml",
                    "input": {
                        "trigger_event": "blueprint_event",
                        "service_to_call": "test.automation",
                        "a_number": 5,
                    },
                }
            }
        },
    )

    with patch("pathlib.Path.unlink", return_value=Mock()) as unlink_mock:
        client = await hass_ws_client(hass)
        await client.send_json_auto_id(
            {
                "type": "blueprint/delete",
                "path": "test_event_service.yaml",
                "domain": "automation",
            }
        )

        msg = await client.receive_json()

        expect(bool(unlink_mock.mock_calls)).to_be(False)
        expect(msg["success"]).to_be(False)
        expect(msg["error"]).to_equal(
            {
                "code": "home_assistant_error",
                "message": "Blueprint in use",
            }
        )


@test
async def delete_blueprint_in_use_by_script(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test deleting a blueprint which is in use."""
    await _setup_bp(
        hass,
        script_config={
            "script": {
                "test_script": {
                    "use_blueprint": {
                        "path": "test_service.yaml",
                        "input": {
                            "service_to_call": "test.automation",
                        },
                    }
                }
            }
        },
    )

    with patch("pathlib.Path.unlink", return_value=Mock()) as unlink_mock:
        client = await hass_ws_client(hass)
        await client.send_json(
            {
                "id": 9,
                "type": "blueprint/delete",
                "path": "test_service.yaml",
                "domain": "script",
            }
        )

        msg = await client.receive_json()

        expect(bool(unlink_mock.mock_calls)).to_be(False)
        expect(msg["success"]).to_be(False)
        expect(msg["error"]).to_equal(
            {
                "code": "home_assistant_error",
                "message": "Blueprint in use",
            }
        )


@test
async def substituting_blueprint_inputs(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test substituting blueprint inputs."""
    await _setup_bp(hass)
    client = await hass_ws_client(hass)
    await client.send_json_auto_id(
        {
            "type": "blueprint/substitute",
            "domain": "automation",
            "path": "test_event_service.yaml",
            "input": {
                "trigger_event": "test_event",
                "service_to_call": "test.automation",
                "a_number": 5,
            },
        }
    )

    msg = await client.receive_json()

    expect(msg["success"]).to_be(True)
    expect(msg["result"]["substituted_config"]).to_equal(
        {
            "actions": {
                "entity_id": "light.kitchen",
                "service": "test.automation",
            },
            "triggers": {
                "event_type": "test_event",
                "trigger": "event",
            },
        }
    )


@test
async def substituting_blueprint_inputs_unknown_domain(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test substituting blueprint inputs."""
    await _setup_bp(hass)
    client = await hass_ws_client(hass)
    await client.send_json_auto_id(
        {
            "type": "blueprint/substitute",
            "domain": "donald_duck",
            "path": "test_event_service.yaml",
            "input": {
                "trigger_event": "test_event",
                "service_to_call": "test.automation",
                "a_number": 5,
            },
        }
    )

    msg = await client.receive_json()

    expect(msg["success"]).to_be(False)
    expect(msg["error"]).to_equal(
        {
            "code": "invalid_format",
            "message": "Unsupported domain",
        }
    )


@test
async def substituting_blueprint_inputs_incomplete_input(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test substituting blueprint inputs."""
    await _setup_bp(hass)
    client = await hass_ws_client(hass)
    await client.send_json_auto_id(
        {
            "type": "blueprint/substitute",
            "domain": "automation",
            "path": "test_event_service.yaml",
            "input": {
                "service_to_call": "test.automation",
                "a_number": 5,
            },
        }
    )

    msg = await client.receive_json()

    expect(msg["success"]).to_be(False)
    expect(msg["error"]).to_equal(
        {
            "code": "unknown_error",
            "message": "Missing input trigger_event",
        }
    )


@test
async def substituting_blueprint_inputs_incomplete_input_2(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test substituting blueprint inputs."""
    await _setup_bp(hass)
    client = await hass_ws_client(hass)
    with patch(
        "homeassistant.components.blueprint.models.BlueprintInputs.async_substitute",
        side_effect=UndefinedSubstitution("blah"),
    ):
        await client.send_json_auto_id(
            {
                "type": "blueprint/substitute",
                "domain": "automation",
                "path": "test_event_service.yaml",
                "input": {
                    "trigger_event": "test_event",
                    "service_to_call": "test.automation",
                    "a_number": 5,
                },
            }
        )
        msg = await client.receive_json()

    expect(msg["success"]).to_be(False)
    expect(msg["error"]).to_equal(
        {
            "code": "unknown_error",
            "message": "No substitution found for input blah",
        }
    )
