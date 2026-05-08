"""Tryke skip-stubs for otbr init tests.

Original tests use OTBR REST API + supervisor_client mocks; full port deferred.
"""

from tryke import test

@test.skip("OTBR REST API + supervisor_client mocks")
async def import_dataset() -> None:
    """Test the active dataset is imported at setup."""

@test.skip("OTBR REST API + supervisor_client mocks")
async def import_share_radio_channel_collision() -> None:
    """Test the active dataset is imported at setup."""

@test.skip("OTBR REST API + supervisor_client mocks")
async def import_share_radio_no_channel_collision() -> None:
    """Test the active dataset is imported at setup."""

@test.skip("OTBR REST API + supervisor_client mocks")
async def import_insecure_dataset() -> None:
    """Test the active dataset is imported at setup."""

@test.skip("OTBR REST API + supervisor_client mocks")
async def config_entry_not_ready() -> None:
    """Test raising ConfigEntryNotReady ."""

@test.skip("OTBR REST API + supervisor_client mocks")
async def border_agent_id_not_supported() -> None:
    """Test border router does not support border agent ID."""

@test.skip("OTBR REST API + supervisor_client mocks")
async def config_entry_update() -> None:
    """Test update config entry settings."""

@test.skip("OTBR REST API + supervisor_client mocks")
async def remove_entry() -> None:
    """Test async_get_active_dataset_tlvs after removing the config entry."""

@test.skip("OTBR REST API + supervisor_client mocks")
async def update_unique_id() -> None:
    """Test we update the unique id if extended address has changed."""
