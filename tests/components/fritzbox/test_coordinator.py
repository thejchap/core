"""Tryke skip stub for test_coordinator.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the fritzbox.coordinator module imports cleanly."""
    from homeassistant.components.fritzbox import coordinator  # noqa: PLC0415
    expect(coordinator).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def coordinator_update_after_reboot() -> None:
    """Stub for test_coordinator_update_after_reboot."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def coordinator_update_after_password_change() -> None:
    """Stub for test_coordinator_update_after_password_change."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def coordinator_update_when_unreachable() -> None:
    """Stub for test_coordinator_update_when_unreachable."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def coordinator_automatic_registry_cleanup() -> None:
    """Stub for test_coordinator_automatic_registry_cleanup."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def coordinator_workaround_sub_units_without_main_device() -> None:
    """Stub for test_coordinator_workaround_sub_units_without_main_device."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def coordinator_has_triggers() -> None:
    """Stub for test_coordinator_has_triggers."""

