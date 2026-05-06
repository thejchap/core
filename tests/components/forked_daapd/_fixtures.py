"""Tryke fixtures for forked_daapd."""

from __future__ import annotations

from tryke import fixture

from homeassistant.components.forked_daapd.const import CONF_TTS_PAUSE_TIME, DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT

from tests.common import MockConfigEntry


@fixture
def config_entry() -> MockConfigEntry:
    """Create hass config_entry fixture."""
    data = {
        CONF_HOST: "192.168.1.1",
        CONF_PORT: "2345",
        CONF_PASSWORD: "",
    }
    return MockConfigEntry(
        version=1,
        domain=DOMAIN,
        title="",
        data=data,
        options={CONF_TTS_PAUSE_TIME: 0},
        source=SOURCE_USER,
        entry_id=1,
    )
