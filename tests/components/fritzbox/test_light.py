"""Tryke skip stub for test_light.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the fritzbox.light module imports cleanly."""
    from homeassistant.components.fritzbox import light  # noqa: PLC0415
    expect(light).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup() -> None:
    """Stub for test_setup."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup_non_color() -> None:
    """Stub for test_setup_non_color."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup_non_color_non_level() -> None:
    """Stub for test_setup_non_color_non_level."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup_color() -> None:
    """Stub for test_setup_color."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def turn_on() -> None:
    """Stub for test_turn_on."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def turn_on_color() -> None:
    """Stub for test_turn_on_color."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def turn_on_color_no_fullcolorsupport() -> None:
    """Stub for test_turn_on_color_no_fullcolorsupport."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def turn_off() -> None:
    """Stub for test_turn_off."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def update() -> None:
    """Stub for test_update."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def update_error() -> None:
    """Stub for test_update_error."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def discover_new_device() -> None:
    """Stub for test_discover_new_device."""

