"""Tryke skip stub for test_system_health.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the gios.system_health module imports cleanly."""
    from homeassistant.components.gios import system_health  # noqa: PLC0415
    expect(system_health).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def gios_system_health() -> None:
    """Stub for test_gios_system_health."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def gios_system_health_fail() -> None:
    """Stub for test_gios_system_health_fail."""

