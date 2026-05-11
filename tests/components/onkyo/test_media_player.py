"""Tryke skip-stubs for onkyo media_player tests.

Original tests use aioonkyo discovery autouse + receiver mocks; full port deferred.
"""

from tryke import expect, test

@test
def module_importable() -> None:
    """Smoke test: the homeassistant.components.onkyo.media_player module imports cleanly."""
    from homeassistant.components.onkyo import media_player  # noqa: PLC0415
    expect(media_player).not_.to_be(None)


@test.skip("aioonkyo discovery autouse + receiver mocks")
async def entities() -> None:
    """Test entities."""

@test.skip("aioonkyo discovery autouse + receiver mocks")
async def availability() -> None:
    """Test entity availability on disconnect and reconnect."""

@test.skip("aioonkyo discovery autouse + receiver mocks")
async def actions() -> None:
    """Test actions."""

@test.skip("aioonkyo discovery autouse + receiver mocks")
async def select_source() -> None:
    """Test select source."""

@test.skip("aioonkyo discovery autouse + receiver mocks")
async def select_sound_mode() -> None:
    """Test select sound mode."""

@test.skip("aioonkyo discovery autouse + receiver mocks")
async def play_media() -> None:
    """Test play media (radio preset)."""

@test.skip("aioonkyo discovery autouse + receiver mocks")
async def select_hdmi_output() -> None:
    """Test select hdmi output."""

@test.skip("aioonkyo discovery autouse + receiver mocks")
async def query_state_task() -> None:
    """Test query state task."""

@test.skip("aioonkyo discovery autouse + receiver mocks")
async def query_av_info_task() -> None:
    """Test query AV info task."""
