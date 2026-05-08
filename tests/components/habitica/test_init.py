"""Tryke skip stub for test_init.py with one passing smoke test."""

from tryke import expect, test


@test
def domain_const_importable() -> None:
    """Smoke test: the habitica integration's DOMAIN constant imports cleanly."""
    from homeassistant.components.habitica.const import DOMAIN  # noqa: PLC0415
    expect(DOMAIN).to_equal("habitica")


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def entry_setup_unload() -> None:
    """Stub for test_entry_setup_unload."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def config_entry_not_ready() -> None:
    """Stub for test_config_entry_not_ready."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def config_entry_auth_failed() -> None:
    """Stub for test_config_entry_auth_failed."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def coordinator_update_failed() -> None:
    """Stub for test_coordinator_update_failed."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def coordinator_rate_limited() -> None:
    """Stub for test_coordinator_rate_limited."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def remove_party_and_reload() -> None:
    """Stub for test_remove_party_and_reload."""

