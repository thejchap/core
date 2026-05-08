"""Tryke skip stub for test_coordinator.py."""

from tryke import test


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

