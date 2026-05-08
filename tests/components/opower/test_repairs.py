"""Tryke skip-stubs for opower repairs tests.

Original tests use opower API mocks + recorder + statistics; full port deferred.
"""

from tryke import test

@test.skip("opower API mocks + recorder + statistics")
async def unsupported_utility_fix_flow() -> None:
    """Test the unsupported utility fix flow."""
