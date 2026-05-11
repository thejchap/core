"""Tests for SMLIGHT SLZB-06 button entities. (tryke skip stub)."""

from tryke import expect, fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test
def module_importable() -> None:
    """Smoke test: the homeassistant.components.smlight.button module imports cleanly."""
    from homeassistant.components.smlight import button  # noqa: PLC0415
    expect(button).not_.to_be(None)


@test.skip("conftest fixtures need migration to _fixtures.py")
async def buttons() -> None:
    """Stub for test_buttons (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def disabled_by_default_buttons() -> None:
    """Stub for test_disabled_by_default_buttons (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def zigbee2_router_button() -> None:
    """Stub for test_zigbee2_router_button (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def remove_router_reconnect() -> None:
    """Stub for test_remove_router_reconnect (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def multi_radio_buttons_u_device() -> None:
    """Stub for test_multi_radio_buttons_u_device (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def multi_radio_press_calls_idx() -> None:
    """Stub for test_multi_radio_press_calls_idx (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def multi_radio_buttons_shared_non_u_device() -> None:
    """Stub for test_multi_radio_buttons_shared_non_u_device (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def router_button_with_3_radios() -> None:
    """Stub for test_router_button_with_3_radios (port deferred)."""
