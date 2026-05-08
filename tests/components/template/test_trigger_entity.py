"""Tryke skip-stubs for template/test_trigger_entity.py."""

from tryke import test


@test.skip("requires template integration setup — port deferred")
async def reference_blueprints_is_none() -> None:
    """Stub for test_reference_blueprints_is_none."""

@test.skip("requires template integration setup — port deferred")
async def template_state() -> None:
    """Stub for test_template_state."""

@test.skip("requires template integration setup — port deferred")
async def bad_template_state() -> None:
    """Stub for test_bad_template_state."""

@test.skip("requires template integration setup — port deferred")
async def template_state_syntax_error() -> None:
    """Stub for test_template_state_syntax_error."""

@test.skip("requires template integration setup — port deferred")
async def script_variables_from_coordinator() -> None:
    """Stub for test_script_variables_from_coordinator."""

@test.skip("requires template integration setup — port deferred")
async def default_entity_id() -> None:
    """Stub for test_default_entity_id."""

@test.skip("requires template integration setup — port deferred")
async def bad_default_entity_id() -> None:
    """Stub for test_bad_default_entity_id."""

@test.skip("requires template integration setup — port deferred")
async def multiple_template_validators() -> None:
    """Stub for test_multiple_template_validators."""

@test.skip("requires template integration setup — port deferred")
async def coordinator_shutdown_unloads_script_and_condition() -> None:
    """Stub for test_coordinator_shutdown_unloads_script_and_condition."""

@test.skip("requires template integration setup — port deferred")
async def shutdown_stops_script_and_keeps_triggers_subscribed() -> None:
    """Stub for test_shutdown_stops_script_and_keeps_triggers_subscribed."""

@test.skip("requires template integration setup — port deferred")
async def reload_stops_script_and_unsubscribes_triggers() -> None:
    """Stub for test_reload_stops_script_and_unsubscribes_triggers."""

