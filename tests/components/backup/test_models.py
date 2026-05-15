"""Tests for the Backup integration."""

from tryke import expect, test

from homeassistant.components.backup import AgentBackup

from .common import TEST_BACKUP_ABC123


@test
async def agent_backup_serialization() -> None:
    """Test AgentBackup serialization."""

    expect(AgentBackup.from_dict(TEST_BACKUP_ABC123.as_dict())).to_equal(
        TEST_BACKUP_ABC123
    )
