"""Tryke skip stub for test_event.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the gentex_homelink.event module imports cleanly."""
    from homeassistant.components.gentex_homelink import event  # noqa: PLC0415
    expect(event).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def entities() -> None:
    """Stub for test_entities."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def entities_update() -> None:
    """Stub for test_entities_update."""

