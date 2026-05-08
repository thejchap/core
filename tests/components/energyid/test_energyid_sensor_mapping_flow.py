"""Test EnergyID sensor mapping subentry flow (direct handler tests)."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.energyid.const import DOMAIN
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor fixture for tryke fixture-injection."""


@test
async def user_step_form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the user step form is shown."""
    parent_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Mock Title",
        data={
            "provisioning_key": "test_key",
            "provisioning_secret": "test_secret",
            "device_id": "test_device",
            "device_name": "Test Device",
        },
        entry_id="parent_entry_id",
    )
    parent_entry.add_to_hass(hass)

    result = await hass.config_entries.subentries.async_init(
        (parent_entry.entry_id, "sensor_mapping"),
        context={"source": "user"},
    )
    expect(result["type"]).to_equal("form")
    expect(result["step_id"]).to_equal("user")
    expect("ha_entity_id" in result["data_schema"].schema).to_be(True)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def successful_creation() -> None:
    """Stub for test_successful_creation."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def entity_already_mapped() -> None:
    """Stub for test_entity_already_mapped."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def entity_not_found() -> None:
    """Stub for test_entity_not_found."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def no_entity_selected() -> None:
    """Stub for test_no_entity_selected."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def entity_disappears_after_validation() -> None:
    """Stub for test_entity_disappears_after_validation."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def no_suitable_entities() -> None:
    """Stub for test_no_suitable_entities."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def get_suggested_entities_no_suitable_entities() -> None:
    """Stub for test_get_suggested_entities_no_suitable_entities."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def energyid_sensor_mapping_flow_handler_repr() -> None:
    """Stub for test_energyid_sensor_mapping_flow_handler_repr."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def duplicate_entity_key() -> None:
    """Stub for test_duplicate_entity_key."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def validate_mapping_input_none_entity() -> None:
    """Stub for test_validate_mapping_input_none_entity."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def validate_mapping_input_empty_string() -> None:
    """Stub for test_validate_mapping_input_empty_string."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def validate_mapping_input_already_mapped() -> None:
    """Stub for test_validate_mapping_input_already_mapped."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def get_suggested_entities_with_state_class() -> None:
    """Stub for test_get_suggested_entities_with_state_class."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def get_suggested_entities_with_device_class() -> None:
    """Stub for test_get_suggested_entities_with_device_class."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def subentry_entity_not_found_after_validation() -> None:
    """Stub for test_subentry_entity_not_found_after_validation."""

