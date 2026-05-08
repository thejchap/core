"""The camera tests for the prosegur platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def camera() -> None:
    """Stub for test_camera (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def camera_fail() -> None:
    """Stub for test_camera_fail (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def request_image() -> None:
    """Stub for test_request_image (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def request_image_fail() -> None:
    """Stub for test_request_image_fail (port deferred)."""
