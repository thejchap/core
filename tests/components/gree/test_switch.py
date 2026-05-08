"""Tryke skip stub for test_switch.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the gree.switch module imports cleanly."""
    from homeassistant.components.gree import switch  # noqa: PLC0415
    expect(switch).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def registry_settings() -> None:
    """Stub for test_registry_settings."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def send_switch_on() -> None:
    """Stub for test_send_switch_on."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def send_switch_on_device_timeout() -> None:
    """Stub for test_send_switch_on_device_timeout."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def send_switch_off() -> None:
    """Stub for test_send_switch_off."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def send_switch_toggle() -> None:
    """Stub for test_send_switch_toggle."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def entity_state() -> None:
    """Stub for test_entity_state."""

