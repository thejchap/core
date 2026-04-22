"""Test entity functions for Home Assistant templates."""

from __future__ import annotations

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

from tests.common import MockConfigEntry
from tests.hass_fixtures import device_registry, entity_registry, hass
from tests.helpers.template.helpers import render


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@test
async def entity_name(
    hass: HomeAssistant = Depends(hass),
    entity_registry: er.EntityRegistry = Depends(entity_registry),
    device_registry: dr.DeviceRegistry = Depends(device_registry),
) -> None:
    """Test entity_name method."""
    expect(render(hass, "{{ entity_name('sensor.fake') }}")).to_be(None)

    entry = entity_registry.async_get_or_create(
        "sensor", "test", "unique_1", original_name="Registry Sensor"
    )
    expect(render(hass, f"{{{{ entity_name('{entry.entity_id}') }}}}")).to_equal(
        "Registry Sensor"
    )
    expect(render(hass, f"{{{{ '{entry.entity_id}' | entity_name }}}}")).to_equal(
        "Registry Sensor"
    )

    entity_registry.async_update_entity(entry.entity_id, name="My Custom Sensor")
    expect(render(hass, f"{{{{ entity_name('{entry.entity_id}') }}}}")).to_equal(
        "My Custom Sensor"
    )

    # Falls back to state for entities not in the registry
    hass.states.async_set(
        "light.no_unique_id", "on", {"friendly_name": "No Unique ID Light"}
    )
    expect(render(hass, "{{ entity_name('light.no_unique_id') }}")).to_equal(
        "No Unique ID Light"
    )

    config_entry = MockConfigEntry(domain="test")
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
        name="My Device",
    )
    entry2 = entity_registry.async_get_or_create(
        "sensor",
        "test",
        "unique_2",
        config_entry=config_entry,
        device_id=device_entry.id,
        has_entity_name=True,
        original_name="Temperature",
    )
    expect(render(hass, f"{{{{ entity_name('{entry2.entity_id}') }}}}")).to_equal(
        "Temperature"
    )

    # Strips device name prefix
    entity_registry.async_update_entity(
        entry2.entity_id, name="My Device Custom Sensor"
    )
    expect(render(hass, f"{{{{ entity_name('{entry2.entity_id}') }}}}")).to_equal(
        "Custom Sensor"
    )


@test
async def is_hidden_entity(
    hass: HomeAssistant = Depends(hass),
    entity_registry: er.EntityRegistry = Depends(entity_registry),
) -> None:
    """Test is_hidden_entity method."""
    hidden_entity = entity_registry.async_get_or_create(
        "sensor", "mock", "hidden", hidden_by=er.RegistryEntryHider.USER
    )
    visible_entity = entity_registry.async_get_or_create("sensor", "mock", "visible")
    expect(
        bool(render(hass, f"{{{{ is_hidden_entity('{hidden_entity.entity_id}') }}}}"))
    ).to_be(True)

    expect(
        bool(render(hass, f"{{{{ is_hidden_entity('{visible_entity.entity_id}') }}}}"))
    ).to_be(False)

    expect(
        bool(
            render(
                hass,
                f"{{{{ ['{visible_entity.entity_id}'] | select('is_hidden_entity') | first }}}}",
            )
        )
    ).to_be(False)
