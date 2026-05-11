"""Tryke skip stub for test_init.py."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the homeassistant.components.devolo_home_control module imports cleanly."""
    from homeassistant.components import devolo_home_control  # noqa: PLC0415
    expect(devolo_home_control).not_.to_be(None)


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def setup_entry() -> None:
    """Stub for test_setup_entry."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def setup_entry_credentials_invalid() -> None:
    """Stub for test_setup_entry_credentials_invalid."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def setup_entry_maintenance() -> None:
    """Stub for test_setup_entry_maintenance."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def setup_gateway_offline() -> None:
    """Stub for test_setup_gateway_offline."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def setup_all_gateways_offline() -> None:
    """Stub for test_setup_all_gateways_offline."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def unload_entry() -> None:
    """Stub for test_unload_entry."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def home_assistant_stop() -> None:
    """Stub for test_home_assistant_stop."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def remove_device() -> None:
    """Stub for test_remove_device."""

