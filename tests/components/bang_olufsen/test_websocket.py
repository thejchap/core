"""Tryke skip stub for test_websocket.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("snapshot test — out of scope")
async def connection() -> None:
    """Stub for test_connection."""


@test.skip("snapshot test — out of scope")
async def connection_lost() -> None:
    """Stub for test_connection_lost."""


@test.skip("snapshot test — out of scope")
async def on_software_update_state() -> None:
    """Stub for test_on_software_update_state."""


@test.skip("snapshot test — out of scope")
async def on_remote_control_already_added() -> None:
    """Stub for test_on_remote_control_already_added."""


@test.skip("snapshot test — out of scope")
async def on_remote_control_paired() -> None:
    """Stub for test_on_remote_control_paired."""


@test.skip("snapshot test — out of scope")
async def on_remote_control_unpaired() -> None:
    """Stub for test_on_remote_control_unpaired."""


@test.skip("snapshot test — out of scope")
async def on_all_notifications_raw() -> None:
    """Stub for test_on_all_notifications_raw."""


