"""The tests for the SamsungTV remote platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def setup() -> None:
    """Stub for test_setup (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def unique_id() -> None:
    """Stub for test_unique_id (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def main_services() -> None:
    """Stub for test_main_services (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def send_command_service() -> None:
    """Stub for test_send_command_service (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def turn_on_wol() -> None:
    """Stub for test_turn_on_wol (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def turn_on_without_turnon() -> None:
    """Stub for test_turn_on_without_turnon (port deferred)."""
