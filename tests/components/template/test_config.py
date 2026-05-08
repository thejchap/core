"""Tryke skip-stubs for template/test_config.py."""

from tryke import test


@test.skip("requires template integration setup — port deferred")
async def invalid_schema() -> None:
    """Stub for test_invalid_schema."""

@test.skip("requires template integration setup — port deferred")
async def valid_default_entity_id() -> None:
    """Stub for test_valid_default_entity_id."""

@test.skip("requires template integration setup — port deferred")
async def invalid_default_entity_id() -> None:
    """Stub for test_invalid_default_entity_id."""

@test.skip("requires template integration setup — port deferred")
async def invalid_binary_sensor_schema_with_auto_off() -> None:
    """Stub for test_invalid_binary_sensor_schema_with_auto_off."""

@test.skip("requires template integration setup — port deferred")
async def combined_state_variables() -> None:
    """Stub for test_combined_state_variables."""

@test.skip("requires template integration setup — port deferred")
async def combined_trigger_variables() -> None:
    """Stub for test_combined_trigger_variables."""

@test.skip("requires template integration setup — port deferred")
async def state_init_attribute_variables() -> None:
    """Stub for test_state_init_attribute_variables."""

@test.skip("requires template integration setup — port deferred")
async def invalid_schema_raises_issue() -> None:
    """Stub for test_invalid_schema_raises_issue."""

@test.skip("requires template integration setup — port deferred")
async def multiple_configuration_keys() -> None:
    """Stub for test_multiple_configuration_keys."""

