"""Tryke skip stubs for test_fan - sibling test pending port."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def fan_entity_state() -> None:
    """Stub for test_fan_entity_state (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def fan_set_state() -> None:
    """Stub for test_fan_set_state (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def fan_set_state_error() -> None:
    """Stub for test_fan_set_state_error (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def fan_set_state_rate_limit_logs_warning() -> None:
    """Stub for test_fan_set_state_rate_limit_logs_warning (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def coordinator_update_marks_unavailable() -> None:
    """Stub for test_coordinator_update_marks_unavailable (port deferred)."""


