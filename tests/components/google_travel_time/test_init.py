"""Tryke skip stub for test_init.py with one passing smoke test."""

from tryke import expect, test


@test
def domain_const_importable() -> None:
    """Smoke test: the google_travel_time integration's DOMAIN constant imports cleanly."""
    from homeassistant.components.google_travel_time.const import DOMAIN  # noqa: PLC0415
    expect(DOMAIN).to_equal("google_travel_time")


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def migrate_entry_v1_v2() -> None:
    """Stub for test_migrate_entry_v1_v2."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def migrate_entry_v1_v2_invalid_time() -> None:
    """Stub for test_migrate_entry_v1_v2_invalid_time."""

