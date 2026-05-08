"""Tryke skip-stubs for otbr homeassistant_hardware tests.

Original tests use OTBR REST API + supervisor_client mocks; full port deferred.
"""

from tryke import test

@test.skip("OTBR REST API + supervisor_client mocks")
async def get_firmware_info() -> None:
    """Test `async_get_firmware_info`."""

@test.skip("OTBR REST API + supervisor_client mocks")
async def get_firmware_info_ignored() -> None:
    """Test `async_get_firmware_info` with ignored entry."""

@test.skip("OTBR REST API + supervisor_client mocks")
async def get_firmware_info_no_coprocessor_version() -> None:
    """Test `async_get_firmware_info` with no coprocessor version support."""

@test.skip("OTBR REST API + supervisor_client mocks")
async def hardware_firmware_info_provider_notification() -> None:
    """Test that the OTBR provides hardware and firmware information."""

@test.skip("OTBR REST API + supervisor_client mocks")
async def get_firmware_info_remote_otbr() -> None:
    """Test `async_get_firmware_info` with no coprocessor version support."""
