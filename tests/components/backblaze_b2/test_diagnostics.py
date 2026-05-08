"""Tryke skip stub for test_diagnostics.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def diagnostics_basic() -> None:
    """Stub for test_diagnostics_basic."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def diagnostics_error_handling() -> None:
    """Stub for test_diagnostics_error_handling."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def diagnostics_bucket_data_redaction() -> None:
    """Stub for test_diagnostics_bucket_data_redaction."""

