"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def good_callback() -> None:
    """Stub for test_good_callback (port deferred)."""

@test.skip("pending tryke port")
async def bad_callback() -> None:
    """Stub for test_bad_callback (port deferred)."""

@test.skip("pending tryke port")
async def good_fixture() -> None:
    """Stub for test_good_fixture (port deferred)."""

@test.skip("pending tryke port")
async def bad_fixture_session_scope() -> None:
    """Stub for test_bad_fixture_session_scope (port deferred)."""

@test.skip("pending tryke port")
async def bad_fixture_package_scope() -> None:
    """Stub for test_bad_fixture_package_scope (port deferred)."""

@test.skip("pending tryke port")
async def bad_fixture_autouse() -> None:
    """Stub for test_bad_fixture_autouse (port deferred)."""
