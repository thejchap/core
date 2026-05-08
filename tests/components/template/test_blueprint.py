"""Tryke skip-stubs for template/test_blueprint.py."""

from tryke import test


@test.skip("requires template integration setup — port deferred")
async def inverted_binary_sensor() -> None:
    """Stub for test_inverted_binary_sensor."""

@test.skip("requires template integration setup — port deferred")
async def reload_template_when_blueprint_changes() -> None:
    """Stub for test_reload_template_when_blueprint_changes."""

@test.skip("requires template integration setup — port deferred")
async def init_attribute_variables_from_blueprint() -> None:
    """Stub for test_init_attribute_variables_from_blueprint."""

@test.skip("requires template integration setup — port deferred")
async def trigger_event_sensor() -> None:
    """Stub for test_trigger_event_sensor."""

@test.skip("requires template integration setup — port deferred")
async def blueprint_template_override() -> None:
    """Stub for test_blueprint_template_override."""

@test.skip("requires template integration setup — port deferred")
async def domain_blueprint() -> None:
    """Stub for test_domain_blueprint."""

@test.skip("requires template integration setup — port deferred")
async def invalid_blueprint() -> None:
    """Stub for test_invalid_blueprint."""

@test.skip("requires template integration setup — port deferred")
async def no_blueprint() -> None:
    """Stub for test_no_blueprint."""

@test.skip("requires template integration setup — port deferred")
async def variables_for_entity() -> None:
    """Stub for test_variables_for_entity."""

