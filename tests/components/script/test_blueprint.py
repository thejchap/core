"""Test script blueprints."""

import asyncio
from collections.abc import Iterator
import contextlib
import pathlib
from unittest.mock import patch

import pytest
from tryke import Depends, expect, fixture, test

from homeassistant.components import script
from homeassistant.components.blueprint import (
    BLUEPRINT_SCHEMA,
    Blueprint,
    DomainBlueprints,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import Context, HomeAssistant, callback
from homeassistant.helpers import device_registry as dr, template
from homeassistant.setup import async_setup_component
from homeassistant.util import yaml as yaml_util

from tests.common import MockConfigEntry, async_mock_service
from tests.hass_fixtures import device_registry as device_registry_fixture
from tests.hass_fixtures import hass as hass_fixture

BUILTIN_BLUEPRINT_FOLDER = pathlib.Path(script.__file__).parent / "blueprints"


@fixture
def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Anchor fixture for the module."""
    return hass


@contextlib.contextmanager
def patch_blueprint(blueprint_path: str, data_path: str) -> Iterator[None]:
    """Patch blueprint loading from a different source."""
    orig_load = DomainBlueprints._load_blueprint

    @callback
    def mock_load_blueprint(self, path: str) -> Blueprint:
        if path != blueprint_path:
            pytest.fail(f"Unexpected blueprint {path}")
            return orig_load(self, path)

        return Blueprint(
            yaml_util.load_yaml(data_path),
            expected_domain=self.domain,
            path=path,
            schema=BLUEPRINT_SCHEMA,
        )

    with patch(
        "homeassistant.components.blueprint.models.DomainBlueprints._load_blueprint",
        mock_load_blueprint,
    ):
        yield


@test
async def confirmable_notification(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test confirmable notification blueprint."""
    config_entry = MockConfigEntry(domain="fake_integration", data={})
    config_entry.mock_state(hass, ConfigEntryState.LOADED)
    config_entry.add_to_hass(hass)

    frodo = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "00:00:00:00:00:01")},
    )

    with patch_blueprint(
        "confirmable_notification.yaml",
        BUILTIN_BLUEPRINT_FOLDER / "confirmable_notification.yaml",
    ):
        expect(
            await async_setup_component(
                hass,
                script.DOMAIN,
                {
                    "script": {
                        "confirm": {
                            "use_blueprint": {
                                "path": "confirmable_notification.yaml",
                                "input": {
                                    "notify_device": frodo.id,
                                    "title": "Lord of the things",
                                    "message": "Throw ring in mountain?",
                                    "confirm_action": [
                                        {
                                            "action": "homeassistant.turn_on",
                                            "target": {"entity_id": "mount.doom"},
                                        }
                                    ],
                                },
                            }
                        }
                    }
                },
            )
        ).to_be_truthy()

    turn_on_calls = async_mock_service(hass, "homeassistant", "turn_on")
    context = Context()

    with patch(
        "homeassistant.components.mobile_app.device_action.async_call_action_from_config"
    ) as mock_call_action:
        # Trigger script
        await hass.services.async_call(script.DOMAIN, "confirm", context=context)

        # Give script the time to attach the trigger.
        await asyncio.sleep(0.1)

    hass.bus.async_fire("mobile_app_notification_action", {"action": "ANYTHING_ELSE"})
    hass.bus.async_fire(
        "mobile_app_notification_action", {"action": "CONFIRM_" + Context().id}
    )
    hass.bus.async_fire(
        "mobile_app_notification_action", {"action": "CONFIRM_" + context.id}
    )
    await hass.async_block_till_done()

    expect(len(mock_call_action.mock_calls)).to_equal(1)
    _hass, config, variables, _context = mock_call_action.mock_calls[0][1]

    rendered_config = template.render_complex(config, variables)

    expect(rendered_config).to_equal(
        {
            "title": "Lord of the things",
            "message": "Throw ring in mountain?",
            "alias": "Send notification",
            "domain": "mobile_app",
            "type": "notify",
            "device_id": frodo.id,
            "data": {
                "actions": [
                    {"action": "CONFIRM_" + _context.id, "title": "Confirm"},
                    {"action": "DISMISS_" + _context.id, "title": "Dismiss"},
                ]
            },
        }
    )

    expect(len(turn_on_calls)).to_equal(1)
    expect(turn_on_calls[0].data).to_equal(
        {
            "entity_id": ["mount.doom"],
        }
    )
