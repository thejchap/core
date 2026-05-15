"""Test script init."""

from unittest.mock import patch

from tryke import expect, test

from homeassistant import scripts


@test
def config_per_platform() -> None:
    """Test config per platform method."""
    with patch(
        "homeassistant.scripts.get_default_config_dir", return_value="/default"
    ):
        expect(scripts.get_default_config_dir()).to_equal("/default")
        expect(scripts.extract_config_dir()).to_equal("/default")
        expect(scripts.extract_config_dir([""])).to_equal("/default")
        expect(scripts.extract_config_dir(["-c", "/arg"])).to_equal("/arg")
        expect(scripts.extract_config_dir(["--config", "/a"])).to_equal("/a")
