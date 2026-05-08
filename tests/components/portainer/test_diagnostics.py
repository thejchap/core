"""Test the Portainer component diagnostics. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def get_config_entry_diagnostics() -> None:
    """Stub for test_get_config_entry_diagnostics (port deferred)."""
