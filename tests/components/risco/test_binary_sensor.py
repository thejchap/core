"""Tests for the Risco binary sensors. (tryke skip stub)."""

from tryke import expect, fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test
def module_importable() -> None:
    """Smoke test: the homeassistant.components.risco.binary_sensor module imports cleanly."""
    from homeassistant.components.risco import binary_sensor  # noqa: PLC0415
    expect(binary_sensor).not_.to_be(None)


@test.skip("conftest fixtures need migration to _fixtures.py")
async def error_on_login() -> None:
    """Stub for test_error_on_login (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def cloud_setup() -> None:
    """Stub for test_cloud_setup (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def cloud_states() -> None:
    """Stub for test_cloud_states (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def error_on_connect() -> None:
    """Stub for test_error_on_connect (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def local_setup() -> None:
    """Stub for test_local_setup (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def local_states() -> None:
    """Stub for test_local_states (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def alarmed_local_states() -> None:
    """Stub for test_alarmed_local_states (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def armed_local_states() -> None:
    """Stub for test_armed_local_states (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def system_states() -> None:
    """Stub for test_system_states (port deferred)."""
