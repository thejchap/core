"""Tryke skip stub for test_lock.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def default_state() -> None:
    """Stub for test_default_state."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def state_reporting() -> None:
    """Stub for test_state_reporting."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def service_calls_openable() -> None:
    """Stub for test_service_calls_openable."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def service_calls_basic() -> None:
    """Stub for test_service_calls_basic."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def reload() -> None:
    """Stub for test_reload."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def reload_with_platform_not_setup() -> None:
    """Stub for test_reload_with_platform_not_setup."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def reload_with_base_integration_platform_not_setup() -> None:
    """Stub for test_reload_with_base_integration_platform_not_setup."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def nested_group() -> None:
    """Stub for test_nested_group."""

