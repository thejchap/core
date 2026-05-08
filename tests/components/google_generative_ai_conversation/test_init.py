"""Tryke skip stub for test_init.py with one passing smoke test."""

from tryke import expect, test


@test
def domain_const_importable() -> None:
    """Smoke test: the google_generative_ai_conversation integration's DOMAIN constant imports cleanly."""
    from homeassistant.components.google_generative_ai_conversation.const import DOMAIN  # noqa: PLC0415
    expect(DOMAIN).to_equal("google_generative_ai_conversation")


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def config_entry_error() -> None:
    """Stub for test_config_entry_error."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def migration_from_v1() -> None:
    """Stub for test_migration_from_v1."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def migration_from_v1_disabled() -> None:
    """Stub for test_migration_from_v1_disabled."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def migration_from_v1_with_multiple_keys() -> None:
    """Stub for test_migration_from_v1_with_multiple_keys."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def migration_from_v1_with_same_keys() -> None:
    """Stub for test_migration_from_v1_with_same_keys."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def migration_from_v2_1() -> None:
    """Stub for test_migration_from_v2_1."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def devices() -> None:
    """Stub for test_devices."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def migrate_entry_from_v2_2() -> None:
    """Stub for test_migrate_entry_from_v2_2."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def migrate_entry_from_v2_3() -> None:
    """Stub for test_migrate_entry_from_v2_3."""

