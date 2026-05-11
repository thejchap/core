"""Tests for Renault sensors. (tryke skip stub)."""

from tryke import expect, fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test
def module_importable() -> None:
    """Smoke test: the homeassistant.components.renault.button module imports cleanly."""
    from homeassistant.components.renault import button  # noqa: PLC0415
    expect(button).not_.to_be(None)


@test.skip("syrupy snapshot; indirect parametrize")
async def buttons() -> None:
    """Stub for test_buttons (port deferred)."""

@test.skip("syrupy snapshot; indirect parametrize")
async def button_empty() -> None:
    """Stub for test_button_empty (port deferred)."""

@test.skip("syrupy snapshot; indirect parametrize")
async def button_errors() -> None:
    """Stub for test_button_errors (port deferred)."""

@test.skip("syrupy snapshot; indirect parametrize")
async def button_access_denied() -> None:
    """Stub for test_button_access_denied (port deferred)."""

@test.skip("syrupy snapshot; indirect parametrize")
async def button_not_supported() -> None:
    """Stub for test_button_not_supported (port deferred)."""

@test.skip("syrupy snapshot; indirect parametrize")
async def button_start_charge() -> None:
    """Stub for test_button_start_charge (port deferred)."""

@test.skip("syrupy snapshot; indirect parametrize")
async def button_stop_charge() -> None:
    """Stub for test_button_stop_charge (port deferred)."""

@test.skip("syrupy snapshot; indirect parametrize")
async def button_start_air_conditioner() -> None:
    """Stub for test_button_start_air_conditioner (port deferred)."""

@test.skip("syrupy snapshot; indirect parametrize")
async def button_sound_horn() -> None:
    """Stub for test_button_sound_horn (port deferred)."""

@test.skip("syrupy snapshot; indirect parametrize")
async def button_flash_lights() -> None:
    """Stub for test_button_flash_lights (port deferred)."""
