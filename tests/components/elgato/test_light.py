"""Tryke skip stub for test_light.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def light_state_temperature() -> None:
    """Stub for test_light_state_temperature."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def light_change_state_temperature() -> None:
    """Stub for test_light_change_state_temperature."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def light_unavailable() -> None:
    """Stub for test_light_unavailable."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def light_identify() -> None:
    """Stub for test_light_identify."""

