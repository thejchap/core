"""Tryke skip-stubs for tesla_fleet/test_media_player.py."""

from tryke import test


@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def media_player() -> None:
    """Stub for test_media_player."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def media_player_alt() -> None:
    """Stub for test_media_player_alt."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def media_player_offline() -> None:
    """Stub for test_media_player_offline."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def media_player_noscope() -> None:
    """Stub for test_media_player_noscope."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def media_player_services() -> None:
    """Stub for test_media_player_services."""

