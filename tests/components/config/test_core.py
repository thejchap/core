"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def validate_config_ok() -> None:
    """Stub for test_validate_config_ok (port deferred)."""

@test.skip("pending tryke port")
async def validate_config_requires_admin() -> None:
    """Stub for test_validate_config_requires_admin (port deferred)."""

@test.skip("pending tryke port")
async def websocket_core_update() -> None:
    """Stub for test_websocket_core_update (port deferred)."""

@test.skip("pending tryke port")
async def websocket_core_update_not_admin() -> None:
    """Stub for test_websocket_core_update_not_admin (port deferred)."""

@test.skip("pending tryke port")
async def websocket_bad_core_update() -> None:
    """Stub for test_websocket_bad_core_update (port deferred)."""

@test.skip("pending tryke port")
async def detect_config() -> None:
    """Stub for test_detect_config (port deferred)."""

@test.skip("pending tryke port")
async def detect_config_fail() -> None:
    """Stub for test_detect_config_fail (port deferred)."""
