"""Tryke skip stub for test_diagnostics.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def entry_diagnostics() -> None:
    """Stub for test_entry_diagnostics."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def redact_url() -> None:
    """Stub for test_redact_url."""

