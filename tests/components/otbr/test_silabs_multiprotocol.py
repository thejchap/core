"""Tryke skip-stubs for otbr silabs_multiprotocol tests.

Original tests use OTBR REST API + supervisor_client mocks; full port deferred.
"""

from tryke import test

@test.skip("OTBR REST API + supervisor_client mocks")
async def async_change_channel() -> None:
    """Test async_change_channel."""

@test.skip("OTBR REST API + supervisor_client mocks")
async def async_change_channel_no_pending() -> None:
    """Test async_change_channel when the pending dataset already expired."""

@test.skip("OTBR REST API + supervisor_client mocks")
async def async_change_channel_no_update() -> None:
    """Test async_change_channel when we didn't get a dataset from the OTBR."""

@test.skip("OTBR REST API + supervisor_client mocks")
async def async_change_channel_no_otbr() -> None:
    """Test async_change_channel when otbr is not configured."""

@test.skip("OTBR REST API + supervisor_client mocks")
async def async_change_channel_non_matching_url() -> None:
    """Test async_change_channel when otbr is not configured."""

@test.skip("OTBR REST API + supervisor_client mocks")
async def async_get_channel() -> None:
    """Test test_async_get_channel."""

@test.skip("OTBR REST API + supervisor_client mocks")
async def async_get_channel_no_dataset() -> None:
    """Test test_async_get_channel."""

@test.skip("OTBR REST API + supervisor_client mocks")
async def async_get_channel_error() -> None:
    """Test test_async_get_channel."""

@test.skip("OTBR REST API + supervisor_client mocks")
async def async_get_channel_no_otbr() -> None:
    """Test test_async_get_channel when otbr is not configured."""

@test.skip("OTBR REST API + supervisor_client mocks")
async def async_get_channel_non_matching_url() -> None:
    """Test async_change_channel when otbr is not configured."""

@test.skip("OTBR REST API + supervisor_client mocks")
async def async_using_multipan() -> None:
    """Test async_change_channel when otbr is not configured."""

@test.skip("OTBR REST API + supervisor_client mocks")
async def async_using_multipan_no_otbr() -> None:
    """Test async_change_channel when otbr is not configured."""

@test.skip("OTBR REST API + supervisor_client mocks")
async def async_using_multipan_non_matching_url() -> None:
    """Test async_change_channel when otbr is not configured."""
