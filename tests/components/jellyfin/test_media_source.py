"""Tryke skip-stubs for test_media_source.py - snapshot fixture coupling - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot test — out of scope")
async def resolve() -> None:
    """Stub for test_resolve."""

@test.skip("snapshot test — out of scope")
async def audio_codec_resolve() -> None:
    """Stub for test_audio_codec_resolve."""

@test.skip("snapshot test — out of scope")
async def root() -> None:
    """Stub for test_root."""

@test.skip("snapshot test — out of scope")
async def tv_library() -> None:
    """Stub for test_tv_library."""

@test.skip("snapshot test — out of scope")
async def movie_library() -> None:
    """Stub for test_movie_library."""

@test.skip("snapshot test — out of scope")
async def music_library() -> None:
    """Stub for test_music_library."""

@test.skip("snapshot test — out of scope")
async def browse_unsupported() -> None:
    """Stub for test_browse_unsupported."""
