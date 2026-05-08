"""Tryke skip stub for test_select.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the hdfury.select module imports cleanly."""
    from homeassistant.components.hdfury import select  # noqa: PLC0415
    expect(select).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def select_entities() -> None:
    """Stub for test_select_entities."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def select_operation_mode() -> None:
    """Stub for test_select_operation_mode."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def select_tx_ports() -> None:
    """Stub for test_select_tx_ports."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def select_operation_mode_error() -> None:
    """Stub for test_select_operation_mode_error."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def select_ports_missing_state() -> None:
    """Stub for test_select_ports_missing_state."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def select_entities_unavailable_on_error() -> None:
    """Stub for test_select_entities_unavailable_on_error."""

