"""Tryke skip-stubs for SolarEdge sensor tests."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the homeassistant.components.solaredge.sensor module imports cleanly."""
    from homeassistant.components.solaredge import sensor  # noqa: PLC0415
    expect(sensor).not_.to_be(None)


@test.skip("requires entity_registry_enabled_by_default + freezer — port deferred")
async def storage_data_service() -> None:
    """Stub for test_storage_data_service."""


@test.skip("requires entity_registry_enabled_by_default + freezer — port deferred")
async def storage_data_service_multi_battery() -> None:
    """Stub for test_storage_data_service_multi_battery."""


@test.skip("requires entity_registry_enabled_by_default + freezer — port deferred")
async def storage_data_service_no_batteries() -> None:
    """Stub for test_storage_data_service_no_batteries."""


@test.skip("requires entity_registry_enabled_by_default + freezer — port deferred")
async def storage_data_service_api_error() -> None:
    """Stub for test_storage_data_service_api_error."""


@test.skip("requires entity_registry_enabled_by_default + freezer — port deferred")
async def storage_data_missing_keys_in_response() -> None:
    """Stub for test_storage_data_missing_keys_in_response."""


@test.skip("requires entity_registry_enabled_by_default + freezer — port deferred")
async def storage_data_missing_batteries_key() -> None:
    """Stub for test_storage_data_missing_batteries_key."""


@test.skip("requires entity_registry_enabled_by_default + freezer — port deferred")
async def storage_service_deferred_after_inventory_failure() -> None:
    """Stub for test_storage_service_deferred_after_inventory_failure."""


@test.skip("requires entity_registry_enabled_by_default + freezer — port deferred")
async def storage_service_not_created_when_inventory_has_no_batteries() -> None:
    """Stub for test_storage_service_not_created_when_inventory_has_no_batteries."""
