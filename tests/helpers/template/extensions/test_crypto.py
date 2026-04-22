"""Test cryptographic hash functions for Home Assistant templates."""

from __future__ import annotations

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant

from tests.hass_fixtures import hass
from tests.helpers.template.helpers import render


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@test
async def md5(hass: HomeAssistant = Depends(hass)) -> None:
    """Test the md5 function and filter."""
    ha_md5 = "3d15e5c102c3413d0337393c3287e006"
    expect(render(hass, "{{ md5('Home Assistant') }}")).to_equal(ha_md5)
    expect(render(hass, "{{ 'Home Assistant' | md5 }}")).to_equal(ha_md5)


@test
async def sha1(hass: HomeAssistant = Depends(hass)) -> None:
    """Test the sha1 function and filter."""
    ha_sha1 = "c8fd3bb19b94312664faa619af7729bdbf6e9f8a"
    expect(render(hass, "{{ sha1('Home Assistant') }}")).to_equal(ha_sha1)
    expect(render(hass, "{{ 'Home Assistant' | sha1 }}")).to_equal(ha_sha1)


@test
async def sha256(hass: HomeAssistant = Depends(hass)) -> None:
    """Test the sha256 function and filter."""
    ha_sha256 = "2a366abb0cd47f51f3725bf0fb7ebcb4fefa6e20f4971e25fe2bb8da8145ce2b"
    expect(render(hass, "{{ sha256('Home Assistant') }}")).to_equal(ha_sha256)
    expect(render(hass, "{{ 'Home Assistant' | sha256 }}")).to_equal(ha_sha256)


@test
async def sha512(hass: HomeAssistant = Depends(hass)) -> None:
    """Test the sha512 function and filter."""
    ha_sha512 = "9e3c2cdd1fbab0037378d37e1baf8a3a4bf92c54b56ad1d459deee30ccbb2acbebd7a3614552ea08992ad27dedeb7b4c5473525ba90cb73dbe8b9ec5f69295bb"
    expect(render(hass, "{{ sha512('Home Assistant') }}")).to_equal(ha_sha512)
    expect(render(hass, "{{ 'Home Assistant' | sha512 }}")).to_equal(ha_sha512)
