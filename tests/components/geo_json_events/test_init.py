"""Tryke skip stub for test_init.py with one passing smoke test."""

from tryke import expect, test


@test
def domain_const_importable() -> None:
    """Smoke test: the geo_json_events integration's DOMAIN constant imports cleanly."""
    from homeassistant.components.geo_json_events.const import DOMAIN  # noqa: PLC0415
    expect(DOMAIN).to_equal("geo_json_events")


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def component_unload_config_entry() -> None:
    """Stub for test_component_unload_config_entry."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def remove_orphaned_entities() -> None:
    """Stub for test_remove_orphaned_entities."""

