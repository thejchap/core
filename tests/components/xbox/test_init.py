"""Tryke skip-stubs for test_init.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("xbox: sibling test pending tryke port")
async def entry_setup_unload() -> None:
    """Stub for test_entry_setup_unload."""


@test.skip("xbox: sibling test pending tryke port")
async def config_entry_not_ready() -> None:
    """Stub for test_config_entry_not_ready."""


@test.skip("xbox: sibling test pending tryke port")
async def config_implementation_not_available() -> None:
    """Stub for test_config_implementation_not_available."""


@test.skip("xbox: sibling test pending tryke port")
async def oauth_session_refresh_failure_exceptions() -> None:
    """Stub for test_oauth_session_refresh_failure_exceptions."""


@test.skip("xbox: sibling test pending tryke port")
async def oauth_session_refresh_user_and_xsts_token_exceptions() -> None:
    """Stub for test_oauth_session_refresh_user_and_xsts_token_exceptions."""


@test.skip("xbox: sibling test pending tryke port")
async def coordinator_update_failed() -> None:
    """Stub for test_coordinator_update_failed."""


@test.skip("xbox: sibling test pending tryke port")
async def dynamic_devices() -> None:
    """Stub for test_dynamic_devices."""
