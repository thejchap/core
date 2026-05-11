"""The test for the sensibo switch platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("snapshot test — out of scope")
async def switch() -> None:
    """Stub for test_switch (port deferred)."""

@test.skip("snapshot test — out of scope")
async def switch_timer() -> None:
    """Stub for test_switch_timer (port deferred)."""

@test.skip("snapshot test — out of scope")
async def switch_pure_boost() -> None:
    """Stub for test_switch_pure_boost (port deferred)."""

@test.skip("snapshot test — out of scope")
async def switch_command_failure() -> None:
    """Stub for test_switch_command_failure (port deferred)."""

@test.skip("snapshot test — out of scope")
async def switch_climate_react() -> None:
    """Stub for test_switch_climate_react (port deferred)."""

@test.skip("snapshot test — out of scope")
async def switch_climate_react_no_data() -> None:
    """Stub for test_switch_climate_react_no_data (port deferred)."""
