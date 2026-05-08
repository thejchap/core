"""Test the Splunk integration init. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def setup_entry_success() -> None:
    """Stub for test_setup_entry_success (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def setup_entry_error() -> None:
    """Stub for test_setup_entry_error (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def unload_entry() -> None:
    """Stub for test_unload_entry (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def yaml_import_without_filter() -> None:
    """Stub for test_yaml_import_without_filter (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def yaml_with_filter() -> None:
    """Stub for test_yaml_with_filter (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def setup_without_yaml() -> None:
    """Stub for test_setup_without_yaml (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def event_listener_with_filter() -> None:
    """Stub for test_event_listener_with_filter (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def event_listener_unauthorized() -> None:
    """Stub for test_event_listener_unauthorized (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def event_listener_error_handling() -> None:
    """Stub for test_event_listener_error_handling (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def yaml_filter_only_no_deprecation_issue() -> None:
    """Stub for test_yaml_filter_only_no_deprecation_issue (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def yaml_with_connection_creates_deprecation_issue() -> None:
    """Stub for test_yaml_with_connection_creates_deprecation_issue (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def yaml_import_error_creates_specific_issue() -> None:
    """Stub for test_yaml_import_error_creates_specific_issue (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def yaml_import_already_configured_creates_deprecation_issue() -> None:
    """Stub for test_yaml_import_already_configured_creates_deprecation_issue (port deferred)."""
