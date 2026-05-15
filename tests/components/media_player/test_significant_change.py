"""Test the Media Player significant change platform."""

from typing import Any

from tryke import expect, test

from homeassistant.components.media_player import (
    ATTR_APP_ID,
    ATTR_APP_NAME,
    ATTR_ENTITY_PICTURE_LOCAL,
    ATTR_GROUP_MEMBERS,
    ATTR_INPUT_SOURCE,
    ATTR_MEDIA_ALBUM_ARTIST,
    ATTR_MEDIA_ALBUM_NAME,
    ATTR_MEDIA_ARTIST,
    ATTR_MEDIA_CHANNEL,
    ATTR_MEDIA_CONTENT_ID,
    ATTR_MEDIA_CONTENT_TYPE,
    ATTR_MEDIA_DURATION,
    ATTR_MEDIA_EPISODE,
    ATTR_MEDIA_PLAYLIST,
    ATTR_MEDIA_POSITION,
    ATTR_MEDIA_POSITION_UPDATED_AT,
    ATTR_MEDIA_REPEAT,
    ATTR_MEDIA_SEASON,
    ATTR_MEDIA_SERIES_TITLE,
    ATTR_MEDIA_SHUFFLE,
    ATTR_MEDIA_TITLE,
    ATTR_MEDIA_TRACK,
    ATTR_MEDIA_VOLUME_LEVEL,
    ATTR_MEDIA_VOLUME_MUTED,
    ATTR_SOUND_MODE,
)
from homeassistant.components.media_player.significant_change import (
    async_check_significant_change,
)


@test
async def significant_state_change() -> None:
    """Detect Media Player significant state changes."""
    attrs: dict[str, Any] = {}
    expect(async_check_significant_change(None, "on", attrs, "on", attrs)).to_be(False)
    expect(async_check_significant_change(None, "on", attrs, "off", attrs)).to_be(True)


@test.cases(
    test.case("app_id_same", old_attrs={ATTR_APP_ID: "old_value"}, new_attrs={ATTR_APP_ID: "old_value"}, expected_result=False),
    test.case("app_id_change", old_attrs={ATTR_APP_ID: "old_value"}, new_attrs={ATTR_APP_ID: "new_value"}, expected_result=True),
    test.case("app_name_change", old_attrs={ATTR_APP_NAME: "old_value"}, new_attrs={ATTR_APP_NAME: "new_value"}, expected_result=True),
    test.case("picture_local_change", old_attrs={ATTR_ENTITY_PICTURE_LOCAL: "old_value"}, new_attrs={ATTR_ENTITY_PICTURE_LOCAL: "new_value"}, expected_result=True),
    test.case("group_members_change", old_attrs={ATTR_GROUP_MEMBERS: ["old1", "old2"]}, new_attrs={ATTR_GROUP_MEMBERS: ["old1", "new"]}, expected_result=False),
    test.case("input_source_change", old_attrs={ATTR_INPUT_SOURCE: "old_value"}, new_attrs={ATTR_INPUT_SOURCE: "new_value"}, expected_result=True),
    test.case("album_artist_change", old_attrs={ATTR_MEDIA_ALBUM_ARTIST: "old_value"}, new_attrs={ATTR_MEDIA_ALBUM_ARTIST: "new_value"}, expected_result=True),
    test.case("album_name_change", old_attrs={ATTR_MEDIA_ALBUM_NAME: "old_value"}, new_attrs={ATTR_MEDIA_ALBUM_NAME: "new_value"}, expected_result=True),
    test.case("artist_change", old_attrs={ATTR_MEDIA_ARTIST: "old_value"}, new_attrs={ATTR_MEDIA_ARTIST: "new_value"}, expected_result=True),
    test.case("channel_change", old_attrs={ATTR_MEDIA_CHANNEL: "old_value"}, new_attrs={ATTR_MEDIA_CHANNEL: "new_value"}, expected_result=True),
    test.case("content_id_change", old_attrs={ATTR_MEDIA_CONTENT_ID: "old_value"}, new_attrs={ATTR_MEDIA_CONTENT_ID: "new_value"}, expected_result=True),
    test.case("content_type_change", old_attrs={ATTR_MEDIA_CONTENT_TYPE: "old_value"}, new_attrs={ATTR_MEDIA_CONTENT_TYPE: "new_value"}, expected_result=True),
    test.case("duration_change", old_attrs={ATTR_MEDIA_DURATION: "old_value"}, new_attrs={ATTR_MEDIA_DURATION: "new_value"}, expected_result=True),
    test.case("episode_change", old_attrs={ATTR_MEDIA_EPISODE: "old_value"}, new_attrs={ATTR_MEDIA_EPISODE: "new_value"}, expected_result=True),
    test.case("playlist_change", old_attrs={ATTR_MEDIA_PLAYLIST: "old_value"}, new_attrs={ATTR_MEDIA_PLAYLIST: "new_value"}, expected_result=True),
    test.case("repeat_change", old_attrs={ATTR_MEDIA_REPEAT: "old_value"}, new_attrs={ATTR_MEDIA_REPEAT: "new_value"}, expected_result=True),
    test.case("season_change", old_attrs={ATTR_MEDIA_SEASON: "old_value"}, new_attrs={ATTR_MEDIA_SEASON: "new_value"}, expected_result=True),
    test.case("series_title_change", old_attrs={ATTR_MEDIA_SERIES_TITLE: "old_value"}, new_attrs={ATTR_MEDIA_SERIES_TITLE: "new_value"}, expected_result=True),
    test.case("shuffle_change", old_attrs={ATTR_MEDIA_SHUFFLE: "old_value"}, new_attrs={ATTR_MEDIA_SHUFFLE: "new_value"}, expected_result=True),
    test.case("title_change", old_attrs={ATTR_MEDIA_TITLE: "old_value"}, new_attrs={ATTR_MEDIA_TITLE: "new_value"}, expected_result=True),
    test.case("track_change", old_attrs={ATTR_MEDIA_TRACK: "old_value"}, new_attrs={ATTR_MEDIA_TRACK: "new_value"}, expected_result=True),
    test.case("volume_muted_change", old_attrs={ATTR_MEDIA_VOLUME_MUTED: "old_value"}, new_attrs={ATTR_MEDIA_VOLUME_MUTED: "new_value"}, expected_result=True),
    test.case("sound_mode_change", old_attrs={ATTR_SOUND_MODE: "old_value"}, new_attrs={ATTR_SOUND_MODE: "new_value"}, expected_result=True),
    test.case("multi_attr_change", old_attrs={ATTR_SOUND_MODE: "old_value", ATTR_MEDIA_VOLUME_MUTED: "old_value"}, new_attrs={ATTR_SOUND_MODE: "new_value", ATTR_MEDIA_VOLUME_MUTED: "old_value"}, expected_result=True),
    test.case("volume_0.1_to_0.2", old_attrs={ATTR_MEDIA_VOLUME_LEVEL: 0.1}, new_attrs={ATTR_MEDIA_VOLUME_LEVEL: 0.2}, expected_result=True),
    test.case("volume_0.1_to_0.19", old_attrs={ATTR_MEDIA_VOLUME_LEVEL: 0.1}, new_attrs={ATTR_MEDIA_VOLUME_LEVEL: 0.19}, expected_result=False),
    test.case("volume_invalid_to_1", old_attrs={ATTR_MEDIA_VOLUME_LEVEL: "invalid"}, new_attrs={ATTR_MEDIA_VOLUME_LEVEL: 1}, expected_result=True),
    test.case("volume_1_to_invalid", old_attrs={ATTR_MEDIA_VOLUME_LEVEL: 1}, new_attrs={ATTR_MEDIA_VOLUME_LEVEL: "invalid"}, expected_result=False),
    test.case("position_change_insignificant", old_attrs={ATTR_MEDIA_POSITION: "old_value"}, new_attrs={ATTR_MEDIA_POSITION: "new_value"}, expected_result=False),
    test.case("position_updated_at_insignificant", old_attrs={ATTR_MEDIA_POSITION_UPDATED_AT: "old_value"}, new_attrs={ATTR_MEDIA_POSITION_UPDATED_AT: "new_value"}, expected_result=False),
    test.case("unknown_attr_same", old_attrs={"unknown_attr": "old_value"}, new_attrs={"unknown_attr": "old_value"}, expected_result=False),
    test.case("unknown_attr_change", old_attrs={"unknown_attr": "old_value"}, new_attrs={"unknown_attr": "new_value"}, expected_result=False),
)
async def significant_atributes_change(
    old_attrs: dict[str, Any],
    new_attrs: dict[str, Any],
    expected_result: bool,
) -> None:
    """Detect Media Player significant attribute changes."""
    expect(
        async_check_significant_change(None, "state", old_attrs, "state", new_attrs)
    ).to_equal(expected_result)
