"""Tryke skip-stubs for test_init.py - addon manager fixtures not in shim."""

from tryke import test

@test.skip("addon manager fixtures not in shim")
async def setup_entry() -> None:
    """Stub for test_setup_entry."""

@test.skip("addon manager fixtures not in shim")
async def setup_zha() -> None:
    """Stub for test_setup_zha."""

@test.skip("addon manager fixtures not in shim")
async def contributes_radio_serial_port() -> None:
    """Stub for test_contributes_radio_serial_port."""

@test.skip("addon manager fixtures not in shim")
async def setup_entry_no_hassio() -> None:
    """Stub for test_setup_entry_no_hassio."""

@test.skip("addon manager fixtures not in shim")
async def setup_entry_wrong_board() -> None:
    """Stub for test_setup_entry_wrong_board."""

@test.skip("addon manager fixtures not in shim")
async def setup_entry_wait_hassio() -> None:
    """Stub for test_setup_entry_wait_hassio."""

@test.skip("addon manager fixtures not in shim")
async def setup_entry_addon_info_fails() -> None:
    """Stub for test_setup_entry_addon_info_fails."""

@test.skip("addon manager fixtures not in shim")
async def migrate_entry() -> None:
    """Stub for test_migrate_entry."""
