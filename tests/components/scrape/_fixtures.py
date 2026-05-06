"""Tryke fixtures for Scrape tests."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, patch

from tryke import Depends, fixture

from homeassistant.components.rest.data import (  # pylint: disable=hass-component-root-import
    DEFAULT_TIMEOUT,
)
from homeassistant.components.rest.schema import (  # pylint: disable=hass-component-root-import
    DEFAULT_METHOD,
    DEFAULT_VERIFY_SSL,
)
from homeassistant.components.scrape.const import (
    CONF_ENCODING,
    CONF_INDEX,
    CONF_SELECT,
    DEFAULT_ENCODING,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import (
    CONF_METHOD,
    CONF_RESOURCE,
    CONF_TIMEOUT,
    CONF_VERIFY_SSL,
)
from homeassistant.core import HomeAssistant

from . import MockRestData

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Patch async_setup_entry."""
    with patch(
        "homeassistant.components.scrape.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
async def get_resource_config() -> dict[str, Any]:
    """Return default minimal configuration for resource."""
    return {
        CONF_RESOURCE: "https://www.home-assistant.io",
        CONF_METHOD: DEFAULT_METHOD,
        "auth": {},
        "advanced": {
            CONF_VERIFY_SSL: DEFAULT_VERIFY_SSL,
            CONF_TIMEOUT: DEFAULT_TIMEOUT,
            CONF_ENCODING: DEFAULT_ENCODING,
        },
    }


@fixture
async def get_sensor_config() -> tuple[dict[str, Any], ...]:
    """Return default minimal configuration for sensor."""
    return (
        {
            "data": {"advanced": {}, CONF_INDEX: 0, CONF_SELECT: ".current-version h1"},
            "subentry_id": "01JZN07D8D23994A49YKS649S7",
            "subentry_type": "entity",
            "title": "Current version",
            "unique_id": None,
        },
    )


@fixture
async def get_data() -> MockRestData:
    """Return RestData mock."""
    return MockRestData("test_scrape_sensor")


@fixture
async def loaded_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    resource_config: dict[str, Any] = Depends(get_resource_config),
    sensor_config: tuple[dict[str, Any], ...] = Depends(get_sensor_config),
    data: MockRestData = Depends(get_data),
) -> MockConfigEntry:
    """Set up the Scrape integration in Home Assistant."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        source=SOURCE_USER,
        options=resource_config,
        entry_id="01JZN04ZJ9BQXXGXDS05WS7D6P",
        subentries_data=sensor_config,
        version=2,
    )

    config_entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.rest.RestData",
        return_value=data,
    ):
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    return config_entry
