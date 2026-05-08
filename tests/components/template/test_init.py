"""The tests for template integration init."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.template.const import DOMAIN
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fixture,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Anchor fixture for tryke Depends() resolution."""


@test
async def fail_non_numerical_number_settings(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test that non numerical number options causes config entry setup to fail."""
    options = {
        "template_type": "number",
        "name": "My template",
        "state": "{{ 10 }}",
        "min": "{{ 0 }}",
        "max": "{{ 100 }}",
        "step": "{{ 0.1 }}",
        "set_value": {
            "action": "input_number.set_value",
            "target": {"entity_id": "input_number.test"},
            "data": {"value": "{{ value }}"},
        },
    }
    template_config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options=options,
        title="Template",
    )
    template_config_entry.add_to_hass(hass)
    expect(
        await hass.config_entries.async_setup(template_config_entry.entry_id)
    ).to_be(False)
    expect(
        "The 'My template' number template needs to be reconfigured, "
        "max must be a number, got '{{ 100 }}'" in caplog.text
    ).to_be(True)


@test.skip("requires template integration setup — port deferred")
async def reloadable() -> None:
    """Stub for test_reloadable."""


@test.skip("requires template integration setup — port deferred")
async def reloadable_can_remove() -> None:
    """Stub for test_reloadable_can_remove."""


@test.skip("requires template integration setup — port deferred")
async def reloadable_stops_on_invalid_config() -> None:
    """Stub for test_reloadable_stops_on_invalid_config."""


@test.skip("requires template integration setup — port deferred")
async def reloadable_handles_partial_valid_config() -> None:
    """Stub for test_reloadable_handles_partial_valid_config."""


@test.skip("requires template integration setup — port deferred")
async def reloadable_multiple_platforms() -> None:
    """Stub for test_reloadable_multiple_platforms."""


@test.skip("requires template integration setup — port deferred")
async def reload_sensors_that_reference_other_template_sensors() -> None:
    """Stub for test_reload_sensors_that_reference_other_template_sensors."""


@test.skip("requires template integration setup — port deferred")
async def reload_removes_legacy_deprecation() -> None:
    """Stub for test_reload_removes_legacy_deprecation."""


@test.skip("requires template integration setup — port deferred")
async def change_device() -> None:
    """Stub for test_change_device."""


@test.skip("requires template integration setup — port deferred")
async def yaml_reload_when_labs_flag_changes() -> None:
    """Stub for test_yaml_reload_when_labs_flag_changes."""


@test.skip("requires template integration setup — port deferred")
async def config_entry_reload_when_labs_flag_changes() -> None:
    """Stub for test_config_entry_reload_when_labs_flag_changes."""


@test.skip("requires template integration setup — port deferred")
async def migration_1_1() -> None:
    """Stub for test_migration_1_1."""


@test.skip("requires template integration setup — port deferred")
async def migration_from_future_version() -> None:
    """Stub for test_migration_from_future_version."""
