"""Tryke skip stub for test_init.py with one passing smoke test."""

from tryke import expect, test


@test
def domain_const_importable() -> None:
    """Smoke test: the fully_kiosk integration's DOMAIN constant imports cleanly."""
    from homeassistant.components.fully_kiosk.const import DOMAIN  # noqa: PLC0415
    expect(DOMAIN).to_equal("fully_kiosk")


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def load_unload_config_entry() -> None:
    """Stub for test_load_unload_config_entry."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def config_entry_not_ready() -> None:
    """Stub for test_config_entry_not_ready."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def multiple_kiosk_with_empty_mac() -> None:
    """Stub for test_multiple_kiosk_with_empty_mac."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def valid_global_mac_address() -> None:
    """Stub for test_valid_global_mac_address."""

