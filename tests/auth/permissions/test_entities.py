"""Tests for entity permissions."""

import voluptuous as vol
from tryke import Depends, expect, fixture, test

from homeassistant.auth.permissions.entities import (
    ENTITY_POLICY_SCHEMA,
    compile_entities,
)
from homeassistant.auth.permissions.models import PermissionLookup
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntry

from tests.common import RegistryEntryWithDefaults, mock_device_registry, mock_registry
from tests.hass_fixtures import hass


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@test
def entities_none() -> None:
    """Test entity ID policy."""
    policy = None
    compiled = compile_entities(policy, None)
    expect(compiled("light.kitchen", "read")).to_be(False)


@test
def entities_empty() -> None:
    """Test entity ID policy."""
    policy = {}
    ENTITY_POLICY_SCHEMA(policy)
    compiled = compile_entities(policy, None)
    expect(compiled("light.kitchen", "read")).to_be(False)


@test
def entities_false() -> None:
    """Test entity ID policy."""
    policy = False
    expect(lambda: ENTITY_POLICY_SCHEMA(policy)).to_raise(vol.Invalid)


@test
def entities_true() -> None:
    """Test entity ID policy."""
    policy = True
    ENTITY_POLICY_SCHEMA(policy)
    compiled = compile_entities(policy, None)
    expect(compiled("light.kitchen", "read")).to_be(True)


@test
def entities_domains_true() -> None:
    """Test entity ID policy."""
    policy = {"domains": True}
    ENTITY_POLICY_SCHEMA(policy)
    compiled = compile_entities(policy, None)
    expect(compiled("light.kitchen", "read")).to_be(True)


@test
def entities_domains_domain_true() -> None:
    """Test entity ID policy."""
    policy = {"domains": {"light": True}}
    ENTITY_POLICY_SCHEMA(policy)
    compiled = compile_entities(policy, None)
    expect(compiled("light.kitchen", "read")).to_be(True)
    expect(compiled("switch.kitchen", "read")).to_be(False)


@test
def entities_domains_domain_false() -> None:
    """Test entity ID policy."""
    policy = {"domains": {"light": False}}
    expect(lambda: ENTITY_POLICY_SCHEMA(policy)).to_raise(vol.Invalid)


@test
def entities_entity_ids_true() -> None:
    """Test entity ID policy."""
    policy = {"entity_ids": True}
    ENTITY_POLICY_SCHEMA(policy)
    compiled = compile_entities(policy, None)
    expect(compiled("light.kitchen", "read")).to_be(True)


@test
def entities_entity_ids_false() -> None:
    """Test entity ID policy."""
    policy = {"entity_ids": False}
    expect(lambda: ENTITY_POLICY_SCHEMA(policy)).to_raise(vol.Invalid)


@test
def entities_entity_ids_entity_id_true() -> None:
    """Test entity ID policy."""
    policy = {"entity_ids": {"light.kitchen": True}}
    ENTITY_POLICY_SCHEMA(policy)
    compiled = compile_entities(policy, None)
    expect(compiled("light.kitchen", "read")).to_be(True)
    expect(compiled("switch.kitchen", "read")).to_be(False)


@test
def entities_entity_ids_entity_id_false() -> None:
    """Test entity ID policy."""
    policy = {"entity_ids": {"light.kitchen": False}}
    expect(lambda: ENTITY_POLICY_SCHEMA(policy)).to_raise(vol.Invalid)


@test
def entities_control_only() -> None:
    """Test policy granting control only."""
    policy = {"entity_ids": {"light.kitchen": {"read": True}}}
    ENTITY_POLICY_SCHEMA(policy)
    compiled = compile_entities(policy, None)
    expect(compiled("light.kitchen", "read")).to_be(True)
    expect(compiled("light.kitchen", "control")).to_be(False)
    expect(compiled("light.kitchen", "edit")).to_be(False)


@test
def entities_read_control() -> None:
    """Test policy granting control only."""
    policy = {"domains": {"light": {"read": True, "control": True}}}
    ENTITY_POLICY_SCHEMA(policy)
    compiled = compile_entities(policy, None)
    expect(compiled("light.kitchen", "read")).to_be(True)
    expect(compiled("light.kitchen", "control")).to_be(True)
    expect(compiled("light.kitchen", "edit")).to_be(False)


@test
def entities_all_allow() -> None:
    """Test policy allowing all entities."""
    policy = {"all": True}
    ENTITY_POLICY_SCHEMA(policy)
    compiled = compile_entities(policy, None)
    expect(compiled("light.kitchen", "read")).to_be(True)
    expect(compiled("light.kitchen", "control")).to_be(True)
    expect(compiled("switch.kitchen", "read")).to_be(True)


@test
def entities_all_read() -> None:
    """Test policy applying read to all entities."""
    policy = {"all": {"read": True}}
    ENTITY_POLICY_SCHEMA(policy)
    compiled = compile_entities(policy, None)
    expect(compiled("light.kitchen", "read")).to_be(True)
    expect(compiled("light.kitchen", "control")).to_be(False)
    expect(compiled("switch.kitchen", "read")).to_be(True)


@test
def entities_all_control() -> None:
    """Test entity ID policy applying control to all."""
    policy = {"all": {"control": True}}
    ENTITY_POLICY_SCHEMA(policy)
    compiled = compile_entities(policy, None)
    expect(compiled("light.kitchen", "read")).to_be(False)
    expect(compiled("light.kitchen", "control")).to_be(True)
    expect(compiled("switch.kitchen", "read")).to_be(False)
    expect(compiled("switch.kitchen", "control")).to_be(True)


@test
async def entities_device_id_boolean(hass: HomeAssistant = Depends(hass)) -> None:
    """Test entity ID policy applying control on device id."""
    entity_registry = mock_registry(
        hass,
        {
            "test_domain.allowed": RegistryEntryWithDefaults(
                entity_id="test_domain.allowed",
                unique_id="1234",
                platform="test_platform",
                device_id="mock-allowed-dev-id",
            ),
            "test_domain.not_allowed": RegistryEntryWithDefaults(
                entity_id="test_domain.not_allowed",
                unique_id="5678",
                platform="test_platform",
                device_id="mock-not-allowed-dev-id",
            ),
        },
    )
    device_registry = mock_device_registry(hass)

    policy = {"device_ids": {"mock-allowed-dev-id": {"read": True}}}
    ENTITY_POLICY_SCHEMA(policy)
    compiled = compile_entities(
        policy, PermissionLookup(entity_registry, device_registry)
    )
    expect(compiled("test_domain.allowed", "read")).to_be(True)
    expect(compiled("test_domain.allowed", "control")).to_be(False)
    expect(compiled("test_domain.not_allowed", "read")).to_be(False)
    expect(compiled("test_domain.not_allowed", "control")).to_be(False)


@test
def entities_areas_true() -> None:
    """Test entity ID policy for areas."""
    policy = {"area_ids": True}
    ENTITY_POLICY_SCHEMA(policy)
    compiled = compile_entities(policy, None)
    expect(compiled("light.kitchen", "read")).to_be(True)


@test
async def entities_areas_area_true(hass: HomeAssistant = Depends(hass)) -> None:
    """Test entity ID policy for areas with specific area."""
    entity_registry = mock_registry(
        hass,
        {
            "light.kitchen": RegistryEntryWithDefaults(
                entity_id="light.kitchen",
                unique_id="1234",
                platform="test_platform",
                device_id="mock-dev-id",
            )
        },
    )
    device_registry = mock_device_registry(
        hass, {"mock-dev-id": DeviceEntry(id="mock-dev-id", area_id="mock-area-id")}
    )

    policy = {"area_ids": {"mock-area-id": {"read": True, "control": True}}}
    ENTITY_POLICY_SCHEMA(policy)
    compiled = compile_entities(
        policy, PermissionLookup(entity_registry, device_registry)
    )
    expect(compiled("light.kitchen", "read")).to_be(True)
    expect(compiled("light.kitchen", "control")).to_be(True)
    expect(compiled("light.kitchen", "edit")).to_be(False)
    expect(compiled("switch.kitchen", "read")).to_be(False)
