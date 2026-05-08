"""Tryke skip stub for test_diagnostics.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the github.diagnostics module imports cleanly."""
    from homeassistant.components.github import diagnostics  # noqa: PLC0415
    expect(diagnostics).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def entry_diagnostics() -> None:
    """Stub for test_entry_diagnostics."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def entry_diagnostics_exception() -> None:
    """Stub for test_entry_diagnostics_exception."""

