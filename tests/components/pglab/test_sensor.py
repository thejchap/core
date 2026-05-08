"""Tryke skip-stubs for pglab sensor tests.

Original tests use MQTT discovery + per-platform device registry; full port deferred.
"""

from tryke import test

@test.skip("MQTT discovery + per-platform device registry")
async def sensors() -> None:
    """Check if sensors are properly created and updated."""
