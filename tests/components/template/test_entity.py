"""Tryke skip-stubs for template/test_entity.py."""

from tryke import test


@test.skip("requires template integration setup — port deferred")
async def template_entity_not_implemented() -> None:
    """Stub for test_template_entity_not_implemented."""

@test.skip("requires template integration setup — port deferred")
async def reload_stops_entity_action_scripts() -> None:
    """Stub for test_reload_stops_entity_action_scripts."""

