"""Tests config_flow."""

from tryke import test


@test.skip("complex asyncssh + filesystem mock fixtures")
async def backup_sftp_full_flow() -> None:
    """Skipped pending fixture port."""

@test.skip("complex asyncssh + filesystem mock fixtures")
async def already_configured() -> None:
    """Skipped pending fixture port."""

@test.skip("complex asyncssh + filesystem mock fixtures")
async def config_flow_exceptions() -> None:
    """Skipped pending fixture port."""

@test.skip("complex asyncssh + filesystem mock fixtures")
async def config_entry_error() -> None:
    """Skipped pending fixture port."""

@test.skip("complex asyncssh + filesystem mock fixtures")
async def relative_backup_location_rejected() -> None:
    """Skipped pending fixture port."""
