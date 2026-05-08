"""Test schlage lock. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def lock_attributes() -> None:
    """Stub for test_lock_attributes (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def lock_services() -> None:
    """Stub for test_lock_services (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def changed_by() -> None:
    """Stub for test_changed_by (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def add_code_service() -> None:
    """Stub for test_add_code_service (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def add_code_service_integer_code() -> None:
    """Stub for test_add_code_service_integer_code (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def add_code_service_default_notify_on_use_value() -> None:
    """Stub for test_add_code_service_default_notify_on_use_value (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def add_code_service_invalid_code() -> None:
    """Stub for test_add_code_service_invalid_code (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def add_code_service_duplicate_name() -> None:
    """Stub for test_add_code_service_duplicate_name (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def add_code_service_duplicate_code() -> None:
    """Stub for test_add_code_service_duplicate_code (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def delete_code_service() -> None:
    """Stub for test_delete_code_service (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def delete_code_service_case_insensitive() -> None:
    """Stub for test_delete_code_service_case_insensitive (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def delete_code_service_nonexistent_code() -> None:
    """Stub for test_delete_code_service_nonexistent_code (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def delete_code_service_no_access_codes() -> None:
    """Stub for test_delete_code_service_no_access_codes (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def get_codes_service() -> None:
    """Stub for test_get_codes_service (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def get_codes_service_no_codes() -> None:
    """Stub for test_get_codes_service_no_codes (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def get_codes_service_empty_codes() -> None:
    """Stub for test_get_codes_service_empty_codes (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def delete_code_service_nonexistent_code_with_existing_codes() -> None:
    """Stub for test_delete_code_service_nonexistent_code_with_existing_codes (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def add_code_service_refresh_error() -> None:
    """Stub for test_add_code_service_refresh_error (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def add_code_service_api_error() -> None:
    """Stub for test_add_code_service_api_error (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def delete_code_service_api_error() -> None:
    """Stub for test_delete_code_service_api_error (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def get_codes_service_refresh_error() -> None:
    """Stub for test_get_codes_service_refresh_error (port deferred)."""
