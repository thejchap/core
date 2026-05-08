"""Tryke skip stub for test_coordinator.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the fronius.coordinator module imports cleanly."""
    from homeassistant.components.fronius import coordinator  # noqa: PLC0415
    expect(coordinator).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def adaptive_update_interval() -> None:
    """Stub for test_adaptive_update_interval."""

