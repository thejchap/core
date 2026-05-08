"""Tryke skip-stubs for teslemetry/test_media_player.py."""

from tryke import test


@test.skip("requires teslemetry API + snapshot — port deferred")
async def media_player() -> None:
    """Stub for test_media_player."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def media_player_alt() -> None:
    """Stub for test_media_player_alt."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def media_player_noscope() -> None:
    """Stub for test_media_player_noscope."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def media_player_services() -> None:
    """Stub for test_media_player_services."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def update_streaming() -> None:
    """Stub for test_update_streaming."""

