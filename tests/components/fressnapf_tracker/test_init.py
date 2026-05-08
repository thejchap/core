"""Tryke skip stub for test_init.py with one passing smoke test."""

from tryke import expect, test


@test
def domain_const_importable() -> None:
    """Smoke test: the fressnapf_tracker integration's DOMAIN constant imports cleanly."""
    from homeassistant.components.fressnapf_tracker.const import DOMAIN  # noqa: PLC0415
    expect(DOMAIN).to_equal("fressnapf_tracker")


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup_entry() -> None:
    """Stub for test_setup_entry."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def unload_entry() -> None:
    """Stub for test_unload_entry."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup_entry_tracker_is_valid_api_error() -> None:
    """Stub for test_setup_entry_tracker_is_valid_api_error."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def state_entity_device_snapshots() -> None:
    """Stub for test_state_entity_device_snapshots."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def invalid_tracker() -> None:
    """Stub for test_invalid_tracker."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def invalid_tracker_already_exists() -> None:
    """Stub for test_invalid_tracker_already_exists."""

