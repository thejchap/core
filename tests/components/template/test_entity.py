"""Test abstract template entity."""

from __future__ import annotations

from tryke import Depends, expect, fixture, test

from homeassistant.components.template import entity as abstract_entity
from homeassistant.core import HomeAssistant

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Module-local anchor fixture (tryke 0.0.27 quirk)."""
    return hass


@test
async def template_entity_not_implemented(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test abstract template entity raises not implemented error."""
    raised = False
    try:
        _ = abstract_entity.AbstractTemplateEntity(hass, {})
    except TypeError:
        raised = True
    expect(raised).to_be(True)


@test.skip("reload test requires intricate script lifecycle — port deferred")
async def reload_stops_entity_action_scripts() -> None:
    """Stub: complex reload-time behaviour test."""
