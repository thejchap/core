"""Tryke skip-stubs for mysensors config flow tests.

Original tests use complex fixture chain not yet ported to tryke shim; full port deferred.
"""

from tryke import test

@test.skip("requires mysensors gateway socket+serial fixtures (not in tryke shim)")
async def config_mqtt() -> None:
    """Stub for test_config_mqtt (port deferred)."""

@test.skip("requires mysensors gateway socket+serial fixtures (not in tryke shim)")
async def missing_mqtt() -> None:
    """Stub for test_missing_mqtt (port deferred)."""

@test.skip("requires mysensors gateway socket+serial fixtures (not in tryke shim)")
async def config_serial() -> None:
    """Stub for test_config_serial (port deferred)."""

@test.skip("requires mysensors gateway socket+serial fixtures (not in tryke shim)")
async def config_tcp() -> None:
    """Stub for test_config_tcp (port deferred)."""

@test.skip("requires mysensors gateway socket+serial fixtures (not in tryke shim)")
async def fail_to_connect() -> None:
    """Stub for test_fail_to_connect (port deferred)."""

@test.skip("requires mysensors gateway socket+serial fixtures (not in tryke shim)")
async def config_invalid() -> None:
    """Stub for test_config_invalid (port deferred)."""

@test.skip("requires mysensors gateway socket+serial fixtures (not in tryke shim)")
async def duplicate() -> None:
    """Stub for test_duplicate (port deferred)."""
