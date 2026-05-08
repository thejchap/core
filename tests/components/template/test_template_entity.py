"""Tryke skip-stubs for template/test_template_entity.py."""

from tryke import test


@test.skip("requires template integration setup — port deferred")
async def template_entity_requires_hass_set() -> None:
    """Stub for test_template_entity_requires_hass_set."""

@test.skip("requires template integration setup — port deferred")
async def default_entity_id() -> None:
    """Stub for test_default_entity_id."""

@test.skip("requires template integration setup — port deferred")
async def bad_default_entity_id() -> None:
    """Stub for test_bad_default_entity_id."""

