"""Tryke skip-stubs for test_diagnostic.py - snapshot fixture coupling - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def diagnostics() -> None:
    """Stub for test_diagnostics."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def diagnostic_config_error() -> None:
    """Stub for test_diagnostic_config_error."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def diagnostic_redact() -> None:
    """Stub for test_diagnostic_redact."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def diagnostics_project() -> None:
    """Stub for test_diagnostics_project."""
