"""Testing the Prowl initialisation. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def load_reload_unload_config_entry() -> None:
    """Stub for test_load_reload_unload_config_entry (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def config_entry_failures() -> None:
    """Stub for test_config_entry_failures (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def both_yaml_and_config_entry() -> None:
    """Stub for test_both_yaml_and_config_entry (port deferred)."""
