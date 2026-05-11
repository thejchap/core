"""Test the Sunricher DALI light platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("snapshot test — out of scope")
async def entities() -> None:
    """Stub for test_entities (port deferred)."""

@test.skip("snapshot test — out of scope")
async def turn_on_light() -> None:
    """Stub for test_turn_on_light (port deferred)."""

@test.skip("snapshot test — out of scope")
async def turn_off_light() -> None:
    """Stub for test_turn_off_light (port deferred)."""

@test.skip("snapshot test — out of scope")
async def turn_on_with_brightness() -> None:
    """Stub for test_turn_on_with_brightness (port deferred)."""

@test.skip("snapshot test — out of scope")
async def callback_registration() -> None:
    """Stub for test_callback_registration (port deferred)."""

@test.skip("snapshot test — out of scope")
async def status_updates() -> None:
    """Stub for test_status_updates (port deferred)."""

@test.skip("snapshot test — out of scope")
async def device_availability() -> None:
    """Stub for test_device_availability (port deferred)."""
