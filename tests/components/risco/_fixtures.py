"""Tryke fixtures for Risco integration tests."""

from __future__ import annotations

from typing import Any

from tryke import Depends, fixture

from homeassistant.components.risco.const import DOMAIN, TYPE_LOCAL
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PIN,
    CONF_PORT,
    CONF_TYPE,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture

TEST_CLOUD_CONFIG = {
    CONF_USERNAME: "test-username",
    CONF_PASSWORD: "test-password",
    CONF_PIN: "1234",
}
TEST_LOCAL_CONFIG = {
    CONF_TYPE: TYPE_LOCAL,
    CONF_HOST: "test-host",
    CONF_PORT: 5004,
    CONF_PIN: "1234",
}


@fixture
def options() -> dict[str, Any]:
    """Fixture for default (empty) options."""
    return {}


@fixture
def cloud_config_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    opts: dict[str, Any] = Depends(options),
) -> MockConfigEntry:
    """Fixture for a cloud config entry."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=TEST_CLOUD_CONFIG,
        options=opts,
        unique_id=TEST_CLOUD_CONFIG[CONF_USERNAME],
    )
    config_entry.add_to_hass(hass)
    return config_entry
