"""Test squeezebox initialization. (tryke skip stub)."""

from tryke import expect, fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test
def module_importable() -> None:
    """Smoke test: the homeassistant.components.squeezebox module imports cleanly."""
    from homeassistant.components import squeezebox  # noqa: PLC0415
    expect(squeezebox).not_.to_be(None)


@test.skip("syrupy snapshot")
async def init_api_fail() -> None:
    """Stub for test_init_api_fail (port deferred)."""

@test.skip("syrupy snapshot")
async def init_timeout_error() -> None:
    """Stub for test_init_timeout_error (port deferred)."""

@test.skip("syrupy snapshot")
async def init_unauthorized() -> None:
    """Stub for test_init_unauthorized (port deferred)."""

@test.skip("syrupy snapshot")
async def init_missing_uuid() -> None:
    """Stub for test_init_missing_uuid (port deferred)."""

@test.skip("syrupy snapshot")
async def device_registry() -> None:
    """Stub for test_device_registry (port deferred)."""

@test.skip("syrupy snapshot")
async def device_registry_server_merged() -> None:
    """Stub for test_device_registry_server_merged (port deferred)."""

@test.skip("syrupy snapshot")
async def remove_device_blocked() -> None:
    """Stub for test_remove_device_blocked (port deferred)."""

@test.skip("syrupy snapshot")
async def remove_device_allowed_offline_player() -> None:
    """Stub for test_remove_device_allowed_offline_player (port deferred)."""

@test.skip("syrupy snapshot")
async def remove_device_allowed_stale_player() -> None:
    """Stub for test_remove_device_allowed_stale_player (port deferred)."""
