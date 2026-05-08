"""Tryke skip stub for test_switch.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the fully_kiosk.switch module imports cleanly."""
    from homeassistant.components.fully_kiosk import switch  # noqa: PLC0415
    expect(switch).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def switches() -> None:
    """Stub for test_switches."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def switches_mqtt_update() -> None:
    """Stub for test_switches_mqtt_update."""

