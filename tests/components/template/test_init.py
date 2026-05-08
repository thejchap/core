"""Tryke skip-stubs for template/test_init.py."""

from tryke import test


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
async def fail_non_numerical_number_settings() -> None:
    """Stub for test_fail_non_numerical_number_settings."""

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

