"""Tryke skip-stubs for otbr util tests.

Original tests use OTBR REST API + supervisor_client mocks; full port deferred.
"""

from tryke import test

@test.skip("OTBR REST API + supervisor_client mocks")
async def get_allowed_channel() -> None:
    """Test get_allowed_channel."""

@test.skip("OTBR REST API + supervisor_client mocks")
async def factory_reset() -> None:
    """Test factory_reset."""

@test.skip("OTBR REST API + supervisor_client mocks")
async def factory_reset_not_supported() -> None:
    """Test factory_reset."""

@test.skip("OTBR REST API + supervisor_client mocks")
async def factory_reset_error_1() -> None:
    """Test factory_reset."""

@test.skip("OTBR REST API + supervisor_client mocks")
async def factory_reset_error_2() -> None:
    """Test factory_reset."""
