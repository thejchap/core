"""Test WebDAV component setup."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("webdav: caplog text matching diverges between pytest/tryke runtime")
async def error_during_setup() -> None:
    """Stub for test_error_during_setup (port deferred)."""
