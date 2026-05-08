"""Test Notion diagnostics."""

from tryke import test


@test.skip("requires setup_config_entry conftest fixture and ANY/diagnostics path; defer port")
async def entry_diagnostics() -> None:
    """Stub for test_entry_diagnostics (port deferred)."""
