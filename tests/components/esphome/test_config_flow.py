"""Tryke skip-stubs for esphome config flow tests.

The esphome integration depends on assist_pipeline + bluetooth manager
which require system capabilities (NET_ADMIN/NET_RAW) and a fuller
fixture chain than the tryke shim currently provides; defer port.
"""

from tryke import test

@test.skip("requires assist_pipeline + bluetooth manager setup (NET_ADMIN/NET_RAW)")
async def retrieve_encryption_key_from_storage_with_device_mac() -> None:
    """Stub."""

@test.skip("requires assist_pipeline + bluetooth manager setup (NET_ADMIN/NET_RAW)")
async def reauth_fixed_from_from_storage() -> None:
    """Stub."""
