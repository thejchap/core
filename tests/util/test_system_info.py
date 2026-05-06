"""Tests for the system info helper."""

from unittest.mock import patch

from tryke import expect, test

from homeassistant.util.system_info import is_official_image as _is_official_image


@test
async def is_official_image() -> None:
    """Test is_official_image."""
    _is_official_image.cache_clear()
    with patch("homeassistant.util.system_info.os.path.isfile", return_value=True):
        expect(_is_official_image()).to_be(True)
    _is_official_image.cache_clear()
    with patch("homeassistant.util.system_info.os.path.isfile", return_value=False):
        expect(_is_official_image()).to_be(False)
