"""Tryke skip-stubs for opower diagnostics tests.

Original tests use opower API mocks + recorder + statistics; full port deferred.
"""

from tryke import test

@test.skip("opower API mocks + recorder + statistics")
async def diagnostics() -> None:
    """Test diagnostics."""
