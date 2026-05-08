"""Tryke skip-stubs for onvif diagnostics tests.

Original tests use ONVIF camera mocks + zeroconf discovery; full port deferred.
"""

from tryke import test

@test.skip("ONVIF camera mocks + zeroconf discovery")
async def diagnostics() -> None:
    """Test generating diagnostics for a config entry."""
