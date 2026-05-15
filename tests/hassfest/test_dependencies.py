"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def child_import() -> None:
    """Stub for test_child_import (port deferred)."""

@test.skip("pending tryke port")
async def subimport() -> None:
    """Stub for test_subimport (port deferred)."""

@test.skip("pending tryke port")
async def child_import_field() -> None:
    """Stub for test_child_import_field (port deferred)."""

@test.skip("pending tryke port")
async def renamed_absolute() -> None:
    """Stub for test_renamed_absolute (port deferred)."""

@test.skip("pending tryke port")
async def all_imports() -> None:
    """Stub for test_all_imports (port deferred)."""

@test.skip("pending tryke port")
async def dependency_on_core_integration_rejected() -> None:
    """Stub for test_dependency_on_core_integration_rejected (port deferred)."""

@test.skip("pending tryke port")
async def dependency_on_non_core_integration_allowed() -> None:
    """Stub for test_dependency_on_non_core_integration_allowed (port deferred)."""

@test.skip("pending tryke port")
async def core_integrations_in_sync_with_bootstrap() -> None:
    """Stub for test_core_integrations_in_sync_with_bootstrap (port deferred)."""
