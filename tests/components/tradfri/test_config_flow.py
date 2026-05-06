"""Test the Tradfri config flow."""

from tryke import test


@test.skip("pytradfri[async] not installed (requires autoconf-built dtlssocket)")
async def already_paired() -> None:
    """Test Gateway already paired."""


@test.skip("pytradfri[async] not installed (requires autoconf-built dtlssocket)")
async def user_connection_successful() -> None:
    """Test a successful connection."""


@test.skip("pytradfri[async] not installed (requires autoconf-built dtlssocket)")
async def user_connection_timeout() -> None:
    """Test a connection timeout."""


@test.skip("pytradfri[async] not installed (requires autoconf-built dtlssocket)")
async def user_connection_bad_key() -> None:
    """Test a connection with bad key."""


@test.skip("pytradfri[async] not installed (requires autoconf-built dtlssocket)")
async def discovery_connection() -> None:
    """Test a connection via discovery."""


@test.skip("pytradfri[async] not installed (requires autoconf-built dtlssocket)")
async def discovery_duplicate_aborted() -> None:
    """Test duplicate discovery aborts."""


@test.skip("pytradfri[async] not installed (requires autoconf-built dtlssocket)")
async def duplicate_discovery() -> None:
    """Test duplicate in-progress discovery is ignored."""


@test.skip("pytradfri[async] not installed (requires autoconf-built dtlssocket)")
async def discovery_updates_unique_id() -> None:
    """Test duplicate discovery host updates unique_id."""
