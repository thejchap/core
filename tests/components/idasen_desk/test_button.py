"""Tryke skip-stubs for test_button.py - sibling port deferred (34 LOC, 0 parametrize)."""

from tryke import test


@test.skip("requires bluetooth/idasen-desk integration setup beyond shim slice")
async def connect_button() -> None:
    """Stub for test_connect_button."""


@test.skip("requires bluetooth/idasen-desk integration setup beyond shim slice")
async def disconnect_button() -> None:
    """Stub for test_disconnect_button."""
