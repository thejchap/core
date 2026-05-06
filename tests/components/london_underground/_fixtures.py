"""Tryke fixtures for the london_underground tests."""

from collections.abc import AsyncGenerator
import json
from unittest.mock import AsyncMock, patch

from london_tube_status import parse_api_response
from tryke import Depends, fixture

from homeassistant.components.london_underground.const import CONF_LINE, DOMAIN
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry, async_load_fixture
from tests.hass_fixtures import hass as hass_fixture


@fixture
def mock_setup_entry():
    """Prevent setup of integration during tests."""
    with patch(
        "homeassistant.components.london_underground.async_setup_entry",
        return_value=True,
    ) as mock_setup:
        yield mock_setup


@fixture
async def mock_config_entry(
    hass: HomeAssistant = Depends(hass_fixture),
) -> MockConfigEntry:
    """Mock the config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={},
        options={CONF_LINE: ["Metropolitan"]},
        title="London Underground",
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    return entry


@fixture
async def mock_london_underground_client(
    hass: HomeAssistant = Depends(hass_fixture),
) -> AsyncGenerator[AsyncMock]:
    """Mock a London Underground client."""
    with (
        patch(
            "homeassistant.components.london_underground.TubeData",
            autospec=True,
        ) as mock_client,
        patch(
            "homeassistant.components.london_underground.config_flow.TubeData",
            new=mock_client,
        ),
    ):
        client = mock_client.return_value

        fixture_text = await async_load_fixture(hass, "line_status.json", DOMAIN)
        fixture_data = parse_api_response(json.loads(fixture_text))
        client.data = fixture_data

        yield client
