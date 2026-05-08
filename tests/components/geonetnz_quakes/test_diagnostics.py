"""Tryke skip stub for test_diagnostics.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the geonetnz_quakes.diagnostics module imports cleanly."""
    from homeassistant.components.geonetnz_quakes import diagnostics  # noqa: PLC0415
    expect(diagnostics).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def entry_diagnostics() -> None:
    """Stub for test_entry_diagnostics."""

