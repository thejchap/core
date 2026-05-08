"""Test the switchbot lights. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def bulb_services() -> None:
    """Stub for test_bulb_services (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def bulb_services_exception() -> None:
    """Stub for test_bulb_services_exception (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def ceiling_light_services() -> None:
    """Stub for test_ceiling_light_services (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def ceiling_light_services_exception() -> None:
    """Stub for test_ceiling_light_services_exception (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def strip_light_services() -> None:
    """Stub for test_strip_light_services (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def strip_light_services_exception() -> None:
    """Stub for test_strip_light_services_exception (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def floor_lamp_services() -> None:
    """Stub for test_floor_lamp_services (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def floor_lamp_services_exception() -> None:
    """Stub for test_floor_lamp_services_exception (port deferred)."""
