"""Tryke skip-stubs for otbr websocket_api tests.

Original tests use OTBR REST API + supervisor_client mocks; full port deferred.
"""

from tryke import test

@test.skip("OTBR REST API + supervisor_client mocks")
async def get_info() -> None:
    """Test async_get_info."""

@test.skip("OTBR REST API + supervisor_client mocks")
async def get_info_no_entry() -> None:
    """Test async_get_info."""

@test.skip("OTBR REST API + supervisor_client mocks")
async def get_info_fetch_fails() -> None:
    """Test async_get_info."""

@test.skip("OTBR REST API + supervisor_client mocks")
async def create_network() -> None:
    """Test create network."""

@test.skip("OTBR REST API + supervisor_client mocks")
async def create_network_no_entry() -> None:
    """Test create network."""

@test.skip("OTBR REST API + supervisor_client mocks")
async def create_network_fails_1() -> None:
    """Test create network."""

@test.skip("OTBR REST API + supervisor_client mocks")
async def create_network_fails_2() -> None:
    """Test create network."""

@test.skip("OTBR REST API + supervisor_client mocks")
async def create_network_fails_3() -> None:
    """Test create network."""

@test.skip("OTBR REST API + supervisor_client mocks")
async def create_network_fails_4() -> None:
    """Test create network."""

@test.skip("OTBR REST API + supervisor_client mocks")
async def create_network_fails_5() -> None:
    """Test create network."""

@test.skip("OTBR REST API + supervisor_client mocks")
async def create_network_fails_6() -> None:
    """Test create network."""

@test.skip("OTBR REST API + supervisor_client mocks")
async def create_network_fails_7() -> None:
    """Test create network."""

@test.skip("OTBR REST API + supervisor_client mocks")
async def create_network_fails_8() -> None:
    """Test create network."""

@test.skip("OTBR REST API + supervisor_client mocks")
async def set_network() -> None:
    """Test set network."""

@test.skip("OTBR REST API + supervisor_client mocks")
async def set_network_no_entry() -> None:
    """Test set network."""

@test.skip("OTBR REST API + supervisor_client mocks")
async def set_network_channel_conflict() -> None:
    """Test set network."""

@test.skip("OTBR REST API + supervisor_client mocks")
async def set_network_unknown_dataset() -> None:
    """Test set network."""

@test.skip("OTBR REST API + supervisor_client mocks")
async def set_network_fails_1() -> None:
    """Test set network."""

@test.skip("OTBR REST API + supervisor_client mocks")
async def set_network_fails_2() -> None:
    """Test set network."""

@test.skip("OTBR REST API + supervisor_client mocks")
async def set_network_fails_3() -> None:
    """Test set network."""

@test.skip("OTBR REST API + supervisor_client mocks")
async def set_network_fails_4() -> None:
    """Test set network."""

@test.skip("OTBR REST API + supervisor_client mocks")
async def set_network_fails_5() -> None:
    """Test set network."""

@test.skip("OTBR REST API + supervisor_client mocks")
async def set_channel() -> None:
    """Test set channel."""

@test.skip("OTBR REST API + supervisor_client mocks")
async def set_channel_multiprotocol() -> None:
    """Test set channel."""

@test.skip("OTBR REST API + supervisor_client mocks")
async def set_channel_no_entry() -> None:
    """Test set channel."""

@test.skip("OTBR REST API + supervisor_client mocks")
async def set_channel_fails_1() -> None:
    """Test set channel."""

@test.skip("OTBR REST API + supervisor_client mocks")
async def set_channel_fails_2() -> None:
    """Test set channel."""

@test.skip("OTBR REST API + supervisor_client mocks")
async def set_channel_fails_3() -> None:
    """Test set channel."""
